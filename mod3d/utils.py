import numpy as np
import FreeCAD
import Part
import Mesh

# ==========================================
# 1. 基础几何展示与草图函数
# ==========================================
def show(shape, name="Shape"):
    """将给定的 Shape 显示在 FreeCAD 活动文档中。"""
    doc = FreeCAD.ActiveDocument
    if not doc:
        doc = FreeCAD.newDocument("Unnamed")
        FreeCAD.setActiveDocument(doc.Name)
        
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    doc.recompute()
    return obj

def sketch(shape_obj, sketch_name=None):
    """将给定对象的所有 Face 边界提取并转换到 Sketch 中。"""
    doc = FreeCAD.ActiveDocument
    if not doc:
        doc = FreeCAD.newDocument("Code3D_Sketch")
        FreeCAD.setActiveDocument(doc.Name)

    shape = shape_obj.Shape if hasattr(shape_obj, "Shape") else shape_obj
    faces = shape.Faces
    if not faces:
        raise ValueError("The given object has no faces to extract.")

    if not sketch_name:
        idx = 1
        sketch_name = f"Sketch_{idx:03d}"
        while doc.getObject(sketch_name):
            idx += 1
            sketch_name = f"Sketch_{idx:03d}"

    sk = doc.getObject(sketch_name)
    if not sk:
        sk = doc.addObject("Sketcher::SketchObject", sketch_name)
    elif sk.TypeId != "Sketcher::SketchObject":
        raise TypeError(f"'{sketch_name}' already exists but is not a Sketch object.")

    first_face = faces[0]
    try:
        if hasattr(first_face.Surface, "Axis") and hasattr(first_face.Surface, "Position"):
            plane_axis = first_face.Surface.Axis
            plane_pos = first_face.Surface.Position
            rot = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), plane_axis)
            sk.Placement = FreeCAD.Placement(plane_pos, rot)
    except Exception:
        pass

    count = 0
    for face in faces:
        for edge in face.Edges:
            try:
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
    if isinstance(x, FreeCAD.Vector):
        return n == 3
    try:
        arr = np.asarray(x)
        return arr.ndim == 1 and arr.size == n and np.issubdtype(arr.dtype, np.number)
    except Exception:
        return False

def _vec(x) -> tuple:
    return tuple(float(v) for v in x)

def _tessellate(shape, tol: float = 0.1):
    if isinstance(shape, FreeCAD.Vector) or isinstance(shape, (int, float)):
        return np.array([]), []
    verts, faces = shape.tessellate(tol)
    vert_array = np.array([[v.x, v.y, v.z] for v in verts])
    return vert_array, faces

def _tri_mesh_to_shape(verts, faces, name="CQ_Object"):
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
    bb = part.BoundBox
    return bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax

# ==========================================
# 3. 核心圆角与倒角处理 (新增)
# ==========================================
def apply_fillet_chamfer(shape, radius, selected_edges=None):
    """
    执行倒角/圆角操作。
    :param shape: FreeCAD 的原始 Shape
    :param radius: 正数为圆角(Fillet)，负数为倒角(Chamfer)
    :param selected_edges: 选中的特定边，若为 None 则处理所有边
    """
    if not shape.Edges:
        return shape
        
    if selected_edges:
        try:
            indices = [shape.Edges.index(e) for e in selected_edges]
        except ValueError:
            indices = list(range(len(shape.Edges)))
    else:
        indices = list(range(len(shape.Edges)))

    if not indices:
        return shape

    try:
        if radius > 0:
            return shape.makeFillet(radius, indices)
        elif radius < 0:
            return shape.makeChamfer(-radius, indices)
        return shape
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"Fillet/Chamfer failed: {e}\n")
        return shape
