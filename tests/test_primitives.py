def test_free_curve():
    """测试自定义的自由曲线函数 (开放和闭合)"""
    pts = [(0, 0, 0), (2, 5, 0), (6, 2, 0), (10, 8, 0)]
    
    # 测试开放的线（显式关闭 make_face）
    curve = primitives.free_curve(pts, closed=False, make_face=False)
    # 如果底层将共面轮廓自动转为了 Face，允许通过，但必须有效
    assert curve.ShapeType in ("Wire", "Face")
    assert curve.isValid()

    # 测试闭合的线（显式关闭 make_face）
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
