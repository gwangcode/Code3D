import FreeCAD
import Part
import Mesh

def show(shape, name="Shape"):
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
    """
    from mod3d.shapes import Shape2d
    
    doc = FreeCAD.ActiveDocument
    if not doc:
        doc = FreeCAD.newDocument("Code3D_Sketch")
        FreeCAD.setActiveDocument(doc.Name)

    # 【核心修复】处理不同类型的几何输入
    if isinstance(shape_obj, Shape2d):
        shape = shape_obj.to_face()
    elif hasattr(shape_obj, "Shape"):  # mod3d.Shape 包装类
        shape = shape_obj.Shape
    else:                              # 原生 Part.Shape
        shape = shape_obj

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

    # 自动对齐 Sketch 平面
    first_face = faces[0]
    try:
        if hasattr(first_face.Surface, "Axis") and hasattr(first_face.Surface, "Position"):
            plane_axis = first_face.Surface.Axis
            plane_pos = first_face.Surface.Position
            rot = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), plane_axis)
            sk.Placement = FreeCAD.Placement(plane_pos, rot)
    except Exception:
        pass

    # 计算逆向变换矩阵，用于将 3D 全局坐标转换为 Sketch 的局部 2D 坐标
    inv_placement = sk.getGlobalPlacement().inverse()

    count = 0
    for face in faces:
        for edge in face.Edges:
            try:
                curve = edge.Curve
                
                # 把 Part.Edge 转换为 Sketch 支持的几何原语
                if isinstance(curve, Part.Line):
                    p1 = inv_placement.multVec(edge.Vertexes[0].Point)
                    p2 = inv_placement.multVec(edge.Vertexes[-1].Point)
                    sk.addGeometry(Part.LineSegment(p1, p2), False)
                    count += 1
                    
                elif isinstance(curve, Part.Circle):
                    center = inv_placement.multVec(curve.Center)
                    normal = inv_placement.Rotation.multVec(curve.Axis)
                    local_circle = Part.Circle(center, normal, curve.Radius)
                    sk.addGeometry(local_circle, False)
                    count += 1
                    
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Failed to add edge: {e}\n")

    doc.recompute()
    FreeCAD.Console.PrintMessage(f"✅ Successfully added {count} geometries to Sketch '{sketch_name}'.\n")
    return sk

def _is_vec(x, n: int) -> bool:
    if isinstance(x, FreeCAD.Vector):
        return n == 3
    try:
        import numpy as np
        arr = np.asarray(x)
        return arr.ndim == 1 and arr.size == n and np.issubdtype(arr.dtype, np.number)
    except Exception:
        return False

def _vec(x) -> tuple:
    return tuple(float(v) for v in x)

def _tessellate(shape, tol: float = 0.1):
    import numpy as np
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

def apply_fillet_chamfer(shape, radius, selected_edges=None):
    if not shape.Edges:
        return shape
        
    indices = []
    if selected_edges:
        for e in selected_edges:
            for i, orig_e in enumerate(shape.Edges):
                if orig_e.CenterOfMass.distanceToPoint(e.CenterOfMass) < 1e-4:
                    indices.append(i)
                    break
        if not indices:
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
