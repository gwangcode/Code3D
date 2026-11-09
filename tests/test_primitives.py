import pytest
import FreeCAD
import Part
import numpy as np
from mod3d import primitives
from mod3d.patch import Shape
from mod3d.shapes import Shape2d

@pytest.fixture(autouse=True)
def setup_freecad_doc():
    doc_name = "TestCI_Doc"
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
    FreeCAD.newDocument(doc_name)
    FreeCAD.setActiveDocument(doc_name)
    yield
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(doc_name)

# ==========================================
# 1. 基础点与线生成测试
# ==========================================
def test_point_and_points():
    pt = primitives.point(1.0, 2.0, 3.0)
    assert pt.ShapeType == "Vertex"
    assert pt.isValid()
    assert pt.X == 1.0

    pts_list = [(0,0,0), (10,10,10), (-5,5,-5)]
    pts_cloud = primitives.points(pts_list)
    assert pts_cloud.ShapeType == "Compound"
    assert pts_cloud.isValid()

def test_line():
    l1 = primitives.line((0, 0), (10, 10))
    assert l1.ShapeType == "Wire"
    assert l1.isValid()
    
    l2 = primitives.line((0, 0, 0), (10, 10, 10))
    assert l2.ShapeType == "Wire"
    assert l2.isValid()

# ==========================================
# 2. 2D 基础函数测试 (注意 circle 现在是 Shape)
# ==========================================
def test_2d_primitives():
    # 【修复】circle 现在返回完美的 B-Rep Face，不再是 Shape2d
    shape_circle = primitives.circle(R=5)
    assert isinstance(shape_circle, Shape)
    assert shape_circle.ShapeType == "Face"
    assert shape_circle.isValid()

    shape_poly = primitives.polygon(R=10, n=6)
    assert isinstance(shape_poly, Shape2d)

    shape_ellipse = primitives.ellipse(a=5, b=2)
    assert isinstance(shape_ellipse, Shape2d)

# ==========================================
# 3. 自由曲线测试
# ==========================================
def test_free_curve():
    pts = [(0, 0, 0), (2, 5, 0), (6, 2, 0), (10, 8, 0)]
    
    # 默认参数现在恢复为 closed=False, make_face=False
    curve = primitives.free_curve(pts)
    assert curve.ShapeType == "Wire"
    assert curve.isValid()

    closed_curve = primitives.free_curve(pts, closed=True, make_face=True)
    assert closed_curve.ShapeType == "Face"
    assert closed_curve.isValid()

# ==========================================
# 4. B-Spline 与 smooth_body 测试
# ==========================================
def test_bspline_surface_1d():
    pts = [(0,0,0), (10,0,0), (15,10,0), (10,20,0), (0,20,0), (-5,10,0)]
    result = primitives.bspline_surface(pts)
    assert result.ShapeType == "Face"
    assert result.isValid()

def test_smooth_body_sparse_points():
    pts = [(0,0,0), (10,0,5), (15,10,-2), (10,20,8), (0,20,0), (-5,10,5)]
    result = primitives.smooth_body(pts, iterations=2)
    assert result.ShapeType in ("Solid", "CompSolid")
    assert result.isValid()
    assert result.Volume > 0
    assert result.isClosed()

# ==========================================
# 5. 测试 convex_hull 的共线降级处理
# ==========================================
def test_convex_hull_degenerate():
    """测试共线点是否能优雅降级为 Wire，而不是让程序崩溃"""
    collinear_pts = [(0,0,0), (1,0,0), (2,0,0), (3,0,0)]
    result = primitives.convex_hull(collinear_pts)
    # 因为我们加了 try-except 保护，它应该返回原点的连线
    assert result.ShapeType in ("Wire", "Vertex")
    assert result.isValid()

def test_convex_hull_normal():
    """测试正常的点生成 Solid"""
    pts = [(0,0,0), (10,0,0), (0,10,0), (0,0,10), (10,10,10)]
    result = primitives.convex_hull(pts)
    assert result.ShapeType == "Solid"
    assert result.Volume > 0
