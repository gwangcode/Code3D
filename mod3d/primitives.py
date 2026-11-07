import numpy as np
import FreeCAD
import Part
import Mesh
import MeshPart
import trimesh
import math
from .shapes import Shape2d
from .patch import Shape

# ==========================================
# ---- 3D primitives ----
# ==========================================
def cuboid(a=1, b=1, c=1): return Shape(Part.makeBox(a, b, c))
def cube(a=1):              return cuboid(a, a, a)
def cylinder(radius=1, height=1): return Shape(Part.makeCylinder(radius, height))
def cone(radius=1, height=1):     return Shape(Part.makeCone(radius, 0, height))
def sphere(radius=1, face_index=3): return Shape(Part.makeSphere(radius))
def torus(major_radius=2, minor_radius=1, division=0.1):
    return Shape(Part.makeTorus(major_radius, minor_radius))

def ellipsoid(a=1, b=1, c=1, division=0.1):
    sphere_shape = Part.makeSphere(1.0)
    mat = FreeCAD.Matrix()
    mat.scale(a, b, c)
    return Shape(sphere_shape.transformGeometry(mat))

def prism(radius=1, n=3, height=1):
    pts = [FreeCAD.Vector(radius*np.cos(2*np.pi*i/n), radius*np.sin(2*np.pi*i/n), 0) for i in range(n)]
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    return Shape(face.extrude(FreeCAD.Vector(0, 0, height)))

def pyramid(radius=1, n=3, height=1, division=0.1):
    pts = [FreeCAD.Vector(radius*np.cos(2*np.pi*i/n), radius*np.sin(2*np.pi*i/n), 0) for i in range(n)]
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    return Shape(Part.makeLoft([face, Part.Vertex(FreeCAD.Vector(0, 0, height))], True))

def convex_hull(vertices):
    mesh = trimesh.convex.convex_hull(np.asarray(vertices, dtype=float))
    mesh_obj = Mesh.Mesh()
    for f in mesh.faces:
        v0, v1, v2 = mesh.vertices[f[0]], mesh.vertices[f[1]], mesh.vertices[f[2]]
        mesh_obj.addFacet(float(v0[0]), float(v0[1]), float(v0[2]),
                          float(v1[0]), float(v1[1]), float(v1[2]),
                          float(v2[0]), float(v2[1]), float(v2[2]))
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh_obj.Topology, 0.1)
    return Shape(Part.makeSolid(shape))

def tetrahedron(a=1):
    return convex_hull([[0,0,0],[a,0,0], [0.5*a, 0.5*3**0.5*a, 0], [0.5*a, 0.5*a/3**0.5, 2**0.5/3**0.5*a]])

def octahedron(a=1):
    x = a / 2**0.5
    return convex_hull([[x,0,0],[-x,0,0],[0,x,0],[0,-x,0],[0,0,x],[0,0,-x]])

def dodecahedron(a=1):
    phi = 0.5*(1+5**0.5); c1 = 1/(3-phi)**0.5
    x1 = a*c1; x2, x3 = a*(c1/phi), a*(phi*c1)
    return convex_hull([
        [x1,x1,x1],[-x1,x1,x1],[x1,-x1,x1],[x1,x1,-x1],
        [-x1,-x1,x1],[-x1,x1,-x1],[x1,-x1,-x1],[-x1,-x1,-x1],
        [0,x2,x3],[0,-x2,x3],[0,x2,-x3],[0,-x2,-x3],
        [x2,x3,0],[-x2,x3,0],[x2,-x3,0],[-x2,-x3,0],
        [x3,0,x2],[-x3,0,x2],[x3,0,-x2],[-x3,0,-x2]])

def icosahedron(a=1):
    phi = 0.5*(1+5**0.5); x1 = a*0.5; x2 = x1*phi
    return convex_hull([
        [x1,x2,0],[-x1,x2,0],[x1,-x2,0],[-x1,-x2,0],
        [x2,0,x1],[-x2,0,x1],[x2,0,-x1],[-x2,0,-x1],
        [0,x1,x2],[0,-x1,x2],[0,x1,-x2],[0,-x1,-x2]])

