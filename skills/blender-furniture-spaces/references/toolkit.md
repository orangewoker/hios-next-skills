# furniture_kit API

在 `exec` 的脚本中 `import furniture_kit as kit`。几何内部单位为米，角度为弧度；所有构件函数都接收显式 collection，不依赖选中状态。

```python
import bpy, furniture_kit as kit
scene, collection = kit.task_scene('DSH-MyFurniture', 'DSH-MyFurniture-GEO')
cloth = kit.fabric_material('DSH-MyFurniture-Cloth', (0.055, 0.064, 0.076, 1))
seat = kit.pillow('DSH-MyFurniture-Seat', (2.2, .76, .19), collection,
                  location=(0, 0, .38), radius=.065, crown=.028,
                  material=cloth, subdivisions=1)
_dsh_result = {'scene': scene.name, 'seat': seat.name}
```

- `task_scene(scene_name, collection_name)`：新建或获取任务 scene，若有窗口则切换到它。不会删除已有 scene。**只有调用方自有的 scene 名可以用于该函数**。
- `clear_collection(collection)`：只删除这个集合中、本库带 `dsh_owned` 属性的对象，保留用户后来加入的其他对象。空集合的 mesh/material 数据不全局 purge。
- `rounded_box(name, size, collection, location, bevel, material)`：硬质圆角板件，有保留的 Bevel 修改器；不是软包替代。
- `extruded_outline(name, outline, bottom, top, collection, material, bevel)`：逆时针 XY 闭合轮廓挤出，适合异形柜体/台面，而非把异形结构全做成长方体。
- `pillow(name, size, collection, location, radius, crown, material, subdivisions, tuck)`：按圆角截面放样的闭合软包，具鼓面与收紧边缘，平滑网格与可选细分修改器。
- `tube(name, points, collection, radius, material, cyclic)`：三维曲线滚边或细金属杆，真实圆截面。
- `fabric_material(name, color)` / `wood_material(name, color)` / `plain_material(name, color, roughness, metallic)`：有稳定名称的程序材质。给现有同名**非任务**材质起新名，不要覆盖用户网络。
- `wall_with_openings(name, length, height, thickness, collection, openings, location, material)`：沿 X 的墙，`openings=[{'x':中心X, 'width':宽, 'bottom':窗台Z, 'height':高}]`，坐标相对墙中心。生成墙段，不以实心块遮挡洞口；拒绝越界洞口。
- `studio(scene, collection, target, span, camera_name)`：仅在自己的 task scene 中使用，添加地面、面积灯、任务世界及对准模型的相机；不替换其他 scene 的灯光。返回相机，位置可改后 `kit.aim(camera, target)`。
- `set_camera_view(scene)`：将当前窗口该 scene 的 3D 视图切到相机，不操作其他窗口。

对象 `dsh_parameters` 记录关键输入。`task_scene()` 本身不删除内容；重建脚本需在明确自己的集合上调用 `clear_collection()`，不允许全局删除。复杂轮廓不适配这些基础函数时，直接用 `bpy.data.meshes`、`bmesh` 或截面放样自建，不强行套库。
