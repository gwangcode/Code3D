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

def test_point_and_points():
    pt = primitives.point(1.0, 2.0, 3.0)
    assert pt.ShapeType == "Vertex"
    assert pt.isValid()

    pts_list = [(0,0,0), (10,10,10), (-5,5,-5)]
    pts_cloud = primitives.points(pts_list)
    assert pts_cloud.ShapeType == "Compound"
    assert pts_cloud.isValid()

def test_line():
    l1 = primitives.line((0, 0), (10, 10))
    assert l1.ShapeType == "Wire"
    assert l1.isValid()

def test_2d_primitives():
    shape_circle = primitives.circle(R=5)
    assert isinstance(shape_circle, Shape)
    assert shape_circle.ShapeType == "Face"
    assert shape_circle.isValid()

    shape_poly = primitives.polygon(R=10, n=6)
    assert isinstance(shape_poly, Shape2d)

# 【修复】使用不自相交的点测试 free_curve
def test_free_curve():
    # 矩形边界（不会自相交）
    pts = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)]
    
    # 1. 测试默认参数 (closed=True, make_face=True) -> 应该生成 Face
    default_curve = primitives.free_curve(pts)
    assert default_curve.ShapeType == "Face"
    assert default_curve.isValid()

    # 2. 测试显式传入 False -> 应该生成 Wire
    open_curve = primitives.free_curve(pts, closed=False, make_face=False)
    assert open_curve.ShapeType == "Wire"
    assert open_curve.isValid()

    # 3. 测试闭合但不生成面 -> 应该生成 Wire (闭环)
    closed_wire = primitives.free_curve(pts, closed=True, make_face=False)
    assert closed_wire.ShapeType == "Wire"
    assert closed_wire.isClosed()

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

def test_convex_hull_degenerate():
    collinear_pts = [(0,0,0), (1,0,0), (2,0,0), (3,0,0)]
    result = primitives.convex_hull(collinear_pts)
    assert result.ShapeType in ("Wire", "Vertex")
    assert result.isValid()

def test_convex_hull_normal():
    pts = [(0,0,0), (10,0,0), (0,10,0), (0,0,10), (10,10,10)]
    result = primitives.convex_hull(pts)
    assert result.ShapeType == "Solid"
    assert result.Volume > 0
