import pytest
import sys
import os
import glob

def add_freecad_to_path():
    if 'CONDA_PREFIX' in os.environ:
        prefix = os.environ['CONDA_PREFIX']
        for p in [os.path.join(prefix, 'lib', 'freecad', 'lib'), os.path.join(prefix, 'lib')]:
            if os.path.exists(p) and p not in sys.path: sys.path.append(p)
    if sys.platform == 'win32':
        for p in glob.glob(r"C:\Program Files\FreeCAD*\bin"):
            if p not in sys.path: sys.path.append(p)

add_freecad_to_path()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import FreeCAD
    import Part
except ImportError as e:
    pytest.skip(f"Skipping tests: FreeCAD not found. {e}", allow_module_level=True)

import mod3d

def test_mod3d_primitives():
    box = mod3d.cube(10)
    assert isinstance(box.shape, Part.Shape)
    assert abs(box.Volume - 1000.0) < 1e-3

def test_mod3d_operator_patch():
    box = mod3d.cube(10)
    moved = box + [10, 0, 0]
    assert abs(moved.BoundBox.XMin - 10.0) < 1e-3
    
    sphere = mod3d.sphere(6)
    cut_shape = box - sphere
    assert cut_shape.Volume < box.Volume

def test_mixed_2d_3d_operations():
    """测试 3D 完美圆 (Shape) 和 2D 矩形 (Shape2d) 之间的布尔运算"""
    
    c = mod3d.circle(10)       # Shape
    r = mod3d.rectangle(15, 15) # Shape2d
    
    # 1. Shape + Shape2d
    fused_1 = c + r
    assert isinstance(fused_1, mod3d.Shape)
    assert fused_1.isValid()
    
    # 2. Shape2d + Shape
    fused_2 = r + c
    assert isinstance(fused_2, mod3d.Shape)
    assert fused_2.isValid()

    # 3. Shape - Shape2d
    cut_1 = c - r
    assert isinstance(cut_1, mod3d.Shape)
    assert cut_1.isValid()

def test_apply_noise_seed_determinism():
    base = mod3d.sphere(10)
    res1 = mod3d.apply_noise(base, density=0.5, amplitude=1.0, seed=42)
    res2 = mod3d.apply_noise(base, density=0.5, amplitude=1.0, seed=42)
    assert abs(res1.BoundBox.XMax - res2.BoundBox.XMax) < 1e-5
