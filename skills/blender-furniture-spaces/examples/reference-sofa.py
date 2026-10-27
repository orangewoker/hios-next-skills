"""Editable recreation study of the supplied charcoal fabric / timber sofa.
Dimensions and hidden structure are estimates, not measured reconstruction.
Optional configuration: DSH_SOFA_CONFIG global path to JSON, or environment variable.
"""
import bpy
import json
import math
import os
from pathlib import Path
import furniture_kit as kit

config_path = globals().get('DSH_SOFA_CONFIG') or os.environ.get('DSH_SOFA_CONFIG')
config = json.loads(Path(config_path).read_text(encoding='utf-8')) if config_path else {}
length = float(config.get('length', 2.85))
depth = float(config.get('depth', 1.02))
height = float(config.get('height', .86))
if not 1.8 <= length <= 4.0 or not .7 <= depth <= 1.5 or not .65 <= height <= 1.3:
    raise ValueError('Sofa dimensions outside this example parameterization')
sx,sy,sz = length/2.85,depth/1.02,height/.86
prefix = str(config.get('prefix','DSH-ReferenceSofa'))
scene, collection = kit.task_scene(prefix, prefix+'-Furniture')
kit.clear_collection(collection)
cloth = kit.fabric_material(prefix+'-Charcoal-Linen', (.007,.009,.013,1))
edge_cloth = kit.fabric_material(prefix+'-Edge-Thread', (.005,.006,.008,1))
wood = kit.wood_material(prefix+'-Warm-Walnut', (.21,.087,.022,1))
shadow = kit.plain_material(prefix+'-Inset-Plinth', (.018,.014,.011,1), .56)
brass = kit.plain_material(prefix+'-Aged-Brass', (.23,.14,.055,1), .29,.78)

# All parts are created in metric local geometry, then dimensional controls are
# applied to mesh coordinates (not object scaling / texture scaling).
base = kit.rounded_box(prefix+'-Timber-Base', (2.85,1.02,.09),collection,
                       (0,0,.205),bevel=.034,material=wood)
kit.rounded_box(prefix+'-Recessed-Support', (2.53,.76,.15),collection,
                (0,.02,.095),bevel=.025,material=shadow)

seat = kit.pillow(prefix+'-Continuous-Crowned-Seat', (2.67,.80,.18),collection,
                   location=(0,-.085,.354),radius=.075,crown=.029,material=cloth,subdivisions=2)

def seat_plan(x,y):
    # The rear-left seat narrows around the curved end wing and timber cabinet;
    # the front edge stays long. This is a tailored silhouette, not an L sofa.
    end = max(0,min(1,(-x-.65)/.68))
    rear = max(0,min(1,(y+.13)/.48))
    rear = rear*rear*(3-2*rear)
    return x+.39*end**2*rear, y

for v in seat.data.vertices:
    v.co.x,v.co.y = seat_plan(v.co.x,v.co.y)
seat['dsh_feature'] = 'continuous crowned cushion with shaped rear-left return'
seat.data.update()

back = kit.pillow(prefix+'-Inclined-Continuous-Back', (2.32,.50,.14),collection,
                   location=(.165,.335,.594),radius=.052,crown=.023,material=cloth,subdivisions=2)
back.rotation_euler.x = math.radians(78)

# Sculpted short left return: a vertical soft profile lofted along a curved
# plan spine, with a descending height. Separate editable mesh + Subdivision.
vertices,faces = [],[]
stations = 29
for j in range(stations):
    t = j/(stations-1)
    x = -.925-.225*math.sin(t*math.pi/2)
    y = .34-.79*t
    dx = -.225*math.pi/2*math.cos(t*math.pi/2)
    dy = -.79
    denom = math.hypot(dx,dy)
    nx,ny = -dy/denom,dx/denom
    h = .50-.34*t**1.25
    bottom = .305
    for offset,z in kit.rounded_rectangle(.112,h,.047,segments=8):
        # Gentle swelling of inner/outer upholstery, not a straight board.
        bulge = .010*math.sin(math.pi*(z/h+.5))
        offset += math.copysign(bulge,offset)
        vertices.append((x+nx*offset,y+ny*offset,bottom+h/2+z))
n = len(vertices)//stations
for j in range(stations-1):
    for i in range(n):
        faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
faces.append(tuple(reversed(range(n))))
faces.append(tuple((stations-1)*n+i for i in range(n)))
wing = kit.mesh_object(prefix+'-Curved-Descending-End-Wing',vertices,faces,collection,cloth,True)
wing['dsh_parameters'] = json.dumps({'kind':'curved-profile-loft','stations':stations,'heightRange':[.50,.16]})
sub = wing.modifiers.new('Editable curved wing','SUBSURF')
sub.levels = sub.render_levels = 2