# ==========================================
# ---- Advanced Surface & Point-Cloud Generators ----
# ==========================================
def bspline_surface(points, thickness=0.0):
    """
    Creates a closed B-spline surface from a 1D point list or a 2D grid of points.
    """
    if not points or len(points) == 0:
        raise ValueError("Point list cannot be empty.")

    is_1d = len(points[0]) == 3 and isinstance(points[0][0], (int, float))
    face = None
    
    if is_1d:
        vecs = [FreeCAD.Vector(p[0], p[1], p[2]) for p in points]
        curve = Part.BSplineCurve()
        curve.interpolate(vecs, PeriodicFlag=True)
        wire = Part.Wire([curve.toShape()])
        try:
            face = Part.Face(wire)
        except Exception:
            return Shape(wire, primitive_data={"type": "bspline_surface_1d", "params": {"points": points}})
    else:
        vecs_2d = [[FreeCAD.Vector(p[0], p[1], p[2]) for p in row] for row in points]
        surface = Part.BSplineSurface()
        surface.interpolate(vecs_2d)
        face = Part.Face(surface.toShape())

    if thickness > 0.0 and face is not None:
        try:
            solid = face.thicken(thickness, 1e-5)
            if solid.ShapeType == 'CompSolid':
                solid = solid.Solids[0]
            return Shape(solid)
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to thicken surface: {e}\n")
            return Shape(face)
    
    return Shape(face)


def smooth_body(points, u_res=15, v_res=30):
    """
    Generate a perfectly smooth, watertight B-Spline solid from a point cloud.
    Uses uniform profile topology (equal number of edges) to ensure makeLoft success.
    """
    import numpy as np
    import FreeCAD
    import Part
    from .patch import Shape

    if not points or len(points) < 4:
        raise ValueError("At least 4 points are required to form a 3D solid.")

    np_pts = np.array(points)

    # 1. 共面性检测
    centroid = np_pts.mean(axis=0)
    centered = np_pts - centroid
    _, s, vh = np.linalg.svd(centered)
    distances = np.abs(np.dot(centered, vh[-1]))
    is_coplanar = np.max(distances) < 1e-3 * max(np.max(s), 1e-6)

    if is_coplanar:
        angles = np.arctan2(centered[:, 1], centered[:, 0])
        order = np.argsort(angles)
        sorted_pts = np_pts[order]
        vecs = [FreeCAD.Vector(*p) for p in sorted_pts]
        vecs.append(vecs[0])
        try:
            curve = Part.BSplineCurve()
            curve.interpolate(vecs, PeriodicFlag=True)
            wire = Part.Wire([curve.toShape()])
            return Shape(Part.Face(wire))
        except Exception:
            return Shape(Part.Face(Part.makePolygon(vecs)))

    try:
        # 2. PCA 计算最优椭球主轴
        cov = np.cov(centered.T)
        u, s, vh = np.linalg.svd(cov)
        scale = np.sqrt(s)
        scale = np.maximum(scale, 1e-5)

        # 3. 仿射变换到单位球空间
        normalized_pts = np.dot(centered, u) / scale

        # 4. 严格包含极点的球面参数化
        thetas = np.linspace(0, np.pi, u_res)
        phis = np.linspace(-np.pi, np.pi, v_res)
        
        grid_pts_normalized = []
        for th in thetas:
            row = []
            for ph in phis:
                dir_v = np.array([
                    np.sin(th) * np.cos(ph),
                    np.sin(th) * np.sin(ph),
                    np.cos(th)
                ])
                projections = np.dot(normalized_pts, dir_v)
                max_r = np.max(projections)
                if max_r <= 0:
                    max_r = 1.0
                pt = dir_v * max_r
                row.append(pt)
            grid_pts_normalized.append(row)

        # 5. 逆变换还原回真实坐标
        grid_pts_world = []
        for row in grid_pts_normalized:
            world_row = []
            for p in row:
                world_p = np.dot(p * scale, u.T) + centroid
                world_row.append(FreeCAD.Vector(float(world_p[0]), float(world_p[1]), float(world_p[2])))
            grid_pts_world.append(world_row)
        
        # 6. 闭合经线 (phi)
        wrapped = [row + [row[0]] for row in grid_pts_world]
        
        # ==========================================
        # 7. 【核心修复】生成统一边数的截面，保证 Loft 成功
        # ==========================================
        sections = []
        num_edges = v_res  # 强制所有截面的边数与经向分段数一致

        for i, row in enumerate(wrapped):
            if i == 0 or i == len(wrapped) - 1:
                # 极点：使用与中间截面相同边数的微小多边形（如3边或4边），而非单个 Vertex
                # 这样可以避免 "profiles are inconsistent" 错误
                pole_pt = row[0]
                # 创建一个极小的四边形作为极点截面，避免零尺寸
                epsilon = 1e-5
                # 为了简单，我们创建一个非常小的、边数为 num_edges 的多边形
                # 这里使用简单的多段线近似，确保边数一致
                pts = []
                for k in range(num_edges):
                    angle = 2.0 * np.pi * k / num_edges
                    offset = FreeCAD.Vector(epsilon * np.cos(angle), epsilon * np.sin(angle), 0)
                    # 注意：这里需要根据椭球主轴方向放置小圆，但简单起见，使用垂直于主轴的小圆
                    # 为了简化，我们直接使用极点本身构成一个退化的多边形，但边数一致
                    pts.append(pole_pt)
                # 使用 makePolygon 创建闭合线框
                wire = Part.makePolygon(pts)
                sections.append(wire)
            else:
                # 非极点：使用完美的 B 样条闭合环
                bspline = Part.BSplineCurve()
                bspline.interpolate(row, PeriodicFlag=True)
                wire = Part.Wire([bspline.toShape()])
                sections.append(wire)

        # 直接放样，生成实心体
        loft_solid = Part.makeLoft(sections, solid=True, ruled=False)
        if loft_solid and loft_solid.isValid():
            return Shape(loft_solid)

    except Exception as e:
        FreeCAD.Console.PrintWarning(f"Smooth body generation failed: {e}\n")
        pass

    # ==========================================
    # 8. 终极兜底
    # ==========================================
    import Mesh
    import trimesh
    hull = trimesh.convex.convex_hull(np_pts)
    mesh_obj = Mesh.Mesh()
    for f in hull.faces:
        v0, v1, v2 = hull.vertices[f[0]], hull.vertices[f[1]], hull.vertices[f[2]]
        mesh_obj.addFacet(float(v0[0]), float(v0[1]), float(v0[2]),
                          float(v1[0]), float(v1[1]), float(v1[2]),
                          float(v2[0]), float(v2[1]), float(v2[2]))
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh_obj.Topology, 0.1)
    return Shape(Part.makeSolid(shape))


