import numpy as np
import FreeCAD
import Part
import Mesh

# ==========================================
# 1. 基础几何展示与草图函数 (供 Terminal 调用)
# ==========================================
def show(shape, name="Shape"):
    """
    将给定的 Shape 显示在 FreeCAD 活动文档中。
    返回创建的 FreeCAD 特征对象。
    """
    doc = FreeCAD.ActiveDocument
    if not doc:
        doc = FreeCAD.newDocument("Unnamed")
        FreeCAD.setActiveDocument(doc.Name)
        
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    doc.recompute()
    return obj

def sketch(shape_obj, sketch_name=None):
    """
    将给定对象的所有 Face 边界提取并转换到 Sketch 中。
    如果指定的 Sketch 不存在，则自动创建。
    如果未指定名称，则自动命名为 Sketch_001, Sketch_002...
    """
    doc = FreeCAD.ActiveDocument
    if not doc:
        doc = FreeCAD.newDocument("Code3D_Sketch")
        FreeCAD.setActiveDocument(doc.Name)

    # 获取原始 Shape
    if hasattr(shape_obj, "Shape"):
        shape = shape_obj.Shape
    else:
        shape = shape_obj

    faces = shape.Faces
    if not faces:
        raise ValueError("The given object has no faces to extract.")

    # 自动生成名称
    if not sketch_name:
        idx = 1
        sketch_name = f"Sketch_{idx:03d}"
        while doc.getObject(sketch_name):
            idx += 1
            sketch_name = f"Sketch_{idx:03d}"

    # 查找或创建 Sketch 对象
    sk = doc.getObject(sketch_name)
    if not sk:
        sk = doc.addObject("Sketcher::SketchObject", sketch_name)
    elif sk.TypeId != "Sketcher::SketchObject":
        raise TypeError(f"'{sketch_name}' already exists but is not a Sketch object.")

    # 尝试将 Sketch 的坐标平面自动对齐到第一个 Face 所在的平面
    first_face = faces[0]
    try:
        if hasattr(first_face.Surface, "Axis") and hasattr(first_face.Surface, "Position"):
            plane_axis = first_face.Surface.Axis
            plane_pos = first_face.Surface.Position
            rot = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), plane_axis)
            sk.Placement = FreeCAD.Placement(plane_pos, rot)
    except Exception:
        pass # 如果平面推断失败，保持默认的 XY 平面

    # 提取边并添加
    count = 0
    for face in faces:
        for edge in face.Edges:
            try:
                # 参数 False 表示添加为普通实线（若为 True 则是构造线）
                sk.addGeometry(edge, False)
                count += 1
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Failed to add edge: {e}\n")

    doc.recompute()
    FreeCAD.Console.PrintMessage(f"✅ Successfully added {count} edges to Sketch '{sketch_name}'.\n")
    return sk


# ==========================================
# 2. 几何辅助工具函数
# ==========================================
def _is_vec(x, n: int) -> bool:
    """Support FreeCAD.Vector / list / tuple / ndarray"""
    if isinstance(x, FreeCAD.Vector):
        return n == 3
    try:
        arr = np.asarray(x)
        return arr.ndim == 1 and arr.size == n and np.issubdtype(arr.dtype, np.number)
    except Exception:
        return False

def _vec(x) -> tuple:
    """将输入转换为标准的 Python 浮点数元组"""
    return tuple(float(v) for v in x)

def _tessellate(shape, tol: float = 0.1):
    """
    将 FreeCAD Shape 离散化为网格 (Vertices, Faces)
    返回 Numpy 格式的顶点坐标和面片索引。
    """
    if isinstance(shape, FreeCAD.Vector) or isinstance(shape, (int, float)):
        return np.array([]), []
    verts, faces = shape.tessellate(tol)
    vert_array = np.array([[v.x, v.y, v.z] for v in verts])
    return vert_array, faces

def _tri_mesh_to_shape(verts, faces, name="CQ_Object"):
    """
    将三角形网格 (Vertices, Faces) 转换回 FreeCAD 的 B-Rep 实体。
    使用了原生 API 的 makeShapeFromMesh，并尝试转为 Solid。
    """
    mesh = Mesh.Mesh()
    
    for f in faces:
        v0, v1, v2 = verts[f[0]], verts[f[1]], verts[f[2]]
        mesh.addFacet(
            float(v0[0]), float(v0[1]), float(v0[2]),
            float(v1[0]), float(v1[1]), float(v1[2]),
            float(v2[0]), float(v2[1]), float(v2[2])
        )
    
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Topology, 0.1)
    
    try:
        solid = Part.makeSolid(shape)
        if hasattr(solid, 'ShapeType') and solid.ShapeType == "Solid":
            shape = solid
    except Exception:
        pass
        
    return shape

def extremes(part) -> tuple:
    """
    获取几何体的包围盒极值。
    返回格式: (XMin, XMax, YMin, YMax, ZMin, ZMax)
    """
    bb = part.BoundBox
    return bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax

def fillet_chamfer(value):
    """
    对当前选中的对象或边进行圆角或倒角。
    如果 value > 0，执行 Fillet（圆角）。
    如果 value < 0，执行 Chamfer（倒角）。
    """
    import FreeCAD
    import FreeCADGui
    
    selection = FreeCADGui.Selection.getSelectionEx()
    if not selection:
        raise ValueError("Please select objects or edges in the 3D view or tree first.")
        
    doc = FreeCAD.ActiveDocument
    if not doc:
        raise ValueError("No active document.")
        
    success_count = 0
    for sel in selection:
        obj = sel.Object
        if not hasattr(obj, "Shape") or not obj.Shape:
            continue
            
        shape = obj.Shape
        edges_to_process = []
        
        # 判断是否选中了子元素（比如边、面）
        if sel.SubObjects:
            for sub in sel.SubObjects:
                if sub.ShapeType == "Edge":
                    edges_to_process.append(sub)
        else:
            # 如果没选子元素，而是选了整个实体，则对其所有边操作
            edges_to_process = shape.Edges
            
        if not edges_to_process:
            continue
            
        try:
            # 获取边的索引列表
            indices = [shape.Edges.index(e) for e in edges_to_process]
            
            if value > 0:
                new_shape = shape.makeFillet(value, indices)
                suffix = "Fillet"
            else:
                new_shape = shape.makeChamfer(-value, indices)
                suffix = "Chamfer"
                
            # 生成新对象
            new_obj = doc.addObject("Part::Feature", f"{obj.Name}_{suffix}")
            new_obj.Shape = new_shape
            
            # 隐藏原对象
            if hasattr(obj, 'ViewObject') and obj.ViewObject:
                obj.ViewObject.Visibility = False
                
            success_count += 1
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Failed to process {obj.Name}: {e}\n")
            
    if success_count > 0:
        doc.recompute()
        FreeCAD.Console.PrintMessage(f"✅ Successfully applied {'Fillet' if value > 0 else 'Chamfer'} to {success_count} object(s).\n")
    else:
        raise ValueError("No valid edges found to fillet/chamfer, or operation failed.")
