import pytest
import FreeCAD
import Part
from unittest.mock import MagicMock, patch
from terminal import PythonTerminal, SelectionProxy

@pytest.fixture(autouse=True)
def setup_freecad_doc():
    doc_name = "TestTerminalFillet"
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
    FreeCAD.newDocument(doc_name)
    FreeCAD.setActiveDocument(doc_name)
    yield
    if FreeCAD.ActiveDocument:
        FreeCAD.closeDocument(doc_name)

# ==========================================
# 1. 测试 SelectionProxy 代理逻辑
# ==========================================
@patch('FreeCADGui.Selection.getSelectionEx')
def test_selection_proxy(mock_get_selection):
    """测试 _ & 1 是否成功抓取选中的几何体并做圆角"""
    # 构建一个假的选择对象
    box = Part.makeBox(10, 10, 10)
    mock_obj = MagicMock()
    mock_obj.Object.Shape = box
    mock_obj.SubObjects = [] # 模拟选中了整个模型
    
    mock_get_selection.return_value = [mock_obj]
    
    proxy = SelectionProxy()
    
    # 1. 测试圆角
    fillet_result = proxy & 2.0
    assert fillet_result.Shape.isValid()
    assert len(fillet_result.Shape.Edges) > 12
    
    # 2. 测试倒角
    chamfer_result = proxy & -2.0
    assert chamfer_result.Shape.isValid()
    
    # 3. 测试错误输入
    with pytest.raises(ValueError, match="Unsupported operand"):
        proxy & "string"

@patch('FreeCADGui.Selection.getSelectionEx')
def test_selection_proxy_specific_edges(mock_get_selection):
    """测试 _ & 1 选中了特定的边"""
    box = Part.makeBox(10, 10, 10)
    
    # 构造一个选了特定 edge 的 Mock
    mock_obj = MagicMock()
    mock_obj.Object.Shape = box
    
    # 模拟选中了第一条边
    mock_edge = box.Edges[0]
    mock_edge.ShapeType = "Edge"
    mock_obj.SubObjects = [mock_edge]
    
    mock_get_selection.return_value = [mock_obj]
    
    proxy = SelectionProxy()
    result = proxy & 2.0
    
    assert result.Shape.isValid()
    # 局部圆角通常不会增加太多面，此处只要断言有效即可


# ==========================================
# 2. 测试终端环境下直接输入 `_ & 1`
# ==========================================
@patch('FreeCADGui.Selection.getSelectionEx')
def test_terminal_execute_proxy(mock_get_selection):
    """测试终端内的执行逻辑 (eval 模式)"""
    doc = FreeCAD.ActiveDocument
    
    box = Part.makeBox(10, 10, 10)
    obj = doc.addObject("Part::Feature", "TestBox")
    obj.Shape = box
    
    # 模拟选中
    mock_sel = MagicMock()
    mock_sel.Object = obj
    mock_sel.SubObjects = []
    mock_get_selection.return_value = [mock_sel]
    
    term = PythonTerminal()
    
    # 模拟终端里的 `_ & 1` 命令
    term.execute_code("_ & 2.0")
    
    # 验证是否生成了新的 model 对象
    model_1 = doc.getObject("model_1")
    assert model_1 is not None
    assert model_1.Shape.isValid()