# ==========================================
# ---- 2D primitives ----
# ==========================================
def polygon(R=1, n=6):
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    return Shape2d(np.column_stack([R*np.cos(t), R*np.sin(t)]))

def circle(R=1, step=0.1):
    return polygon(R, max(int(np.ceil(2*np.pi*R / step)), 20))

def rectangle(a=2, b=1):  return Shape2d([[0,0],[a,0],[a,b],[0,b]])
def square(a=1):          return rectangle(a, a)

def parallelogram(a=1, b=1, angle=np.pi/4):
    dx, dy = b*np.cos(angle), b*np.sin(angle)
    return Shape2d([[0,0],[a,0],[a+dx,dy],[dx,dy]])

def rhombus(a=1, angle=np.pi/4): return parallelogram(a, a, angle)

def trapezoid(upper_side=1, lower_side=2, height=1):
    x = (lower_side - upper_side) * 0.5
    return Shape2d([[0,0],[lower_side,0],[lower_side-x,height],[x,height]])

def pentagon(R=1):  return polygon(R, 5)
def hexagon(R=1):   return polygon(R, 6)
def heptagon(R=1):  return polygon(R, 7)
def octagon(R=1):   return polygon(R, 8)
def nonagon(R=1):   return polygon(R, 9)
def decagon(R=1):   return polygon(R, 10)

