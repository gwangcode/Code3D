import numpy as np
import FreeCAD
import Part
import Mesh

# ==========================================
# 1. 基础几何展示函数 (供 Terminal 调用)
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


# ==========================================
# 2. 几何辅助工具函数 (新增)
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
    
    # 直接传入 9 个 float 构建三角面，兼容性最好
    for f in faces:
        v0, v1, v2 = verts[f[0]], verts[f[1]], verts[f[2]]
        mesh.addFacet(
            float(v0[0]), float(v0[1]), float(v0[2]),
            float(v1[0]), float(v1[1]), float(v1[2]),
            float(v2[0]), float(v2[1]), float(v2[2])
        )
    
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Topology, 0.1)
    
    # 尝试转换为实体，确保后续的布尔运算和倒角不出错
    try:
        solid = Part.makeSolid(shape)
        if hasattr(solid, 'ShapeType') and solid.ShapeType == "Solid":
            shape = solid
    except Exception:
        # 如果转换失败，保持原状（可能是壳体 Shell）
        pass
        
    return shape

def extremes(part) -> tuple:
    """
    获取几何体的包围盒极值。
    返回格式: (XMin, XMax, YMin, YMax, ZMin, ZMax)
    """
    bb = part.BoundBox
    # 【修复】修正了原代码中的拼写错误 ZMaxa -> ZMax
    return bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax
