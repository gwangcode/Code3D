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
# 1. 2D 基础函数测试 (确保数学计算不报错)
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

    # 验证生成的 Shape2d 具有正确的点维度
    # 假设 Shape2d 对象包含 points 属性或类似接口，这里用 np.array 转换测试
    # 如果 Shape2d 没有直接暴露 points，可以跳过这点，只校验对象类型


# ==========================================
# 2. 自由 2D 曲线生成测试 (假设你添加了 free_curve)
# ==========================================
def test_free_curve():
    """测试自定义的自由曲线函数"""
    # 生成一条经过 4 个点的平滑开放曲线
    pts = [(0, 0, 0), (2, 5, 0), (6, 2, 0), (10, 8, 0)]
    curve = primitives.free_curve(pts, closed=False)
    
    assert isinstance(curve, Shape)
    assert curve.Shape.ShapeType == "Wire"
    assert curve.Shape.isValid()

    # 生成一条自动闭合的曲线
    closed_curve = primitives.free_curve(pts, closed=True)
    assert closed_curve.Shape.ShapeType == "Wire"
    # 闭合的 wire 应该拥有 isClosed 为 True
    assert closed_curve.Shape.isClosed()


# ==========================================
# 3. B-Spline 曲面生成测试 (1D 和 2D)
# ==========================================
def test_bspline_surface_1d():
    """测试 1D 点集生成 B-Spline 面/线"""
    pts = [(0,0,0), (10,0,0), (15,10,0), (10,20,0), (0,20,0), (-5,10,0)]
    
    # 调用 primitives 中的 bspline_surface
    result = primitives.bspline_surface(pts)
    
    assert isinstance(result, Shape)
    # 这些共面的点会被填充为面
    assert result.Shape.ShapeType == "Face"
    assert result.Shape.isValid()


def test_bspline_surface_2d():
    """测试 2D 点阵生成 B-Spline 曲面"""
    pts_2d = [
        [(0,0,0), (5,0,2), (10,0,0)],
        [(0,5,2), (5,5,5), (10,5,2)],
        [(0,10,0), (5,10,2), (10,10,0)]
    ]
    
    result = primitives.bspline_surface(pts_2d)
    
    assert isinstance(result, Shape)
    assert result.Shape.ShapeType == "Face"
    assert result.Shape.isValid()


# ==========================================
# 4. smooth_body 稳健性测试 (防止回归)
# ==========================================
def test_smooth_body_coplanar():
    """测试共面点集回退为 Face 逻辑"""
    pts = [(0,0,0), (10,0,0), (15,10,0), (10,20,0), (0,20,0), (-5,10,0)]
    result = primitives.smooth_body(pts)
    
    assert isinstance(result, Shape)
    assert result.Shape.ShapeType == "Face"
    assert result.Shape.isValid()


def test_smooth_body_sparse_points():
    """测试非共面稀疏点集生成有效的 Solid"""
    pts = [(0,0,0), (10,0,5), (15,10,-2), (10,20,8), (0,20,0), (-5,10,5)]
    result = primitives.smooth_body(pts, iterations=2)
    
    assert isinstance(result, Shape)
    # 可能是 Solid 或 CompSolid
    assert result.Shape.ShapeType in ("Solid", "CompSolid")
    assert result.Shape.isValid()
    assert result.Shape.Volume > 0
    assert result.Shape.isClosed()


def test_smooth_body_insufficient_points():
    """测试点数不足时是否抛出预期的 ValueError"""
    with pytest.raises(ValueError, match="At least 4 points are required"):
        primitives.smooth_body([(0,0,0), (10,0,0), (0,10,0)])
