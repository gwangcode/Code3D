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
    doc = FreeCAD.newDocument("SmoothBodyTestDoc")
    FreeCAD.setActiveDocument("SmoothBodyTestDoc")
    term = PythonTerminal()
    terminal.QtCore.QTimer.singleShot = lambda ms, func: func()
    yield term
    FreeCAD.closeDocument("SmoothBodyTestDoc")

# ==========================================
# 测试 1：共面点集生成 2D 曲面
# ==========================================
def test_smooth_body_coplanar(term):
    term.write = MagicMock() 
    pts = [(0,0,0), (10,0,0), (15,10,0), (10,20,0), (0,20,0), (-5,10,0)]
    term.execute_code(f"smooth_body({pts})")
    
    if term.write.call_count > 0:
        print("\n=== TERMINAL ERROR ===")
        print(term.write.call_args[0][0])
        print("======================\n")
        
    obj = FreeCAD.ActiveDocument.getObject("model_1")
    assert obj is not None, "Failed to generate object."
    assert obj.Shape.ShapeType == "Face", "Coplanar points should generate a Face."
    assert obj.Shape.isValid(), "Generated Face is invalid."

# ==========================================
# 测试 2：稀疏点云生成极简曲面的实体
# ==========================================
def test_smooth_body_sparse_points(term):
    term.write = MagicMock()
    pts = [(0,0,0), (10,0,5), (15,10,-2), (10,20,8), (0,20,0), (-5,10,5)]
    term.execute_code(f"smooth_body({pts})")
    
    if term.write.call_count > 0:
        print("\n=== TERMINAL ERROR ===")
        print(term.write.call_args[0][0])
        print("======================\n")
        
    obj = FreeCAD.ActiveDocument.getObject("model_1")
    assert obj is not None, "Failed to generate object."
    assert obj.Shape.ShapeType in ("Solid", "CompSolid"), "Should generate a 3D solid."
    assert obj.Shape.isValid(), "Generated solid is invalid."
    assert obj.Shape.Volume > 0, "Volume must be greater than 0."
    assert obj.Shape.isClosed(), "The resulting solid is not closed (leaking)."
    assert len(obj.Shape.Faces) < 200, "Face count is too high, Loft may have failed."

# ==========================================
# 测试 3：密集点云生成极简曲面的实体
# ==========================================
def test_smooth_body_dense_points(term):
    term.write = MagicMock()
    pts = []
    for i in range(7):
        for j in range(7):
            theta = np.pi * i / 6.0
            phi = 2 * np.pi * j / 6.0
            x = 10 * np.sin(theta) * np.cos(phi)
            y = 10 * np.sin(theta) * np.sin(phi)
            z = 15 * np.cos(theta)
            pts.append((x, y, z))
            
    term.execute_code(f"smooth_body({pts})")
    
    if term.write.call_count > 0:
        print("\n=== TERMINAL ERROR ===")
        print(term.write.call_args[0][0])
        print("======================\n")
        
    obj = FreeCAD.ActiveDocument.getObject("model_1")
    assert obj is not None, "Failed to generate object."
    assert obj.Shape.ShapeType in ("Solid", "CompSolid"), "Should generate a 3D solid."
    assert obj.Shape.isValid(), "Generated solid is invalid."
    assert obj.Shape.isClosed(), "The resulting solid is not closed (leaking)."
    assert obj.Shape.Volume > 0, "Volume must be greater than 0."
    assert len(obj.Shape.Faces) < 200, "Face count is too high, Loft may have failed."

# ==========================================
# 测试 4：点数不足时的异常处理
# ==========================================
def test_smooth_body_insufficient_points(term):
    term.write = MagicMock()
    term.execute_code("smooth_body([(0,0,0), (10,0,0), (0,10,0)])")
    term.write.assert_called_once()
    assert "At least 4 points are required" in term.write.call_args[0][0]
