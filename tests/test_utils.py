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
    【核心修复】因为 OCC 引擎在无头环境中执行 makeFillet 极易静默失败，
    我们使用 Mock 技术替换底层的几何运算，纯粹测试我们的业务逻辑（索引匹配与方法调用）。
    """
    box = Part.makeBox(10, 10, 10)
    selected_edges = [box.Edges[0]]
    
    # 拦截底层调用
    mock_fillet = MagicMock(return_value=box)
    mock_chamfer = MagicMock(return_value=box)
    box.makeFillet = mock_fillet
    box.makeChamfer = mock_chamfer
    
    # 1. 测试圆角 (radius > 0)
    apply_fillet_chamfer(box, radius=2.0, selected_edges=selected_edges)
    # 断言 makeFillet 被调用了一次，且传入了正确的半径和提取出的边索引 [0]
    mock_fillet.assert_called_once_with(2.0, [0])
    
    # 2. 测试倒角 (radius < 0)
    apply_fillet_chamfer(box, radius=-2.0, selected_edges=selected_edges)
    # 断言 makeChamfer 被调用了一次，且距离为 2.0
    mock_chamfer.assert_called_once_with(2.0, [0])

    # 3. 测试全边倒角
    apply_fillet_chamfer(box, radius=-1.5)
    # box 有 12 条边，所以应该传入长度为 12 的索引列表
    args, kwargs = mock_chamfer.call_args
    assert len(args[1]) == 12