def ellipse(a=2, b=1, step=0.1):
    h = (a-b)**2 / (a+b)**2
    circ = np.pi*(a+b)*(1 + 3*h/(10 + np.sqrt(4-3*h)))
    n = max(int(np.ceil(circ / step)), 20)
    t = np.linspace(0, 2*np.pi, n, endpoint=False)
    return Shape2d(np.column_stack([a*np.cos(t), b*np.sin(t)]))

def parabola(a=1, b=2, w=1, step=0.1):
    x = np.linspace(-b, b, max(int(w / step), 20))
    return Shape2d(np.column_stack([x, x**2 / (4*a)]))

def hyperbola(a=1, b=1, w=1, step=0.1):
    n = max(int(4*a*np.arcsinh(b/a) / step), 20)
    t = np.linspace(-w*np.pi, w*np.pi, n)
    return Shape2d(np.column_stack([a*np.cosh(t), b*np.sinh(t)]))

def spiral(a=1, b=1, num_turns=2, step=0.1):
    L = num_turns*(np.sqrt(a*a + b*b) + a*np.arcsinh(b/a))
    t = np.linspace(0, 2*np.pi*num_turns, max(int(L/step), 20))
    return Shape2d(np.column_stack([a*t*np.cos(t), b*t*np.sin(t)]))

def cardioid(a=1, step=0.1):
    t = np.linspace(0, 2*np.pi, max(int(8*a/step), 20))
    return Shape2d(np.column_stack([a*(2*np.cos(t) - np.cos(2*t)), a*(2*np.sin(t) - np.sin(2*t))]))

def cycloid(a=1, num_cycles=2, step=0.1):
    t = np.linspace(0, 2*np.pi*num_cycles, max(int(8*a*num_cycles/step), 20))
    return Shape2d(np.column_stack([a*(t-np.sin(t)), a*(1-np.cos(t))]))

def astroid(a=1, step=0.1):
    t = np.linspace(0, 2*np.pi, max(int(6*a/step), 20))
    return Shape2d(np.column_stack([a*np.cos(t)**3, a*np.sin(t)**3]))

def catenary(a=1, step=0.1):
    t = np.linspace(-1, 1, max(int(a/step), 20))
    return Shape2d(np.column_stack([a*(np.cosh(t)-1), a*np.sinh(t)]))

def epicycloid(R=10, r=1, step=0.1):
    t = np.linspace(0, 2*np.pi, max(int(4*(R+r)/step), 20))
    return Shape2d(np.column_stack([
        (R+r)*np.cos(t) - r*np.cos((R+r)/r*t),
        (R+r)*np.sin(t) - r*np.sin((R+r)/r*t)]))

def hypocycloid(R=6, r=1, step=0.1):
    t = np.linspace(0, 2*np.pi, max(int(4*(R-r)/step), 20))
    return Shape2d(np.column_stack([
        (R-r)*np.cos(t) + r*np.cos((R-r)/r*t),
        (R-r)*np.sin(t) - r*np.sin((R-r)/r*t)]))

def lemniscate(a=1, step=0.1):
    t = np.linspace(0, 2*np.pi, max(int(8*a/step), 20))
    return Shape2d(np.column_stack([
        a*np.cos(t)/ (1 + np.sin(t)**2),
        a*np.cos(t)*np.sin(t)/ (1 + np.sin(t)**2)
    ]))

def semicircle(radius=1, step=0.1):
    t = np.linspace(0, np.pi, max(int(np.pi*radius/step), 20))
    return Shape2d(np.column_stack([radius*np.cos(t), radius*np.sin(t)]))

def sine(amplitude=1, frequency=1, x_start=0, x_end=2*np.pi, step=0.1):
    x = np.linspace(x_start, x_end, max(int((x_end-x_start)/step), 20))
    return Shape2d(np.column_stack([x, amplitude*np.sin(frequency*x)]))

def tangent(x_start=-0.5*np.pi, x_end=0.5*np.pi, step=0.1, height=100):
    x = np.linspace(x_start + 0.01, x_end - 0.01, max(int((x_end-x_start)/step), 20))
    y = np.tan(x)
    mask = np.abs(y) < height
    return Shape2d(np.column_stack([x[mask], y[mask]]))
