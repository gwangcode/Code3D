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
    from unittest.mock import MagicMock
    
    fake_shape = MagicMock()
    
    edge1 = MagicMock()
    edge1.CenterOfMass = FreeCAD.Vector(0, 0, 0)
    edge2 = MagicMock()
    edge2.CenterOfMass = FreeCAD.Vector(0, 0, 10)
    
    fake_shape.Edges = [edge1, edge2]
    
    # 测试单边圆角
    apply_fillet_chamfer(fake_shape, radius=2.0, selected_edges=[edge1])
    # 【修复】断言传入的第二个参数是 [edge1]，而不是 [0]
    fake_shape.makeFillet.assert_called_once_with(2.0, [edge1])
    
    fake_shape.makeFillet.reset_mock()
    fake_shape.makeChamfer.reset_mock()
    
    # 测试单边倒角
    apply_fillet_chamfer(fake_shape, radius=-2.0, selected_edges=[edge2])
    fake_shape.makeChamfer.assert_called_once_with(2.0, [edge2])
    
    fake_shape.makeFillet.reset_mock()
    fake_shape.makeChamfer.reset_mock()
    
    # 测试全边圆角
    apply_fillet_chamfer(fake_shape, radius=1.5)
    fake_shape.makeFillet.assert_called_once_with(1.5, [edge1, edge2])
