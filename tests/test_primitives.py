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
    doc_name = "TestCI_Doc"
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
    FreeCAD.newDocument(doc_name)
    FreeCAD.setActiveDocument(doc_name)
    yield
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(doc_name)

# ... (你原有的点、线、2D、曲面、smooth_body 测试都保留，这里省略以节省篇幅) ...
# 请保留你之前的 test_point_and_points 到 test_smooth_body_insufficient_points

# ==========================================
# 6. 测试 & 运算符 (Fillet / Chamfer)
# ==========================================
def test_fillet_chamfer_3d_operator():
    """测试 3D 实体通过 & 运算符进行圆角/倒角"""
    box = primitives.cube(10)
    
    # 圆角
    fillet_box = box & 2.0
    assert fillet_box.isValid()
    # 圆角后由于切角，面数一定会增加（原为6个面）
    assert len(fillet_box.Faces) > 6
    
    # 倒角
    chamfer_box = box & -2.0
    assert chamfer_box.isValid()

def test_fillet_chamfer_2d_operator():
    """测试 2D 图形通过 & 运算符进行圆角"""
    poly = primitives.hexagon(10)
    
    # 2D 圆角操作会自动转为 3D 面返回
    fillet_face = poly & 1.0
    assert fillet_face.isValid()
    assert fillet_face.ShapeType == "Face"
