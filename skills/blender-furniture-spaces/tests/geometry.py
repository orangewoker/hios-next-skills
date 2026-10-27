"""Run with Blender --background --factory-startup --python-exit-code 1 --python FILE.
Never run this test by loading factory settings in a user's live session.
"""
import bpy
import bmesh
import json
import math
import os
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(root/'lib'))
import furniture_kit as kit

original_scene=bpy.context.scene
original_objects={obj.name for obj in original_scene.objects}
scene,col=kit.task_scene('DSH-Test-Curves','DSH-Test-Curves-GEO')
fabric=kit.fabric_material('DSH-Test-Fabric')
wood=kit.wood_material('DSH-Test-Wood')
cushion=kit.pillow('DSH-Test-Pillow',(2.0,.8,.18),col,crown=.03,material=fabric,subdivisions=1)
assert len(cushion.data.vertices)>500
zs=[v.co.z for v in cushion.data.vertices]
assert max(zs)>.115 and min(zs)<-.09, 'Cushion must have actual crown and underside, not a flat box'
bm=bmesh.new();bm.from_mesh(cushion.data)
assert not any(not edge.is_manifold for edge in bm.edges), 'Cushion must be closed manifold'
assert bm.calc_volume(signed=True)>0, 'Cushion winding must point outward'
bm.free()
assert any(mod.type=='SUBSURF' for mod in cushion.modifiers)
assert len(fabric.node_tree.nodes)>15
bsdf=next(n for n in fabric.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
assert bsdf.inputs['Normal'].is_linked and bsdf.inputs['Base Color'].is_linked
assert {o.name for o in original_scene.objects}==original_objects

# Geometric aperture: no wall cell intersects the actual door opening.
walls=kit.wall_with_openings('DSH-Test-Wall',4,2.8,.2,col,
    openings=[{'x':-.8,'width':.9,'bottom':0,'height':2.1},
              {'x':.9,'width':1.0,'bottom':.9,'height':1.2}],material=wood)
volume=0
for wall in walls:
    params=json.loads(wall['dsh_parameters'])
    xs=[v.co.x+wall.location.x for v in wall.data.vertices]
    zs=[v.co.z+wall.location.z for v in wall.data.vertices]
    midx,midz=(min(xs)+max(xs))/2,(min(zs)+max(zs))/2
    assert not (-1.25<midx<-.35 and 0<midz<2.1)
    assert not (.4<midx<1.4 and .9<midz<2.1)
    volume+=(max(xs)-min(xs))*.2*(max(zs)-min(zs))
assert abs(volume-(4*2.8-.9*2.1-1.0*1.2)*.2)<1e-5
try:
    kit.wall_with_openings('Invalid',4,2.8,.2,col,openings=[{'x':3,'width':1,'bottom':0,'height':2}])
    raise AssertionError('Out-of-bounds opening was accepted')
except ValueError:
    pass

example=root/'examples'/'reference-sofa.py'
namespace={'__name__':'__main__','__file__':str(example)}
exec(compile(example.read_text(encoding='utf-8'),str(example),'exec'),namespace)
first=namespace['_dsh_result']
sofa_col=bpy.data.collections[first['collection']]
first_names={obj.name for obj in sofa_col.objects}
for node in bpy.data.scenes[first['scene']].world.node_tree.nodes:
    node.name='本地化和用户自定义节点-'+str(node.as_pointer())
for name in first['curvedParts']:
    obj=bpy.data.objects[name]
    assert len(obj.data.vertices)>500
    assert any(mod.type=='SUBSURF' for mod in obj.modifiers)
    assert obj.data.materials
for obj in sofa_col.objects:
    assert all(math.isfinite(v) for row in obj.matrix_world for v in row)

# A user-added object in our collection is not owned and must survive a rebuild.
sentinel=bpy.data.objects.new('User-Added-Sentinel',None)
sofa_col.objects.link(sentinel)
exec(compile(example.read_text(encoding='utf-8'),str(example),'exec'),namespace)
assert {o.name for o in sofa_col.objects}==first_names|{'User-Added-Sentinel'}
assert bpy.data.objects.get('User-Added-Sentinel') is sentinel
assert {o.name for o in original_scene.objects}==original_objects

# Non-default dimension configuration must transform rotated geometry in world
# space, not translate using a stale matrix or scale the entire scene/floor.
if os.environ.get('DSH_TEST_OUTPUT'):
    config=Path(os.environ['DSH_TEST_OUTPUT'])/'scale-config.json'
    config.parent.mkdir(parents=True,exist_ok=True)
    config.write_text(json.dumps({'length':3.30,'depth':1.12,'height':.94,'prefix':'DSH-ScaledSofa'}),encoding='utf-8')
    scaled={'__name__':'__main__','__file__':str(example),'DSH_SOFA_CONFIG':str(config)}
    exec(compile(example.read_text(encoding='utf-8'),str(example),'exec'),scaled)
    box=bpy.data.objects['DSH-ScaledSofa-Timber-Base']
    bpy.data.scenes['DSH-ScaledSofa'].view_layers[0].update()
    assert abs(box.dimensions.x-3.30)<.001 and abs(box.dimensions.y-1.12)<.001
    from mathutils import Vector
    points=[o.matrix_world@Vector(co) for o in bpy.data.collections['DSH-ScaledSofa-Furniture'].objects
            if o.type=='MESH' and o.get('dsh_role')!='stage' for co in o.bound_box]
    assert 3.29<max(p.x for p in points)-min(p.x for p in points)<3.4
    assert .85<max(p.z for p in points)<1.1
    if bpy.context.window:
        bpy.context.window.scene=bpy.data.scenes[first['scene']]

output=os.environ.get('DSH_TEST_OUTPUT')
if output:
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'tested-sofa.blend'))
    (out/'geometry-report.json').write_text(json.dumps({
        'ok':True,'pillowVertices':len(cushion.data.vertices),'wallCells':len(walls),
        'sofaObjects':len(sofa_col.objects),'originalScenePreserved':True,
        'rebuildIdempotent':True,'userAddedObjectPreserved':True,
    },indent=2),encoding='utf-8')
print('DSH_GEOMETRY_TESTS_PASSED')
