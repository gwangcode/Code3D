import pytest
import FreeCAD
import Part
import numpy as np

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
    box = Part.makeBox(10, 10, 10)
    
    # 1. 测试圆角 (radius > 0)
    fillet_shape = apply_fillet_chamfer(box, radius=2.0)
    assert fillet_shape.isValid()
    # 【修复】圆角后，原来的 6 个平面的角被切掉，面数必然会增加
    assert len(fillet_shape.Faces) > 6
    
    # 2. 测试倒角 (radius < 0)
    chamfer_shape = apply_fillet_chamfer(box, radius=-2.0)
    assert chamfer_shape.isValid()
    assert len(chamfer_shape.Faces) > 6
    
    # 3. 测试只处理特定边
    selected_edges = [box.Edges[0], box.Edges[1]]
    partial_fillet = apply_fillet_chamfer(box, radius=2.0, selected_edges=selected_edges)
    assert partial_fillet.isValid()
