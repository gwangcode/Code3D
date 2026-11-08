# ... (保留你原有的代码) ...

# ==========================================
# 6. 测试 & 运算符 (Fillet / Chamfer)
# ==========================================
def test_fillet_chamfer_3d_operator():
    """测试 3D 实体通过 & 运算符进行圆角/倒角"""
    box = primitives.cube(10)
    
    # 圆角
    fillet_box = box & 2.0
    assert fillet_box.Shape.isValid()
    assert len(fillet_box.Shape.Edges) > 12
    
    # 倒角
    chamfer_box = box & -2.0
    assert chamfer_box.Shape.isValid()

def test_fillet_chamfer_2d_operator():
    """测试 2D 图形通过 & 运算符进行圆角"""
    poly = primitives.hexagon(10)
    
    # 2D 圆角操作会自动转为 3D 面返回
    fillet_face = poly & 1.0
    assert fillet_face.Shape.isValid()
    assert fillet_face.Shape.ShapeType == "Face"
