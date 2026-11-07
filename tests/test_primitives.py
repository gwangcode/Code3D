import pytest
import FreeCAD
import Part
import numpy as np
from mod3d import primitives
from mod3d.patch import Shape
from mod3d.shapes import Shape2d

# ==========================================
# 通用的 fixture：管理 FreeCAD 文档
# ==========================================
@pytest.fixture(autouse=True)
def setup_freecad_doc():
    """为每个测试用例创建和销毁 FreeCAD 文档，避免状态污染"""
    doc_name = "TestCI_Doc"
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
    FreeCAD.newDocument(doc_name)
    FreeCAD.setActiveDocument(doc_name)
    yield
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(doc_name)

# ==========================================
# 1. 基础点生成测试 (新增)
# ==========================================
def test_point_and_points():
    """测试单点生成与点云集合生成"""
    # 测试单个点
    pt = primitives.point(1.0, 2.0, 3.0)
    assert pt.ShapeType == "Vertex"
    assert pt.isValid()
    assert pt.X == 1.0
    assert pt.Y == 2.0
    assert pt.Z == 3.0

    # 测试多点集合
    pts_list = [(0,0,0), (10,10,10), (-5,5,-5)]
    pts_cloud = primitives.points(pts_list)
    assert pts_cloud.ShapeType == "Compound"
    assert pts_cloud.isValid()


# ==========================================
# 2. 2D 基础函数测试 (确保数学计算不报错)
# ==========================================
def test_2d_primitives():
    """测试所有 2D 曲线和多边形函数，确保它们能正确生成 Shape2d 对象"""
    shape_circle = primitives.circle(R=5)
    assert isinstance(shape_circle, Shape2d)

    shape_poly = primitives.polygon(R=10, n=6)
    assert isinstance(shape_poly, Shape2d)

    shape_ellipse = primitives.ellipse(a=5, b=2)
    assert isinstance(shape_ellipse, Shape2d)

    shape_sine = primitives.sine(amplitude=2, frequency=1)
    assert isinstance(shape_sine, Shape2d)

    shape_spiral = primitives.spiral(a=1, b=1, num_turns=3)
    assert isinstance(shape_spiral, Shape2d)


# ==========================================
# 3. 自由曲线与生成面测试 (更新)
# ==========================================
def test_free_curve():
    """测试自定义的自由曲线函数 (开放和闭合)"""
    pts = [(0, 0, 0), (2, 5, 0), (6, 2, 0), (10, 8, 0)]
    
    # 测试开放的线
    curve = primitives.free_curve(pts, closed=False, make_face=False)
    # 兼容底层可能因为共面而自动转为 Face 的情况
    assert curve.ShapeType in ("Wire", "Face")
    assert curve.isValid()

    # 测试闭合的线
    closed_curve = primitives.free_curve(pts, closed=True, make_face=False)
    assert closed_curve.ShapeType in ("Wire", "Face")
    # 不管返回哪种类型，既然要求闭合，它就必须是闭合的拓扑
    assert closed_curve.isClosed()


def test_free_curve_make_face():
    """测试 free_curve 直接生成面 (make_face=True)"""
    pts = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)]
    
    # 1. 闭合曲线生成面
    face_closed = primitives.free_curve(pts, closed=True, make_face=True)
    assert face_closed.ShapeType == "Face"
    assert face_closed.isValid()
    
    # 2. 开放曲线强制生成面 (内部自动加一根线闭合)
    face_open = primitives.free_curve(pts, closed=False, make_face=True)
    assert face_open.ShapeType == "Face"
    assert face_open.isValid()


# ==========================================
# 4. B-Spline 曲面生成测试 (1D 和 2D)
# ==========================================
def test_bspline_surface_1d():
    """测试 1D 点集生成 B-Spline 面/线"""
    pts = [(0,0,0), (10,0,0), (15,10,0), (10,20,0), (0,20,0), (-5,10,0)]
    result = primitives.bspline_surface(pts)
    
    assert result.ShapeType == "Face"
    assert result.isValid()


def test_bspline_surface_2d():
    """测试 2D 点阵生成 B-Spline 曲面"""
    pts_2d = [
        [(0,0,0), (5,0,2), (10,0,0)],
        [(0,5,2), (5,5,5), (10,5,2)],
        [(0,10,0), (5,10,2), (10,10,0)]
    ]
    result = primitives.bspline_surface(pts_2d)
    
    assert result.ShapeType == "Face"
    assert result.isValid()


# ==========================================
# 5. smooth_body 稳健性测试 (防止回归)
# ==========================================
def test_smooth_body_coplanar():
    """测试共面点集回退为 Face 逻辑"""
    pts = [(0,0,0), (10,0,0), (15,10,0), (10,20,0), (0,20,0), (-5,10,0)]
    result = primitives.smooth_body(pts)
    
    assert result.ShapeType == "Face"
    assert result.isValid()


def test_smooth_body_sparse_points():
    """测试非共面稀疏点集生成有效的 Solid"""
    pts = [(0,0,0), (10,0,5), (15,10,-2), (10,20,8), (0,20,0), (-5,10,5)]
    result = primitives.smooth_body(pts, iterations=2)
    
    assert result.ShapeType in ("Solid", "CompSolid")
    assert result.isValid()
    assert result.Volume > 0
    assert result.isClosed()


def test_smooth_body_insufficient_points():
    """测试点数不足时是否抛出预期的 ValueError"""
    with pytest.raises(ValueError, match="At least 4 points are required"):
        primitives.smooth_body([(0,0,0), (10,0,0), (0,10,0)])
