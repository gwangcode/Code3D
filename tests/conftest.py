import pytest
import sys
import os
import glob
import types
from unittest.mock import MagicMock
import numpy as np

def add_freecad_to_path():
    """自动探测 FreeCAD 的安装路径，兼容 Windows 和 Linux"""
    # 如果当前环境已经能找到 FreeCAD，直接跳过
    try:
        import FreeCAD
        return
    except ImportError:
        pass

    paths_to_add = []

    # 1. 优先从 Conda/micromamba 环境变量读取 (CI 环境最常见的路径)
    if 'CONDA_PREFIX' in os.environ:
        prefix = os.environ['CONDA_PREFIX']
        paths_to_add.extend([
            os.path.join(prefix, 'lib', 'freecad', 'lib'), # Linux
            os.path.join(prefix, 'lib'),                   # Linux
            os.path.join(prefix, 'Library', 'lib'),        # Windows Conda
            os.path.join(prefix, 'Library', 'bin'),        # Windows Conda (最重要，包含 FreeCAD.pyd)
            os.path.join(prefix, 'bin'),                   # Windows Conda
        ])

    # 2. Windows 系统默认安装路径探测
    if sys.platform == 'win32':
        paths_to_add.extend(glob.glob(r"C:\Program Files\FreeCAD*\bin"))
        paths_to_add.extend(glob.glob(r"C:\Program Files\FreeCAD*\lib"))
        paths_to_add.extend(glob.glob(os.path.expanduser(r"~\AppData\Local\FreeCAD*\bin")))
        
    # 3. Linux 系统默认安装路径探测
    if sys.platform.startswith('linux'):
        paths_to_add.extend(glob.glob(r"/usr/lib/freecad/lib"))
        paths_to_add.extend(glob.glob(r"/usr/lib/freecad-python3/lib"))

    # 将存在的路径加入到 sys.path 中
    for p in paths_to_add:
        if p and os.path.exists(p) and p not in sys.path:
            sys.path.append(p)

# 执行路径搜索
add_freecad_to_path()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ==========================================
# 尝试导入 FreeCAD，如果找不到则给出明确提示并退出
# ==========================================
try:
    import FreeCAD
    import Part
except ImportError as e:
    print(f"\n{'='*60}")
    print(f"[FATAL ERROR] Cannot import FreeCAD or Part.")
    print(f"Please ensure FreeCAD is installed and its Python lib path is in PYTHONPATH.")
    print(f"Current sys.path: {sys.path}")
    print(f"{'='*60}\n")
    pytest.exit(f"Missing FreeCAD dependency: {e}", returncode=1)

# ==========================================
# PySide6 Mock 补全 (为无界面 CI 准备)
# ==========================================
class DummyQPlainTextEdit:
    NoWrap = 0
    def __init__(self, *args, **kwargs): pass
    def setStyleSheet(self, *args, **kwargs): pass
    def insertPlainText(self, *args, **kwargs): pass
    def moveCursor(self, *args, **kwargs): pass
    def textCursor(self): return MagicMock()
    def setTextCursor(self, cursor): pass
    def setLineWrapMode(self, mode): pass
    def toPlainText(self): return ""
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

# ==========================================
# 清理模块缓存，确保加载最新的代码
# ==========================================
if 'terminal' in sys.modules: del sys.modules['terminal']
if 'mod3d' in sys.modules: del sys.modules['mod3d']
for key in list(sys.modules.keys()):
    if key.startswith('mod3d.'):
        del sys.modules[key]

import mod3d
import terminal
from terminal import PythonTerminal

@pytest.fixture
def term():
    doc = FreeCAD.newDocument("SmoothBodyTestDoc")
    FreeCAD.setActiveDocument("SmoothBodyTestDoc")
    term = PythonTerminal()
    
    # 强行注入依赖，防止加载旧版缓存
    term.local_vars["np"] = np
    term.local_vars["numpy"] = np
    term.local_vars["smooth_body"] = mod3d.primitives.smooth_body
    term.local_vars["free_curve"] = mod3d.primitives.free_curve
    
    terminal.QtCore.QTimer.singleShot = lambda ms, func: func()
    yield term
    FreeCAD.closeDocument("SmoothBodyTestDoc")
