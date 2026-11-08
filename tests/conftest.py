import pytest
import sys
import os
import types
from unittest.mock import MagicMock
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
    def setTextCursor(self, cursor): pass
    def setLineWrapMode(self, mode): pass
    def toPlainText(self): return ""  # 必须存在：用于获取全文判断光标位置
    def clear(self): pass

fake_pyside = types.ModuleType("PySide6")
fake_qtcore = types.ModuleType("PySide6.QtCore")
fake_qtgui = types.ModuleType("PySide6.QtGui")
fake_qtwidgets = types.ModuleType("PySide6.QtWidgets")
fake_qtwidgets.QPlainTextEdit = DummyQPlainTextEdit
fake_qtwidgets.QApplication = MagicMock()
fake_qtcore.Qt = MagicMock()
fake_qtcore.QTimer = MagicMock()
fake_qtgui.QTextCursor = MagicMock()
fake_qtgui.QKeyEvent = MagicMock()

sys.modules.update({
    'PySide6': fake_pyside, 
    'PySide6.QtCore': fake_qtcore, 
    'PySide6.QtGui': fake_qtgui, 
    'PySide6.QtWidgets': fake_qtwidgets
})

if 'terminal' in sys.modules: del sys.modules['terminal']
if 'mod3d' in sys.modules: del sys.modules['mod3d']
for key in list(sys.modules.keys()):
    if key.startswith('mod3d.'):
        del sys.modules[key]

import FreeCAD
import Part
import mod3d
import terminal
from terminal import PythonTerminal

@pytest.fixture
def term():
    doc = FreeCAD.newDocument("SmoothBodyTestDoc")
    FreeCAD.setActiveDocument("SmoothBodyTestDoc")
    term = PythonTerminal()
    
    term.local_vars["np"] = np
    term.local_vars["numpy"] = np
    term.local_vars["smooth_body"] = mod3d.primitives.smooth_body
    term.local_vars["free_curve"] = mod3d.primitives.free_curve
    
    terminal.QtCore.QTimer.singleShot = lambda ms, func: func()
    yield term
    FreeCAD.closeDocument("SmoothBodyTestDoc")