# Wood cabinet: separate shell, door, countertop and a tiny real brass loop.
# The side view not visible in the image is an explicit structural inference.
cabinet_outline=[(-1.399,-.269),(-1.174,-.269),(-1.129,-.14),
                 (-1.066,.075),(-.963,.424),(-1.399,.424)]
kit.extruded_outline(prefix+'-End-Cabinet-Core',cabinet_outline,.260,.591,collection,wood,.006)
top_outline=[(-1.414,-.282),(-1.162,-.282),(-1.117,-.145),
             (-1.053,.072),(-.947,.437),(-1.414,.437)]
kit.extruded_outline(prefix+'-End-Cabinet-Top',top_outline,.591,.618,collection,wood,.005)
door = kit.rounded_box(prefix+'-End-Cabinet-Door',(.022,.61,.299),collection,
                       (-1.405,.105,.423),bevel=.004,material=wood)
# Local-X wood direction runs across the face rather than into its thickness.
for v in door.data.vertices:
    x,y,z = v.co
    v.co = (y,-x,z)
door.rotation_euler.z = math.pi/2
pull_points = [(-1.424,.087+.009*math.cos(2*math.pi*i/48),.462+.022*math.sin(2*math.pi*i/48)) for i in range(48)]
kit.tube(prefix+'-Cabinet-Brass-Pull',pull_points,collection,.0017,brass,True)
for y in (.078,.096):
    kit.rounded_box(prefix+f'-Pull-Mount-{y}',(.009,.007,.006),collection,
                    (-1.421,y,.478),bevel=.002,material=brass)

# Restrained inset seams around soft sections, following the same shape math.
seat_points=[]
for x,y in kit.rounded_rectangle(2.67-.017,.80-.017,.071,segments=22):
    x,y=seat_plan(x,y)
    seat_points.append((x,y-.085,.354+.055))
kit.tube(prefix+'-Seat-Edge-Welt',seat_points,collection,.00105,edge_cloth,True)
back_points=[]
for x,y in kit.rounded_rectangle(2.32-.019,.50-.019,.048,segments=22):
    z=.045
    a=math.radians(78)
    back_points.append((x+.165,y*math.cos(a)-z*math.sin(a)+.335,
                        y*math.sin(a)+z*math.cos(a)+.594))
kit.tube(prefix+'-Back-Edge-Welt',back_points,collection,.001,edge_cloth,True)

# Configured overall dimensions, without scaling physical shader coordinates.
# Keep the example's bevel radii/threads at actual material scale.
scene.view_layers[0].update()
for obj in list(collection.objects):
    if obj.type == 'MESH':
        # Apply the global affine change in world space, then return to local
        # coordinates so rotated back/door parts remain editable and correct.
        matrix=obj.matrix_world.copy()
        inverse=matrix.inverted()
        for v in obj.data.vertices:
            world=matrix@v.co
            world.x*=sx; world.y*=sy; world.z*=sz
            v.co=inverse@world
        obj.data.update()
    elif obj.type == 'CURVE':
        for spline in obj.data.splines:
            for p in spline.points:
                p.co.x*=sx; p.co.y*=sy; p.co.z*=sz

camera=kit.studio(scene,collection,target=(0,0,.40*sz),span=length,camera_name=prefix+'-Camera-Reference')
camera.location=(-4.8,-3.2,5.3)
kit.aim(camera,(0,0,.37*sz))
camera.data.ortho_scale=length*1.30
# Additional side/front cameras expose cushion curvature, rear inclination and
# the independent door, rather than relying on one flattering hero view.
for suffix,loc,target in [('Front',(0,-4.7,1.65),(0,0,.42)),('End',(-4.7,-.8,1.9),(-.30,0,.42)),
                           ('Detail',(-2.1,-1.85,1.5),(-.9,-.02,.47))]:
    data=bpy.data.cameras.new(prefix+'-Camera-'+suffix)
    cam=bpy.data.objects.new(data.name,data)
    cam['dsh_owned']=True;cam['dsh_role']='stage'
    collection.objects.link(cam)
    cam.location=loc
    kit.aim(cam,target)
    data.type='ORTHO'
    data.ortho_scale=1.35 if suffix=='Detail' else length*1.20
kit.set_camera_view(scene)
scene['dsh_model_spec']=json.dumps({
    'reference':'user charcoal textile sofa with timber end cabinet',
    'dimensionsMeters':{'length':length,'depth':depth,'height':height},
    'dimensionStatus':'estimated from a single perspective image',
    'observed':['continuous grey fabric seat','inclined back','curved short end wing','wood base','end storage cabinet'],
    'inferred':['recessed support','unseen rear construction','door joinery'],
},ensure_ascii=False)
scene.view_layers[0].update()
_dsh_result={'scene':scene.name,'collection':collection.name,'camera':camera.name,
             'objects':len(collection.objects),'dimensionsEstimated':True,
             'dimensionsMeters':[length,depth,height],
             'curvedParts':[seat.name,back.name,wing.name]}
print(json.dumps(_dsh_result,ensure_ascii=False))
