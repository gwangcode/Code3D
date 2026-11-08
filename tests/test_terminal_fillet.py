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

@patch('FreeCADGui.Selection.getSelectionEx')
def test_selection_proxy(mock_get_selection):
    """测试 _ & 1 是否成功抓取选中的几何体并做圆角"""
    box = Part.makeBox(10, 10, 10)
    mock_obj = MagicMock()
    mock_obj.Object.Shape = box
    mock_obj.SubObjects = [] 
    
    mock_get_selection.return_value = [mock_obj]
    
    # 【修复】传入一个模拟的 terminal 对象
    mock_terminal = MagicMock()
    proxy = SelectionProxy(mock_terminal)
    
    # 1. 测试圆角
    fillet_result = proxy & 2.0
    assert fillet_result.isValid()
    
    # 2. 测试倒角
    chamfer_result = proxy & -2.0
    assert chamfer_result.isValid()
    
    # 3. 测试错误输入
    with pytest.raises(ValueError, match="Unsupported operand"):
        proxy & "string"

@patch('FreeCADGui.Selection.getSelectionEx')
def test_selection_proxy_specific_edges(mock_get_selection):
    """测试 _ & 1 选中了特定的边"""
    box = Part.makeBox(10, 10, 10)
    
    mock_obj = MagicMock()
    mock_obj.Object.Shape = box
    
    mock_edge = box.Edges[0]
    mock_obj.SubObjects = [mock_edge]
    
    mock_get_selection.return_value = [mock_obj]
    
    mock_terminal = MagicMock()
    proxy = SelectionProxy(mock_terminal)
    
    result = proxy & 2.0
    assert result.isValid()

@patch('FreeCADGui.Selection.getSelectionEx')
def test_terminal_execute_proxy(mock_get_selection):
    """测试终端内的执行逻辑 (eval 模式)"""
    doc = FreeCAD.ActiveDocument
    
    box = Part.makeBox(10, 10, 10)
    obj = doc.addObject("Part::Feature", "TestBox")
    obj.Shape = box
    
    mock_sel = MagicMock()
    mock_sel.Object = obj
    mock_sel.SubObjects = []
    mock_get_selection.return_value = [mock_sel]
    
    term = PythonTerminal()
    
    # 模拟终端里的 `_ & 1` 命令
    term.execute_code("_ & 2.0")
    
    # 【修复】现在会生成带有父子关系的 Fillet 节点，而不是 model_1
    fillet_node = doc.getObject("Fillet")
    assert fillet_node is not None
    assert fillet_node.Shape.isValid()
