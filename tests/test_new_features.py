import pytest
import sys
import os
import types
from unittest.mock import MagicMock, patch
import numpy as np

def add_freecad_to_path():
    if 'CONDA_PREFIX' in os.environ:
        prefix = os.environ['CONDA_PREFIX']
        for p in [os.path.join(prefix, 'lib', 'freecad', 'lib'), os.path.join(prefix, 'Library', 'lib'), os.path.join(prefix, 'lib')]:
            if os.path.exists(p) and p not in sys.path: sys.path.append(p)
    if sys.platform == 'win32':
        import glob
        for p in glob.glob(r"C:\Program Files\FreeCAD*\bin"):
            if p not in sys.path: sys.path.append(p)

add_freecad_to_path()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class DummyQPlainTextEdit:
    NoWrap = 0
    def __init__(self, *args, **kwargs): pass
    def setStyleSheet(self, *args, **kwargs): pass
    def insertPlainText(self, *args, **kwargs): pass
    def moveCursor(self, *args, **kwargs): pass
    def textCursor(self): return MagicMock()
    def setLineWrapMode(self, mode): pass

fake_pyside = types.ModuleType("PySide6")
fake_qtcore = types.ModuleType("PySide6.QtCore")
fake_qtgui = types.ModuleType("PySide6.QtGui")
fake_qtwidgets = types.ModuleType("PySide6.QtWidgets")
fake_qtwidgets.QPlainTextEdit = DummyQPlainTextEdit
fake_qtwidgets.QApplication = MagicMock()
fake_qtcore.Qt = MagicMock()
fake_qtcore.QTimer = MagicMock()
fake_qtgui.QTextCursor = MagicMock()

sys.modules.update({'PySide6': fake_pyside, 'PySide6.QtCore': fake_qtcore, 'PySide6.QtGui': fake_qtgui, 'PySide6.QtWidgets': fake_qtwidgets})

if 'terminal' in sys.modules: del sys.modules['terminal']

import FreeCAD
import Part
import mod3d
import terminal
from terminal import PythonTerminal

@pytest.fixture
def term():
    doc = FreeCAD.newDocument("TestDoc")
    FreeCAD.setActiveDocument("TestDoc")
    term = PythonTerminal()
    terminal.QtCore.QTimer.singleShot = lambda ms, func: func()
    yield term
    FreeCAD.closeDocument("TestDoc")

# ==========================================
# 测试 runf 脚本执行
# ==========================================
def test_runf(term, tmp_path):
    term.write = MagicMock()
    
    # 【核心修复】把终端环境里的 show 替换成 Mock 函数
    mock_show = MagicMock()
    term.local_vars["show"] = mock_show
    
    script_file = tmp_path / "my_script.py"
    script_content = "a = cube(10)\nshow(a, 'TestBox')\n"
    script_file.write_text(script_content)
    
    term.execute_code(f'runf(r"{script_file}")')
    
    # 断言没有打印报错
    assert term.write.call_count == 0, f"脚本执行报错: {term.write.call_args}"
    
    # 断言 show 函数被成功调用，且名字是 TestBox
    mock_show.assert_called_once()
    args, kwargs = mock_show.call_args
    assert args[1] == 'TestBox', "show 函数收到的名字不是 TestBox"

# ... (保留其他的测试：test_bspline_surface_1d, test_bspline_surface_2d, test_2d_shape_display, test_clear_command, test_copy_selected_logic) ...
