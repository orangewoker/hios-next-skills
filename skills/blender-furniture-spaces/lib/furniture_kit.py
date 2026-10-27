"""Small, editable furniture/space primitives. Executed only inside Blender."""
import bpy
import json
import math
from mathutils import Vector


def _owned(obj, collection, role='geometry', parameters=None):
    obj['dsh_owned'] = True
    obj['dsh_role'] = role
    if parameters is not None:
        obj['dsh_parameters'] = json.dumps(parameters, ensure_ascii=False)
    collection.objects.link(obj)
    return obj


def task_scene(scene_name, collection_name):
    scene = bpy.data.scenes.get(scene_name)
    if scene and not scene.get('dsh_owned'):
        raise ValueError('Scene name belongs to user data: ' + scene_name)
    if scene is None:
        scene = bpy.data.scenes.new(scene_name)
        scene['dsh_owned'] = True
    collection = bpy.data.collections.get(collection_name)
    if collection and not collection.get('dsh_owned'):
        raise ValueError('Collection name belongs to user data: ' + collection_name)
    if collection is None:
        collection = bpy.data.collections.new(collection_name)
        collection['dsh_owned'] = True
    if collection.name not in scene.collection.children:
        scene.collection.children.link(collection)
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    if bpy.context.window:
        bpy.context.window.scene = scene
    return scene, collection


def clear_collection(collection, role=None):
    if not collection.get('dsh_owned'):
        raise ValueError('Refusing to clear a collection not owned by this task')
    for obj in list(collection.objects):
        if obj.get('dsh_owned') and (role is None or obj.get('dsh_role') == role):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
                elif isinstance(data, bpy.types.Camera):
                    bpy.data.cameras.remove(data)
                elif isinstance(data, bpy.types.Light):
                    bpy.data.lights.remove(data)


def mesh_object(name, vertices, faces, collection, material=None, smooth=False):
    if bpy.data.objects.get(name):
        raise ValueError('Object already exists; update explicitly or clear owned task collection: ' + name)
    mesh = bpy.data.meshes.new(name + '-Mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = _owned(bpy.data.objects.new(name, mesh), collection)
    if material:
        mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = smooth
    return obj


def rounded_box(name, size, collection, location=(0, 0, 0), bevel=.008, material=None):
    if min(size) <= 0:
        raise ValueError('Box size must be positive')
    x, y, z = [n / 2 for n in size]
    vertices = [(-x,-y,-z), (x,-y,-z), (x,y,-z), (-x,y,-z),
                (-x,-y,z), (x,-y,z), (x,y,z), (-x,y,z)]
    faces = [(3,2,1,0), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7), (4,5,6,7)]
    obj = mesh_object(name, vertices, faces, collection, material, smooth=bevel > 0)
    obj.location = location
    obj['dsh_parameters'] = json.dumps({'kind': 'hard-part', 'size': size, 'bevel': bevel})
    if bevel > 0:
        mod = obj.modifiers.new('Editable edge radius', 'BEVEL')
        mod.width = min(bevel, min(size) * .45)
        mod.segments = 6
        mod.harden_normals = True
        weighted = obj.modifiers.new('Planar weighted normals', 'WEIGHTED_NORMAL')
        weighted.keep_sharp = True
        weighted.weight = 50
    return obj


def rounded_rectangle(width, depth, radius, segments=9):
    radius = max(.00001, min(radius, min(width, depth) * .49))
    result = []
    corners = [(width/2-radius, depth/2-radius, 0),
               (-width/2+radius, depth/2-radius, 90),
               (-width/2+radius, -depth/2+radius, 180),
               (width/2-radius, -depth/2+radius, 270)]
    for cx, cy, start in corners:
        for i in range(segments + 1):
            angle = math.radians(start + 90*i/segments)
            result.append((cx + radius*math.cos(angle), cy + radius*math.sin(angle)))
    return result


