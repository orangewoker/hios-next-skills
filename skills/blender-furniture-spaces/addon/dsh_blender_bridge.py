bl_info = {
    'name': 'DSH Local Modeling Bridge',
    'author': 'DSH Furniture Workflow',
    'version': (1, 0, 0),
    'blender': (4, 2, 0),
    'location': 'System (automatic loopback bridge)',
    'description': 'Local main-thread modeling, inspection, checkpoints and renders for DSH',
    'category': 'System',
}

import bpy
import contextlib
import hashlib
import io
import json
import math
import os
from pathlib import Path
import queue
import secrets
import sys
import threading
import time
import traceback
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOME = Path(os.environ.get('DSH_BLENDER_HOME', Path.home() / '.dsh-blender'))
_server = None
_thread = None
_token = None
_jobs = OrderedDict()
_queue = queue.Queue()
_lock = threading.Lock()
_session_path = None
_accepting = False
_MAX_JOBS = 128


def settings():
    file = HOME / 'settings.json'
    if file.exists():
        return json.loads(file.read_text(encoding='utf-8'))
    return {'workspace': str(Path.home() / 'Documents' / 'DSH-Blender')}


def output_path(value, suffix):
    root = Path(settings()['workspace']).expanduser().resolve()
    target = Path(value).expanduser()
    if not target.is_absolute():
        raise ValueError('Output must be an absolute path')
    target = target.resolve()
    if target == root or root not in target.parents:
        raise ValueError('Output must be inside configured workspace')
    if target.suffix.lower() != suffix:
        raise ValueError('Expected ' + suffix + ' output')
    if target.exists():
        raise FileExistsError('Refusing to overwrite: ' + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def current_scene(name=None):
    if name:
        scene = bpy.data.scenes.get(name)
        if scene is None:
            raise ValueError('Scene not found: ' + name)
        return scene
    return bpy.context.window.scene if bpy.context.window else bpy.context.scene


def inspect_scene(scene):
    from mathutils import Vector
    objects = []
    points = []
    model_points = []
    material_names = set()
    for obj in scene.objects:
        bounds = []
        if obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
            bounds = [tuple(obj.matrix_world @ Vector(v)) for v in obj.bound_box]
            if not all(math.isfinite(n) for p in bounds for n in p):
                raise ValueError('Non-finite geometry bounds: ' + obj.name)
            points.extend(bounds)
            if obj.get('dsh_role') != 'stage':
                model_points.extend(bounds)
        mats = [slot.material.name for slot in obj.material_slots if slot.material]
        material_names.update(mats)
        objects.append({
            'name': obj.name, 'type': obj.type,
            'location': [round(v, 6) for v in obj.location],
            'dimensions': [round(v, 6) for v in obj.dimensions],
            'worldDimensions': [round(max(p[i] for p in bounds)-min(p[i] for p in bounds),6)
                                for i in range(3)] if bounds else None,
            'vertices': len(obj.data.vertices) if obj.type == 'MESH' else 0,
            'polygons': len(obj.data.polygons) if obj.type == 'MESH' else 0,
            'modifiers': [{'name': m.name, 'type': m.type} for m in obj.modifiers],
            'materials': mats, 'collections': [c.name for c in obj.users_collection],
            'owned': bool(obj.get('dsh_owned')), 'hiddenRender': obj.hide_render,
        })
    bounds = None
    if points:
        lo = [min(p[i] for p in points) for i in range(3)]
        hi = [max(p[i] for p in points) for i in range(3)]
        bounds = {'min': lo, 'max': hi, 'size': [hi[i] - lo[i] for i in range(3)]}
    model_bounds = None
    if model_points:
        lo = [min(p[i] for p in model_points) for i in range(3)]
        hi = [max(p[i] for p in model_points) for i in range(3)]
        model_bounds = {'min': lo, 'max': hi, 'size': [hi[i]-lo[i] for i in range(3)]}
    return {
        'pid': os.getpid(), 'blender': bpy.app.version_string,
        'filePath': bpy.data.filepath, 'dirty': bpy.data.is_dirty,
        'scene': scene.name, 'scenes': [s.name for s in bpy.data.scenes],
        'units': {'system': scene.unit_settings.system, 'scale': scene.unit_settings.scale_length},
        'objectCount': len(objects), 'objects': objects[:500],
        'truncated': len(objects) > 500, 'bounds': bounds, 'modelBounds': model_bounds,
        'materials': [{'name': n, 'useNodes': bpy.data.materials[n].use_nodes,
                       'surfaceConnected': any(node.type == 'OUTPUT_MATERIAL' and node.inputs['Surface'].is_linked
                                               for node in bpy.data.materials[n].node_tree.nodes)
                       if bpy.data.materials[n].node_tree else False,
                       'nodeTypes': [node.bl_idname for node in bpy.data.materials[n].node_tree.nodes]
                       if bpy.data.materials[n].node_tree else []} for n in sorted(material_names)],
    }


def save_copy(value):
    target = output_path(value, '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(target), copy=True, check_existing=False)
    if not target.is_file() or target.stat().st_size < 100:
        raise RuntimeError('No valid .blend was saved')
    return {'path': str(target), 'bytes': target.stat().st_size, 'activeFilePath': bpy.data.filepath}


def render(args):
    scene = current_scene(args.get('scene'))
    target = output_path(args['output'], '.png')
    camera = scene.objects.get(args['camera']) if args.get('camera') else scene.camera
    if camera is None or camera.type != 'CAMERA':
        raise ValueError('A valid task camera is required; no arbitrary camera will be created')
    r = scene.render
    fields = ('engine', 'filepath', 'resolution_x', 'resolution_y', 'resolution_percentage')
    before = {field: getattr(r, field) for field in fields}
    old_camera, old_format = scene.camera, r.image_settings.file_format
    old_samples = scene.cycles.samples if hasattr(scene, 'cycles') else None
    try:
        engine = args.get('engine', 'keep')
        if engine not in {'keep', 'eevee', 'cycles'}:
            raise ValueError('Unknown render engine')
        if engine != 'keep':
            r.engine = 'CYCLES' if engine == 'cycles' else 'BLENDER_EEVEE'
        scene.camera = camera
        r.resolution_x = max(64, min(4096, int(args.get('width', 1000))))
        r.resolution_y = max(64, min(4096, int(args.get('height', 1000))))
        r.resolution_percentage = 100
        r.image_settings.file_format = 'PNG'
        r.filepath = str(target)
        if old_samples is not None and 'samples' in args:
            scene.cycles.samples = max(1, min(1024, int(args['samples'])))
        bpy.ops.render.render(write_still=True, scene=scene.name)
        if not target.is_file():
            raise RuntimeError('Render did not produce the expected PNG')
        return {'path': str(target), 'bytes': target.stat().st_size, 'scene': scene.name, 'camera': camera.name}
    finally:
        scene.camera = old_camera
        r.image_settings.file_format = old_format
        if old_samples is not None:
            scene.cycles.samples = old_samples
        for field, value in before.items():
            setattr(r, field, value)


def execute(op, args):
    if op == 'inspect':
        scene = current_scene(args.get('scene'))
        scene.view_layers[0].update()
        return inspect_scene(scene)
    if op in {'checkpoint', 'save'}:
        return save_copy(args['output'])
    if op == 'render':
        return render(args)
    if op == 'execute':
        # Arbitrary user-authorized local Python; this is not a sandbox.
        namespace = {'__name__': '__main__', '__file__': args.get('filename', '<dsh>'),
                     'bpy': bpy, '_dsh_result': None,
                     'DSH_WORKSPACE': settings()['workspace']}
        old_path = list(sys.path)
        stdout, stderr = io.StringIO(), io.StringIO()
        try:
            sys.path[:0] = args.get('searchPaths', [])
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                # Keep independent skill copies/updates from accidentally using
                # a module cached from a different skill installation path.
                for directory in args.get('searchPaths', []):
                    library = Path(directory) / 'furniture_kit.py'
                    if library.is_file():
                        import importlib.util
                        spec = importlib.util.spec_from_file_location('furniture_kit', str(library))
                        module = importlib.util.module_from_spec(spec)
                        # The marketplace fingerprints the installed skill tree.
                        # Compile source directly: neither read stale .pyc files
                        # nor write __pycache__ into the installed resources.
                        exec(compile(library.read_bytes(), str(library), 'exec'), module.__dict__)
                        sys.modules['furniture_kit'] = module
                        break
                exec(compile(args['code'], namespace['__file__'], 'exec'), namespace, namespace)
            result = namespace.get('_dsh_result')
            json.dumps(result, allow_nan=False)
            return {'value': result, 'stdout': stdout.getvalue()[-12000:], 'stderr': stderr.getvalue()[-6000:],
                    'scene': current_scene().name}
        finally:
            sys.path[:] = old_path
    raise ValueError('Unsupported operation')


def _process():
    if not _accepting:
        return None
    try:
        job_id = _queue.get_nowait()
    except queue.Empty:
        return 0.08
    with _lock:
        job = _jobs.get(job_id)
        if job is None:
            return 0.08
        job['state'] = 'running'
        job['startedAt'] = time.time()
    try:
        result = execute(job['op'], job['args'])
        with _lock:
            job.update(state='done', result=result)
    except Exception as error:
        with _lock:
            job.update(state='failed', error=str(error), traceback=traceback.format_exc()[-12000:])
    finally:
        with _lock:
            job['finishedAt'] = time.time()
            job.pop('args', None)
    return 0.08


def _public_job(job):
    return {k: v for k, v in job.items() if k not in {'args', 'digest'}}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body):
        data = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def authorized(self):
        value = self.headers.get('Authorization', '')
        return (not self.headers.get('Origin') and _token is not None
                and secrets.compare_digest(value, 'Bearer ' + _token))

    def do_GET(self):
        if not self.authorized():
            self.reply(403, {'error': 'Forbidden'})
            return
        if self.path == '/health':
            # No bpy calls in HTTP threads, even for read-only inspection.
            self.reply(200, {'ok': True, 'pid': os.getpid(), 'protocol': 1})
        elif self.path.startswith('/jobs/'):
            with _lock:
                job = _jobs.get(self.path[len('/jobs/'):])
                value = _public_job(job) if job else None
            self.reply(200 if value else 404, value or {'error': 'Unknown job; do not assume it can be replayed'})
        else:
            self.reply(404, {'error': 'Not found'})

    def do_POST(self):
        if not self.authorized():
            self.reply(403, {'error': 'Forbidden'})
            return
        if self.path != '/jobs' or not _accepting:
            self.reply(404, {'error': 'Not found'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 2 or length > 2 * 1024 * 1024:
                raise ValueError('Invalid request size')
            request = json.loads(self.rfile.read(length))
            op, args, job_id = request['op'], request.get('args', {}), request['id']
            if op not in {'inspect', 'execute', 'checkpoint', 'save', 'render'}:
                raise ValueError('Unknown operation')
            if (not isinstance(job_id, str) or len(job_id) > 100 or not job_id
                    or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in job_id)):
                raise ValueError('Invalid job ID')
            if not isinstance(args, dict):
                raise ValueError('Arguments must be an object')
            digest = hashlib.sha256(json.dumps([op, args], sort_keys=True).encode()).hexdigest()
            with _lock:
                previous = _jobs.get(job_id)
                if previous:
                    if previous['digest'] != digest:
                        self.reply(409, {'error': 'Request ID already used with different content'})
                        return
                    value = _public_job(previous)
                else:
                    while len(_jobs) >= _MAX_JOBS:
                        completed = next((key for key, item in _jobs.items() if item['state'] in {'done', 'failed'}), None)
                        if completed is None:
                            self.reply(429, {'error': 'Job queue full'})
                            return
                        del _jobs[completed]
                    job = {'id': job_id, 'op': op, 'args': args, 'digest': digest,
                           'state': 'queued', 'createdAt': time.time()}
                    _jobs[job_id] = job
                    value = _public_job(job)
                    _queue.put(job_id)
            self.reply(202, value)
        except (ValueError, KeyError, TypeError) as error:
            self.reply(400, {'error': str(error)})


def register():
    global _server, _thread, _token, _session_path, _accepting
    if _server is not None:
        return
    HOME.mkdir(parents=True, exist_ok=True)
    sessions = HOME / 'sessions'
    sessions.mkdir(exist_ok=True)
    _token = secrets.token_hex(32)
    _server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    _server.daemon_threads = True
    _accepting = True
    _thread = threading.Thread(target=_server.serve_forever, daemon=True, name='DSH-Blender-HTTP')
    _thread.start()
    bpy.app.timers.register(_process, first_interval=0.1, persistent=True)
    _session_path = sessions / ('bridge-%d.json' % os.getpid())
    info = {'protocol': 1, 'pid': os.getpid(), 'version': bpy.app.version_string,
            'binary': bpy.app.binary_path, 'url': 'http://127.0.0.1:%d' % _server.server_port,
            'token': _token, 'startedAt': time.time()}
    temp = _session_path.with_suffix('.tmp')
    temp.write_text(json.dumps(info), encoding='utf-8')
    if os.name != 'nt':
        os.chmod(temp, 0o600)
    temp.replace(_session_path)
    print('[DSH Blender] Local bridge ready, PID %d' % os.getpid())


def unregister():
    global _server, _thread, _token, _accepting
    _accepting = False
    if bpy.app.timers.is_registered(_process):
        bpy.app.timers.unregister(_process)
    if _server:
        _server.shutdown()
        _server.server_close()
    _server = _thread = _token = None
    with _lock:
        _jobs.clear()
    while not _queue.empty():
        try:
            _queue.get_nowait()
        except queue.Empty:
            break
    if _session_path:
        _session_path.unlink(missing_ok=True)
