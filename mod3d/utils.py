import numpy as np
import FreeCAD
import Part
import Mesh

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

def apply_fillet_chamfer(shape, radius, selected_edges=None):
 
    if not shape.Edges:
        return shape
        
    edges_to_process = []
    if selected_edges:
        for e in selected_edges:
            for orig_e in shape.Edges:
             
                if orig_e.CenterOfMass.distanceToPoint(e.CenterOfMass) < 1e-4:
                    edges_to_process.append(orig_e)
                    break
    
        if not edges_to_process:
            edges_to_process = shape.Edges
    else:
        edges_to_process = shape.Edges

    if not edges_to_process:
        return shape

    try:
       
        if radius > 0:
            return shape.makeFillet(radius, edges_to_process)
        elif radius < 0:
            return shape.makeChamfer(-radius, edges_to_process)
        return shape
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"Fillet/Chamfer failed: {e}\n")
        return shape