def extruded_outline(name, outline, bottom, top, collection, material=None, bevel=.004):
    """Closed CCW XY profile extrusion, useful for non-rectangular woodwork."""
    if len(outline) < 3 or top <= bottom:
        raise ValueError('Invalid closed extrusion profile')
    area = sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(outline,outline[1:]+outline[:1]))/2
    if area <= 0:
        raise ValueError('Extrusion outline must be counter-clockwise')
    n = len(outline)
    vertices = [(x,y,bottom) for x,y in outline]+[(x,y,top) for x,y in outline]
    faces = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    obj = mesh_object(name,vertices,faces,collection,material,smooth=False)
    if bevel > 0:
        mod=obj.modifiers.new('Profile edge radius','BEVEL')
        mod.width=bevel;mod.segments=4
    obj['dsh_parameters']=json.dumps({'kind':'profile-extrusion','outline':outline,'bottom':bottom,'top':top})
    return obj


def pillow(name, size, collection, location=(0, 0, 0), radius=.06, crown=.025,
           material=None, subdivisions=1, tuck=.0008):
    w, d, h = size
    if min(size) <= 0 or crown < 0 or not 0 <= subdivisions <= 3:
        raise ValueError('Invalid cushion dimensions/crown/subdivision level')
    edge = min(h*.36, .045, min(w,d)*.12)
    rings = []
    # Bottom face grows outwards, then smoothly rolls up the soft edge.
    for scale in (.18, .42, .68, .86):
        rings.append(((w-2*edge)*scale, (d-2*edge)*scale, radius*scale,
                      -h/2 - crown*.22*(1-scale*scale)))
    for i in range(15):
        angle = -math.pi/2 + math.pi*i/14
        inset = edge*(1-math.cos(angle))
        rings.append((w-2*inset, d-2*inset, max(.006, radius-inset*.35), h/2*math.sin(angle)))
    for scale in (.88, .7, .48, .24):
        rings.append(((w-2*edge)*scale, (d-2*edge)*scale, radius*scale,
                      h/2 + crown*(1-scale*scale)**1.35))
    vertices, faces = [], []
    for rw, rd, rr, z in rings:
        for x, y in rounded_rectangle(rw, rd, rr):
            # Small localized edge tucking, not large random rock-like displacement.
            corner = (abs(x)/(w/2))**8 * (abs(y)/(d/2))**6
            wrinkle = tuck * corner * math.sin(35*x + 28*y) * math.exp(-((z-h*.25)/max(.015,h*.3))**2)
            vertices.append((x, y, z-wrinkle))
    n = len(vertices)//len(rings)
    for j in range(len(rings)-1):
        for i in range(n):
            a, b = j*n+i, j*n+(i+1)%n
            faces.append((a,b,b+n,a+n))
    bottom = len(vertices)
    vertices.append((0,0,-h/2-crown*.22))
    top = len(vertices)
    vertices.append((0,0,h/2+crown))
    for i in range(n):
        faces.append((bottom,(i+1)%n,i))
        base = (len(rings)-1)*n
        faces.append((base+i,base+(i+1)%n,top))
    obj = mesh_object(name, vertices, faces, collection, material, smooth=True)
    obj.location = location
    obj['dsh_parameters'] = json.dumps({'kind': 'lofted-upholstery', 'size': size,
                                       'radius': radius, 'crown': crown, 'tuck': tuck})
    if subdivisions:
        mod = obj.modifiers.new('Editable upholstery subdivision', 'SUBSURF')
        mod.levels = subdivisions
        mod.render_levels = max(2, subdivisions)
    return obj


