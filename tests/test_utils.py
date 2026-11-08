import pytest
import FreeCAD
import Part
import numpy as np
from unittest.mock import MagicMock

from utils import show, sketch
from mod3d.utils import _is_vec, _vec, _tessellate, _tri_mesh_to_shape, extremes, apply_fillet_chamfer

@pytest.fixture(autouse=True)
def setup_freecad_doc():
    doc_name = "TestUtils_Doc"
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
    FreeCAD.newDocument(doc_name)
    FreeCAD.setActiveDocument(doc_name)
    yield
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(doc_name)

def test_is_vec_and_vec():
    assert _is_vec(FreeCAD.Vector(1, 2, 3), 3) is True
    assert _is_vec([1.0, 2.0, 3.0], 3) is True
    assert _is_vec((1, 2, 3), 3) is True
    assert _is_vec(np.array([1.0, 2.0, 3.0]), 3) is True
    assert _is_vec(FreeCAD.Vector(1, 2, 3), 2) is False
    assert _is_vec([1.0, 2.0], 3) is False
    assert _is_vec("not_a_vector", 3) is False
    assert _is_vec(None, 3) is False

    result = _vec([1, 2, 3])
    assert isinstance(result, tuple)
    assert result == (1.0, 2.0, 3.0)
    assert all(isinstance(v, float) for v in result)

def test_extremes():
    box = Part.makeBox(10, 20, 30)
    res = extremes(box)
    expected = (0.0, 10.0, 0.0, 20.0, 0.0, 30.0)
    assert res == pytest.approx(expected)

def test_tessellate_and_rebuild():
    sphere = Part.makeSphere(10.0)
    verts, faces = _tessellate(sphere, tol=1.0)
    assert verts.size > 0
    assert len(faces) > 0
    
    new_shape = _tri_mesh_to_shape(verts, faces, name="Rebuilt_Sphere")
    assert new_shape.isValid()
    assert new_shape.ShapeType in ("Solid", "Shell", "Compound")
    bb = new_shape.BoundBox
    assert bb.XLength == pytest.approx(20.0, abs=1.0)

def test_show_function():
    box = Part.makeBox(10, 10, 10)
    obj = show(box, name="My_Box")
    doc = FreeCAD.ActiveDocument
    assert obj is not None
    assert doc.getObject("My_Box") is not None
    assert obj.Shape.isValid()

def test_sketch():
    face = Part.makePlane(10, 10)
    sk = sketch(face, "Sketch_1")
    assert sk is not None
    assert sk.TypeId == "Sketcher::SketchObject"
    assert sk.Name == "Sketch_1"
    if FreeCAD.GuiUp:
        assert len(sk.Geometry) > 0

def test_apply_fillet_chamfer():
    """
    【核心修复】使用纯 Mock 对象来测试 apply_fillet_chamfer 的逻辑。
    绕过 OCC 引擎在无头环境下的静默失败，以及 C++ 对象的只读限制。
    """
    from unittest.mock import MagicMock
    
    # 1. 构造一个假的 Shape 对象
    fake_shape = MagicMock()
    
    # 2. 构造几条假的边
    edge1 = MagicMock()
    edge1.CenterOfMass = FreeCAD.Vector(0, 0, 0)
    edge2 = MagicMock()
    edge2.CenterOfMass = FreeCAD.Vector(0, 0, 10)
    
    # 让 shape.Edges 返回这两条边
    fake_shape.Edges = [edge1, edge2]
    
    # 3. 测试单边圆角
    apply_fillet_chamfer(fake_shape, radius=2.0, selected_edges=[edge1])
    # 断言底层调用了 makeFillet，半径 2.0，且只选中了第 0 条边
    fake_shape.makeFillet.assert_called_once_with(2.0, [0])
    
    # 重置 Mock
    fake_shape.makeFillet.reset_mock()
    fake_shape.makeChamfer.reset_mock()
    
    # 4. 测试单边倒角 (radius < 0)
    apply_fillet_chamfer(fake_shape, radius=-2.0, selected_edges=[edge2])
    # 断言底层调用了 makeChamfer，距离 2.0，且选中了第 1 条边
    fake_shape.makeChamfer.assert_called_once_with(2.0, [1])
    
    # 重置 Mock
    fake_shape.makeFillet.reset_mock()
    fake_shape.makeChamfer.reset_mock()
    
    # 5. 测试全边圆角
    apply_fillet_chamfer(fake_shape, radius=1.5)
    # 断言底层调用了 makeFillet，半径 1.5，且传入了所有边 [0, 1]
    fake_shape.makeFillet.assert_called_once_with(1.5, [0, 1])
