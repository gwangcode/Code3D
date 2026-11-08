import pytest
import FreeCAD
import Part
import numpy as np
from utils import _is_vec, _vec, _tessellate, _tri_mesh_to_shape, extremes, show

@pytest.fixture(autouse=True)
def setup_freecad_doc():
    """为每个测试用例创建和销毁 FreeCAD 文档，避免状态污染"""
    doc_name = "TestUtils_Doc"
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
    FreeCAD.newDocument(doc_name)
    FreeCAD.setActiveDocument(doc_name)
    yield
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(doc_name)

# ==========================================
# 1. 向量处理测试
# ==========================================
def test_is_vec_and_vec():
    """测试 _is_vec 对多种类型的兼容性，以及 _vec 的转换"""
    # 测试长度匹配的情况 (n=3)
    assert _is_vec(FreeCAD.Vector(1, 2, 3), 3) is True
    assert _is_vec([1.0, 2.0, 3.0], 3) is True
    assert _is_vec((1, 2, 3), 3) is True
    assert _is_vec(np.array([1.0, 2.0, 3.0]), 3) is True

    # 测试长度不匹配的情况
    assert _is_vec(FreeCAD.Vector(1, 2, 3), 2) is False
    assert _is_vec([1.0, 2.0], 3) is False
    
    # 测试非法输入
    assert _is_vec("not_a_vector", 3) is False
    assert _is_vec(None, 3) is False

    # 测试 _vec 转换
    result = _vec([1, 2, 3])
    assert isinstance(result, tuple)
    assert result == (1.0, 2.0, 3.0)
    assert all(isinstance(v, float) for v in result)


# ==========================================
# 2. 包围盒极值测试
# ==========================================
def test_extremes():
    """测试 extremes 能否正确返回六个边界极值"""
    # 创建一个尺寸为 10 x 20 x 30 的长方体
    box = Part.makeBox(10, 20, 30)
    
    # 获取极值
    res = extremes(box)
    
    # 预期结果 (XMin, XMax, YMin, YMax, ZMin, ZMax)
    expected = (0.0, 10.0, 0.0, 20.0, 0.0, 30.0)
    
    # 使用 pytest.approx 处理可能的浮点误差
    assert res == pytest.approx(expected)


# ==========================================
# 3. 网格离散化与重建测试
# ==========================================
def test_tessellate_and_rebuild():
    """测试 _tessellate (离散化) 和 _tri_mesh_to_shape (转回B-Rep)"""
    # 1. 创建一个球体进行离散化
    sphere = Part.makeSphere(10.0)
    
    # 2. 离散化为网格 (verts: numpy array, faces: list of tuples)
    verts, faces = _tessellate(sphere, tol=1.0)
    
    # 验证离散化结果不为空
    assert verts.size > 0
    assert len(faces) > 0
    assert verts.shape[1] == 3 # 确保是 3D 坐标
    
    # 3. 将网格重新转回 Shape
    new_shape = _tri_mesh_to_shape(verts, faces, name="Rebuilt_Sphere")
    
    # 验证结果有效性
    assert new_shape.isValid()
    # 由于离散化是由三角面拼成的近似，类型可能是 Solid 或 Shell
    assert new_shape.ShapeType in ("Solid", "Shell", "Compound")
    # 验证生成的包围盒尺寸大致接近原来的球体（直径 20）
    bb = new_shape.BoundBox
    assert bb.XLength == pytest.approx(20.0, abs=1.0)


def test_tessellate_invalid_input():
    """测试 _tessellate 对非 Shape 输入的处理"""
    verts, faces = _tessellate(123.45)
    assert verts.size == 0
    assert faces == []


# ==========================================
# 4. 显示函数测试
# ==========================================
def test_show_function():
    """测试 show 函数能否在文档中正确创建对象"""
    box = Part.makeBox(10, 10, 10)
    obj = show(box, name="My_Box")
    
    # 验证文档中存在该对象
    doc = FreeCAD.ActiveDocument
    assert obj is not None
    assert doc.getObject("My_Box") is not None
    
    # 验证对象的 Shape 是否正确赋值
    assert obj.Shape.isValid()
    assert obj.Shape.Volume == pytest.approx(1000.0)