def tube(name, points, collection, radius=.0012, material=None, cyclic=False):
    if len(points) < 2 or radius <= 0:
        raise ValueError('Tube requires at least two points and a positive radius')
    curve = bpy.data.curves.new(name+'-Curve', 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 12
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new('POLY')
    spline.points.add(len(points)-1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1)
    spline.use_cyclic_u = cyclic
    obj = _owned(bpy.data.objects.new(name, curve), collection)
    if material:
        curve.materials.append(material)
    return obj


def _material(name):
    mat = bpy.data.materials.get(name)
    if mat and not mat.get('dsh_owned'):
        raise ValueError('Refusing to replace user material: '+name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat['dsh_owned'] = True
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf.location = (600,0)
    output.location = (900,0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat, nodes, links, bsdf


def plain_material(name, color, roughness=.5, metallic=0):
    mat, nodes, links, bsdf = _material(name)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    mat.diffuse_color = color
    return mat


def _math(nodes, links, operation, first=None, second=None):
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    for i, value in enumerate((first,second)):
        if value is None:
            continue
        if isinstance(value, (int,float)):
            node.inputs[i].default_value = value
        else:
            links.new(value, node.inputs[i])
    return node.outputs[0]


def fabric_material(name, color=(.055,.065,.08,1)):
    mat, nodes, links, bsdf = _material(name)
    mat.diffuse_color = color
    tex = nodes.new('ShaderNodeTexCoord')
    tex.label = 'Local metric coordinates (not object-scaled UV)'
    xyz = nodes.new('ShaderNodeSeparateXYZ')
    links.new(tex.outputs['Object'], xyz.inputs[0])
    # 0.7 and 0.8 mm yarn spacing, with a shallow cross-weave relief.
    x = _math(nodes,links,'MULTIPLY',xyz.outputs['X'],2*math.pi/.0007)
    y = _math(nodes,links,'MULTIPLY',xyz.outputs['Y'],2*math.pi/.0008)
    weave = _math(nodes,links,'MULTIPLY',_math(nodes,links,'SINE',x),_math(nodes,links,'SINE',y))
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 170
    noise.inputs['Detail'].default_value = 3
    links.new(tex.outputs['Object'], noise.inputs['Vector'])
    streak = nodes.new('ShaderNodeVectorMath')
    streak.operation = 'MULTIPLY'
    streak.inputs[1].default_value = (15,110,12)
    links.new(tex.outputs['Object'],streak.inputs[0])
    slub = nodes.new('ShaderNodeTexNoise')
    slub.inputs['Scale'].default_value = 5
    slub.inputs['Detail'].default_value = 2
    links.new(streak.outputs['Vector'],slub.inputs['Vector'])
    combined = _math(nodes,links,'ADD',_math(nodes,links,'MULTIPLY',noise.outputs['Fac'],.35),
                     _math(nodes,links,'MULTIPLY',slub.outputs['Fac'],.65))
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .28
    ramp.color_ramp.elements[0].color = tuple(c*.16 for c in color[:3])+(1,)
    ramp.color_ramp.elements[1].position = .72
    ramp.color_ramp.elements[1].color = tuple(min(c*3.5,1) for c in color[:3])+(1,)
    middle = ramp.color_ramp.elements.new(.52)
    middle.color = tuple(c*.9 for c in color[:3])+(1,)
    links.new(combined,ramp.inputs[0])
    links.new(ramp.outputs['Color'],bsdf.inputs['Base Color'])
    height = _math(nodes,links,'ADD',_math(nodes,links,'MULTIPLY',weave,.22),noise.outputs['Fac'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .38
    bump.inputs['Distance'].default_value = .00075
    links.new(height,bump.inputs['Height'])
    links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = .78
    bsdf.inputs['Specular IOR Level'].default_value = .32
    bsdf.inputs['Sheen Weight'].default_value = .12
    bsdf.inputs['Sheen Tint'].default_value = (.05,.06,.08,1)
    bsdf.inputs['Sheen Roughness'].default_value = .68
    mat['dsh_parameters'] = json.dumps({'kind':'woven-fabric','yarnMeters':[.0007,.0008]})
    return mat


def wood_material(name, color=(.28,.135,.045,1)):
    mat, nodes, links, bsdf = _material(name)
    mat.diffuse_color = color
    tex = nodes.new('ShaderNodeTexCoord')
    stretch = nodes.new('ShaderNodeVectorMath')
    stretch.operation = 'MULTIPLY'
    stretch.inputs[1].default_value = (.9,38,15)
    links.new(tex.outputs['Object'],stretch.inputs[0])
    grain = nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 4
    grain.inputs['Detail'].default_value = 3
    grain.inputs['Roughness'].default_value = .7
    links.new(stretch.outputs['Vector'],grain.inputs['Vector'])
    fine = nodes.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 26
    fine.inputs['Detail'].default_value = 2
    links.new(stretch.outputs['Vector'],fine.inputs['Vector'])
    mix = _math(nodes,links,'ADD',_math(nodes,links,'MULTIPLY',grain.outputs['Fac'],.78),
                _math(nodes,links,'MULTIPLY',fine.outputs['Fac'],.22))
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .13
    ramp.color_ramp.elements[0].color = tuple(v*.48 for v in color[:3])+(1,)
    ramp.color_ramp.elements[1].position = .86
    ramp.color_ramp.elements[1].color = tuple(min(1,v*1.3) for v in color[:3])+(1,)
    links.new(mix,ramp.inputs[0])
    links.new(ramp.outputs['Color'],bsdf.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .17
    bump.inputs['Distance'].default_value = .00022
    links.new(fine.outputs['Fac'],bump.inputs['Height'])
    links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = .35
    bsdf.inputs['Specular IOR Level'].default_value = .32
    bsdf.inputs['Coat Weight'].default_value = .06
    bsdf.inputs['Coat Roughness'].default_value = .42
    mat['dsh_parameters'] = json.dumps({'kind':'long-grain-wood','grainAxis':'local-X'})
    return mat


def wall_with_openings(name, length, height, thickness, collection, openings=(),
                       location=(0,0,0), material=None):
    if min(length,height,thickness) <= 0:
        raise ValueError('Wall dimensions must be positive')
    rects = []
    for opening in openings:
        x, w, z, h = [opening[k] for k in ('x','width','bottom','height')]
        if w <= 0 or h <= 0 or x-w/2 < -length/2 or x+w/2 > length/2 or z < 0 or z+h > height:
            raise ValueError('Opening outside wall or invalid size')
        rects.append((x-w/2,x+w/2,z,z+h))
    xs = sorted(set([-length/2,length/2]+[v for r in rects for v in r[:2]]))
    zs = sorted(set([0,height]+[v for r in rects for v in r[2:]]))
    created = []
    for i,(x0,x1) in enumerate(zip(xs,xs[1:])):
        for j,(z0,z1) in enumerate(zip(zs,zs[1:])):
            mx,mz = (x0+x1)/2,(z0+z1)/2
            if any(a < mx < b and c < mz < d for a,b,c,d in rects):
                continue
            obj = rounded_box(f'{name}-{i}-{j}', (x1-x0,thickness,z1-z0), collection,
                              (location[0]+mx,location[1],location[2]+mz), bevel=0, material=material)
            obj['dsh_parameters'] = json.dumps({'kind':'wall-cell','openings':list(openings)})
            created.append(obj)
    return created


def aim(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()


def studio(scene, collection, target=(0,0,.45), span=3.0, camera_name='DSH-Camera'):
    if not scene.get('dsh_owned'):
        raise ValueError('Studio may only change a task-owned scene')
    clear_collection(collection, role='stage')
    ground = plain_material(scene.name+'-Ground-Material', (.24,.24,.24,1), .82)
    floor = rounded_box(scene.name+'-Ground', (span*5,span*5,.02), collection,
                        (0,0,-.015), bevel=0, material=ground)
    floor['dsh_role'] = 'stage'
    world_name = scene.name+'-World'
    world = bpy.data.worlds.get(world_name)
    if world and not world.get('dsh_owned'):
        raise ValueError('World name belongs to user data')
    if world is None:
        world = bpy.data.worlds.new(world_name)
    world['dsh_owned'] = True
    world.use_nodes = True
    # Default node *names* are translated in localized Blender. Construct by
    # RNA type rather than assuming a node named "Background" exists.
    world.node_tree.nodes.clear()
    background = world.node_tree.nodes.new('ShaderNodeBackground')
    output = world.node_tree.nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])
    background.inputs['Color'].default_value = (.32,.34,.38,1)
    background.inputs['Strength'].default_value = .45
    scene.world = world
    for label,loc,energy,size in [('Key',(-2.5,-3.0,5.5),950,4.0),
                                  ('Fill',(3,-1,3.5),550,3.0), ('Rim',(1,3.5,4),850,3.0)]:
        data = bpy.data.lights.new(scene.name+'-'+label, 'AREA')
        data.energy, data.shape, data.size = energy,'DISK',size
        obj = _owned(bpy.data.objects.new(data.name,data),collection,'stage')
        obj.location = loc
        aim(obj,target)
    camera = _owned(bpy.data.objects.new(camera_name,bpy.data.cameras.new(camera_name)),collection,'stage')
    camera.location = (-3.6,-4.2,4.5)
    aim(camera,target)
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = span*1.35
    camera.data.lens = 55
    scene.camera = camera
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x = scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    return camera


def set_camera_view(scene):
    if not bpy.context.window or bpy.context.window.scene != scene:
        return
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.type = 'MATERIAL'
