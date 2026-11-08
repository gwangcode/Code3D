# 📘 Code3D Workbench: The Exhaustive Master Manual
**Version 1.2.0 – Architect Edition**

## 📑 Table of Contents
1. **Introduction & Architectural Philosophy**
2. **Installation & Terminal Environment**
3. **The AST Rewrite Engine & Parametric History**
4. **Operator Overloading: The Ultimate Matrix**
5. **3D Primitives: Mathematical Foundations**
6. **2D Geometry & Free-Form Curves**
7. **Advanced Point-Cloud & Surface Algorithms**
8. **Interactive Modeling: The `_` Proxy & Fillets**
9. **Utility Functions & Document Management**
10. **Masterclass Workflows & Case Studies**
11. **Troubleshooting & OCC Engine Limitations**

---

## 1. Introduction & Architectural Philosophy

### 1.1 What is Code3D?
Code3D is a specialized procedural modeling engine embedded as a workbench within FreeCAD. It bridges the gap between the raw, destructive speed of standard Python scripting and the robust, non-destructive parametric history of the FreeCAD GUI.

### 1.2 The Two-Tier Architecture
*   **The UI Layer (`terminal.py`)**: A custom PySide `QPlainTextEdit` subclass. It intercepts keystrokes, handles multi-line input via `codeop`, and prevents users from accidentally editing historical code.
*   **The Engine Layer (`mod3d`)**: A collection of math and geometry proxies. It wraps native `Part.Shape` objects in Python classes that support operator overloading (`__add__`, `__sub__`, etc.).

### 1.3 AST Rewriting (Abstract Syntax Tree)
When you press `Enter`, the terminal doesn't just `exec` your code. It parses the AST. If it detects an operation (e.g., a `Shape` object added to another `Shape`), it dynamically generates a new FreeCAD document node (like `Part::Cut`) and binds the original objects as its children. This ensures **100% non-destructive modeling**.

---

## 2. Installation & Terminal Environment

### 2.1 Dependencies
The core engine relies purely on FreeCAD's native `Part` module. However, advanced algorithms require:
```bash
pip install numpy scipy trimesh shapely
```

### 2.2 UI Mechanics & Shortcuts
| Shortcut / Command | Description |
| :--- | :--- |
| `Up` / `Down` | Navigate through command history. |
| `Ctrl + U` | Clear the current input line entirely. |
| `Ctrl + Z` | Undo a multi-line input (step back to `...`). |
| `Enter` | Executes code. If brackets are unclosed, it automatically continues to the next line. |
| `Shift + Enter` | Forces a new line without execution. |
| `clear` / `cls` | Wipes the terminal screen. |
| `Ctrl + Shift + C` | **Global Shortcut**: Select any object in the FreeCAD tree, and `part("object_name")` is copied to your clipboard. |

### 2.3 The Cursor Guard Mechanism
In standard Python consoles, clicking on an old command and pressing Enter can re-execute it. Code3D intercepts `mousePressEvent` and `keyPressEvent`. If you click into the history zone without dragging a text selection, the cursor is instantly teleported to the bottom-most `>>> ` prompt. This prevents accidental execution of modified historical code.

---

## 3. The AST Rewrite Engine & Parametric History

### 3.1 The `_build_tree` Method
When Code3D receives the result of an operation, it translates the `Shape` proxy into a FreeCAD tree.
*   **Boolean Operations**: Creates `Part::MultiFuse`, `Part::Cut`, or `Part::MultiCommon`. The original objects are hidden (`Visibility = False`) but retained in the document. Deleting the boolean node restores the originals.
*   **Transformations**: Modifies the `Placement` attribute of the base object. This is an *in-place* modification.
*   **Fillet/Chamfer**: Creates a `Part::FeaturePython` node. It uses a custom `TransformFeature` proxy that explicitly adds a `Base` property pointing to the original object, folding it in the tree view.

---

## 4. Operator Overloading: The Ultimate Matrix

### 4.1 Addition (`+`)
*   **Shape + Shape**: `cube(10) + sphere(5)`
    *   **Action**: Boolean Fusion.
    *   **Result**: Creates a `Fusion` node.
    *   **Edge Case**: If the shapes do not intersect, the result is a `Compound` solid containing two separate volumes.
*   **Shape + Vector**: `cube(10) + [5, 0, 0]`
    *   **Action**: Translation.
    *   **Result**: Modifies `Placement.Base`. In-place. Does not create a new tree node.

### 4.2 Subtraction (`-`)
*   **Shape - Shape**: `cube(10) - cylinder(2, 20)`
    *   **Action**: Boolean Cut.
    *   **Result**: Drills a hole. Creates a `Cut` node. Base = Cube, Tool = Cylinder.
*   **Shape - Vector**: `cube(10) - [5, 0, 0]`
    *   **Action**: Negative translation.

### 4.3 Multiplication (`*`)
*   **Shape * Shape**: `cube(10) * sphere(5)`
    *   **Action**: Boolean Intersection.
    *   **Result**: Retains only the overlapping volume. Creates a `Common` node.
*   **Shape * Float**: `cube(10) * 2.0`
    *   **Action**: Uniform scale.
    *   **Result**: Bakes a new static `Part::Feature`. The geometry itself is mathematically scaled; the bounding box updates.
*   **Shape * Vector**: `cube(10) * [2, 1, 0.5]`
    *   **Action**: Non-uniform scale.

### 4.4 Matrix Multiplication (`@`)
*   **Shape @ Vector**: `cube(10) @ [0, 0, 1.57]`
    *   **Action**: Rotation. The parameters are in **Radians**.
    *   **Result**: Modifies `Placement.Rotation`. In-place. Note: `1.57` radians is approximately 90 degrees.

### 4.5 Modulo (`%`)
*   **Shape % Vector**: `cube(10) % [0.5, 0, 0, 0, 0, 0]`
    *   **Action**: Shear Transformation.
    *   **Parameters**: `[sxy, sxz, syx, syz, szx, szy]`.
    *   **Result**: Applies a 3x3 shear matrix. Bakes the geometry into a new `Part::Feature`.

### 4.6 Bitwise XOR (`^`)
*   **Shape ^ Vector**: `cube(10) ^ [0, 0, 0.2]`
    *   **Action**: Twist Deformation.
    *   **Result**: Generates a `Part::FeaturePython` node. The twisting angle is calculated based on the Z-axis coordinates (or X/Y if specified). If only Z is twisted, it uses an optimized B-Rep algorithm (`brep_twist_z`).

### 4.7 Bitwise AND (`&`)
*   **Shape & Float**: `cube(10) & 2.0`
    *   **Action**: Fillet (if Float > 0) or Chamfer (if Float < 0).
    *   **Result**: Creates a `TransformFeature` node with a `Base` link. The icon updates to the native blue Fillet/Chamfer icon. The original object folds underneath.
    *   **Example**: `cube(10) & -2` creates a 2mm chamfer.

---

## 5. 3D Primitives: Mathematical Foundations

### 5.1 `cuboid(a, b, c)` & `cube(a)`
*   **Description**: Creates a box anchored at the origin `(0,0,0)`, extending into the positive X, Y, and Z axes.
*   **Mathematical Foundation**: Defined by 6 planar faces and 12 edges.

### 5.2 `sphere(radius)`
*   **Description**: Creates a perfect sphere.
*   **Mathematical Foundation**: A single closed B-Spline surface (or approximated UV sphere depending on OCC settings).
*   **Use Case**: Excellent for applying procedural noise to create asteroids.

### 5.3 `cylinder(radius, height)`
*   **Description**: A cylinder along the Z-axis.
*   **Use Case**: Creating holes for boolean cuts.

### 5.4 `cone(radius, height)`
*   **Description**: Base radius at Z=0, apex at Z=height.

### 5.5 `torus(major_radius, minor_radius)`
*   **Description**: A donut shape.
*   **Mathematical Foundation**: `major_radius` is the distance from the center of the hole to the center of the tube. `minor_radius` is the thickness of the tube itself.

### 5.6 `ellipsoid(a, b, c)`
*   **Description**: A sphere scaled along the X, Y, and Z axes.

### 5.7 `prism(radius, n, height)` & `pyramid(radius, n, height)`
*   **Description**: Regular polygonal prisms/pyramids.
*   **Parameters**: `n` is the number of sides. `radius` is the circumradius (distance from center to vertex).

### 5.8 Platonic Solids
*   `tetrahedron(a)` (4 faces)
*   `octahedron(a)` (8 faces)
*   `dodecahedron(a)` (12 faces)
*   `icosahedron(a)` (20 faces)
*   **Algorithm**: These are generated by calculating the 3D vertex coordinates mathematically, then feeding them into `convex_hull()`.

### 5.9 `convex_hull(points)`
*   **Description**: Computes the smallest convex polyhedron containing all points.
*   **Algorithm**: Uses `trimesh.convex.convex_hull`, converts the resulting triangle mesh to a FreeCAD `Mesh`, and then solidifies it using `Part.makeSolid()`.

### 1. Fundamental Definition & Mathematical Concept
In computational geometry, the **Convex Hull** of a set of points is the smallest convex set that contains all the points. 
*   In 2D space, imagine stretching a rubber band around all the given points and letting it snap tight. The shape enclosed by the rubber band is the 2D convex hull.
*   In 3D space, imagine wrapping the points in shrink-wrap plastic. The resulting tightly wrapped 3D volume is the 3D convex hull.

Code3D leverages this mathematical concept to generate a solid polyhedron from any arbitrary, unordered point cloud. It guarantees that all input points will either lie on the surface of the resulting solid or be strictly inside it.

### 2. The Under-the-Hood Pipeline
The function signature is:
```python
def convex_hull(vertices)
```
It performs a complex series of cross-library operations to translate raw mathematical points into a valid FreeCAD B-Rep (Boundary Representation) Solid.

#### Step 2.1: Array Normalization
```python
mesh = trimesh.convex.convex_hull(np.asarray(vertices, dtype=float))
```
*   **Input**: A list, tuple, or Numpy array of 3D coordinates `[(x1, y1, z1), (x2, y2, z2), ...]`.
*   **Conversion**: `np.asarray(..., dtype=float)` ensures that all inputs are strictly coerced into 64-bit floating-point numbers. This prevents integer overflow or type errors when the underlying C++ libraries process the coordinates.
*   **Trimesh Engine**: The function passes the normalized array to `trimesh.convex.convex_hull`. Trimesh uses the **Qhull** algorithm (specifically Quickhull), which operates in \(O(n \log n)\) average time. It computes the triangle facets required to wrap the points.

#### Step 2.2: Mesh Translation (Trimesh to FreeCAD)
```python
mesh_obj = Mesh.Mesh()
for f in mesh.faces:
    v0, v1, v2 = mesh.vertices[f[0]], mesh.vertices[f[1]], mesh.vertices[f[2]]
    mesh_obj.addFacet(
        float(v0[0]), float(v0[1]), float(v0[2]),
        float(v1[0]), float(v1[1]), float(v1[2]),
        float(v2[0]), float(v2[1]), float(v2[2])
    )
```
*   **The Gap**: Trimesh returns a mathematical mesh consisting of a vertex array and a face index array. FreeCAD cannot natively read a Trimesh object.
*   **The Bridge**: The loop iterates through every triangular face generated by Trimesh. 
*   **Triangulation**: Because a face in Trimesh is a triangle, we can extract its 3 vertices (`v0`, `v1`, `v2`).
*   **Facet Injection**: We create a native FreeCAD `Mesh.Mesh()` object and use `addFacet()` to manually construct the mesh, triangle by triangle. We explicitly cast the coordinates to `float` to avoid any numpy float32/float64 pointer issues.

#### Step 2.3: Mesh to B-Rep Conversion
```python
shape = Part.Shape()
shape.makeShapeFromMesh(mesh_obj.Topology, 0.1)
```
*   **The Process**: FreeCAD's `Part` module (which wraps OpenCASCADE) can convert a polygonal mesh into a topological B-Rep shape. 
*   **Tolerance**: The second parameter `0.1` is the **sewing tolerance**. OCC will attempt to stitch adjacent triangles together if their vertices are within 0.1mm of each other. This is crucial for closing gaps that might occur due to floating-point inaccuracies.
*   **Result**: `shape` is now a `Part.Shell` (a hollow, zero-thickness collection of joined faces).

#### Step 2.4: Solidification
```python
return Shape(Part.makeSolid(shape))
```
*   **The Final Step**: Since the convex hull algorithm wraps the entire point cloud, the resulting Shell is guaranteed to be perfectly watertight and closed. We pass this shell to `Part.makeSolid()`, which instructs OCC to treat the interior volume as a solid mass.
*   **Return**: The result is wrapped in Code3D's `Shape` class, allowing immediate use with operators like `+`, `-`, `&`, etc.

---

### 3. Parameters and Return Values

*   **Parameters**:
    *   `vertices`: `list` | `tuple` | `numpy.ndarray`. A list of 3D coordinates. 
        *   **Requirement**: You must provide at least **4 non-coplanar points** to generate a 3D solid. If you provide fewer, the algorithm will fail to create a 3D volume.
*   **Returns**:
    *   `Shape`: A Code3D `Shape` proxy object wrapping a `Part.Solid`.

---

### 4. Edge Cases, Limitations & Troubleshooting

#### 4.1 Coplanar Points (2D Input)
If all points lie on the exact same plane (e.g., all Z coordinates are 0), Qhull will generate a flat, 2D polygon mesh. When `Part.makeSolid()` is called on a flat shell, it will **fail** because a solid requires an enclosed 3D volume.
*   **Solution**: If you have 2D data, either use `free_curve()` with `make_face=True` or offset one of the points slightly in the Z-axis before calling `convex_hull()`.

#### 4.2 Collinear Points (1D Input)
If all points lie on a single straight line, the algorithm will return a `Wire` (a line) or fail entirely. You need at least 3 non-collinear points to form a flat plane, and 4 non-coplanar points for a 3D solid.

#### 4.3 Non-Manifold Geometry
Because the convex hull mathematically guarantees a watertight surface, the resulting solid will **always** be a valid manifold geometry. You will never see "leaking" or "non-manifold" errors when exporting to STL for 3D printing.

#### 4.4 Concavity Loss (The Shrink-wrap Effect)
The biggest limitation of a Convex Hull is that it **erases all concavities**. If your point cloud forms a C-shape, a donut, or a bowl, the Convex Hull will stretch a tight "skin" over the opening, completely sealing it.
*   **Alternative**: If you need concave shapes, use `smooth_body()` instead, which uses Catmull-Clark subdivision to preserve the unique geometric features of the points.

---

### 5. Practical Applications & Examples

#### Example 1: The Ultimate Bounding Box
If you have a complex, rotated part and need the smallest oriented bounding box, Convex Hull is the first step.
```python
# 1. Create a complex twisted shape
shape = cube(10) ^ [0.5, 0, 0.2]

# 2. Extract its vertices
verts = shape.Vertexes
pts = [(v.X, v.Y, v.Z) for v in verts]

# 3. Create a convex hull (acts as a tight bounding body)
hull = convex_hull(pts)

# 4. Display the result
show(hull, "Bounding_Hull")
```

#### Example 2: Wrapping a Point Cloud
If you have a list of random 3D coordinates and want to create a "meteor" or "asteroid" shape without the smoothness of `smooth_body`.
```python
import random

# Generate 50 random points
pts = [(random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5)) for _ in range(50)]

# Create a faceted, low-poly rock
rock = convex_hull(pts)

# Apply a noise deformation for texture
final_rock = apply_noise(rock, density=0.5, amplitude=0.5)
```

#### Example 3: Combining with Boolean Operations
Because `convex_hull` returns a valid `Solid`, you can immediately use it as a cutting tool or a base body.
```python
# Create a convex hull from a set of points
pts = [(0,0,0), (10,0,0), (0,10,0), (0,0,10), (10,10,10)]
hull = convex_hull(pts)

# Drill a hole through it
drill = cylinder(2, 20) + [0, 0, -5]
final_shape = hull - drill
```

#### Example 4: 2D Convex Hull via 3D Workaround
If you absolutely must find the 2D convex hull of a set of `(x,y)` points, you can force it into 3D and then extract the face.
```python
pts_2d = [(0,0), (10,5), (5,10), (15,15), (0,15)]
# Force into 3D
pts_3d = [(x, y, 0) for x, y in pts_2d]
# Get hull and extract the bottom face
hull_solid = convex_hull(pts_3d)
bottom_face = hull_solid.Faces[0]
```
*(Note: For purely 2D operations, using `Shape2d` or Shapely via the `%` operator is vastly more efficient than using 3D convex hulls).*

---

## 6. 2D Geometry & Free-Form Curves

All 2D functions return a `Shape2d` object (wrapping a Numpy array of `(x,y)` coordinates). The terminal automatically fills them into a `Face` for display.

### 6.1 Standard Shapes
*   `polygon(R, n)`: An n-sided polygon.
*   `circle(R)`: Approximated with an n-sided polygon. The number of segments is auto-calculated based on the radius.
*   `rectangle(a, b)`, `square(a)`, `trapezoid(...)`, `ellipse(a, b)`.

### 6.2 Parametric Curves
*   `parabola(a, b, w)`: A parabolic curve.
*   `hyperbola(a, b, w)`: A hyperbolic curve.
*   `spiral(a, b, num_turns)`: Archimedean spiral.
*   `cardioid(a)`: Heart curve.
*   `cycloid(a)`: Brachistochrone curve.
*   `epicycloid(R, r)`: Curve traced by a point on a rolling circle.
*   `hypocycloid(R, r)`: Curve traced inside a larger circle.
*   `astroid(a)`: Star-shaped hypocycloid.
*   `catenary(a)`: Hanging chain curve.
*   `lemniscate(a)`: Figure-eight curve.
*   `sine(...)`, `tangent(...)`: Trigonometric waves.

### 6.3 `free_curve(points, closed=False, make_face=False)`
*   **Description**: Interpolates a B-Spline curve exactly through your custom points.
*   **Algorithm**: Uses `Part.BSplineCurve().interpolate()`.
*   **Parameters**:
    *   `closed`: If `True`, it connects the last point back to the first point smoothly.
    *   `make_face`: If `True`, it creates a closed wire loop and fills it with `Part.Face()`. If `closed=False`, it adds a straight line to close the gap before filling.
*   **Example**:
    ```python
    pts = [(0,0), (10,-5), (15,5), (5,15), (-5,5)]
    free_curve(pts, closed=True, make_face=True)
    ```

---

## 7. Advanced Point-Cloud & Surface Algorithms

### 7.1 `bspline_surface(points, thickness)`
*   **Description**: Generates a mathematically precise B-Spline surface.
*   **1D Input**: `[(x,y,z), ...]`. Generates a closed curve. If coplanar, fills to a Face.
*   **2D Input**: `[[(x,y,z), ...], ...]`. Generates a free-form surface through a grid of points.
*   **Thickness**: Applies `face.thicken(thickness, 1e-5)` to hollow out the surface.

### 7.2 `smooth_body(points, iterations=3)`
*   **Description**: Transforms unordered, chaotic 3D points into a perfectly smooth, watertight organic solid.
*   **Pipeline**:
    1.  **Convex Hull**: Computes the initial bounding volume.
    2.  **Catmull-Clark Subdivision**: Subdivides the mesh faces into smaller quads `iterations` times.
    3.  **Taubin Smoothing**: Applies a Laplacian smoothing filter that preserves the overall volume (prevents shrinking).
    4.  **Solidification**: Converts the final smoothed mesh back to a `Part.Solid`.
*   **Caveats**: Cannot generate concave geometry (e.g., a donut).
*   **Example**:
    ```python
    import random
    pts = [(random.uniform(-10,10), random.uniform(-10,10), random.uniform(-10,10)) for _ in range(100)]
    smooth_body(pts, iterations=3)
    ```

---

## 8. Interactive Modeling: The `_` Proxy & Fillets

### 8.1 The `SelectionProxy` Class
Code3D injects `_` as a special object that dynamically hooks into your mouse selection.
*   **Usage**: `_ & 2` applies a Fillet.
*   **Mechanism**: It queries `FreeCADGui.Selection.getSelectionEx()`. If specific edges are selected, it applies the operation only to those edges. If a whole body is selected, it applies the operation to all edges.

### 8.2 Fillet/Chamfer Algorithm
*   **Positive Value**: `cube(10) & 2` -> Fillet (rounds the edges).
*   **Negative Value**: `cube(10) & -2` -> Chamfer (bevels the edges).
*   **Tree View**: Generates a `Fillet` or `Chamfer` node with the original object folded as a child.

---

## 9. Utility Functions & Document Management

### 9.1 `sketch(shape, "Sketch_001")`
*   **Description**: Extracts all planar edges of a `Face` and pushes them into a `Sketcher::SketchObject`.
*   **Mechanism**: Calculates the surface normal to align the Sketch's coordinate system, then iterates through the edges, calling `addGeometry()`.

### 9.2 `apply_noise(shape, density, smoothness, amplitude, seed)`
*   **Description**: Adds procedural noise (like rocks or meteorites).
*   **Algorithm**:
    1.  Tesselates the shape.
    2.  Generates random noise.
    3.  Applies `scipy.ndimage.gaussian_filter`.
    4.  Displaces vertices along their normals.
    5.  Rebuilds the solid.

---

## 10. Masterclass Workflows & Case Studies

### 10.1 Case Study: Procedural Asteroid
```python
import random
# 1. Generate random points
pts = [(random.uniform(-10,10), random.uniform(-10,10), random.uniform(-10,10)) for _ in range(150)]
# 2. Create smooth body
rock = smooth_body(pts, iterations=4)
# 3. Add noise for texture
final_rock = apply_noise(rock, density=0.4, amplitude=1.5, seed=42)
```

### 10.2 Case Study: Filleted Bracket
```python
# 1. Create base block
bracket = cuboid(50, 30, 10)
# 2. Cut holes
hole1 = cylinder(5, 15) + [10, 15, 0]
hole2 = cylinder(5, 15) + [40, 15, 0]
bracket_with_holes = bracket - hole1 - hole2
# 3. Apply a 2mm fillet to the edges
bracket_with_holes & 2
```

### 10.3 Case Study: Decorative Vase
```python
import FreeCAD
# 1. Create a 2D profile
profile = free_curve([(0,0), (10,20), (5,40), (8,60)], closed=False)
# 2. Extrude and twist
vase_solid = profile.to_face().extrude(FreeCAD.Vector(0,0,80))
vase_solid ^ [0, 0, 0.1]
```

---

## 11. Troubleshooting & OCC Engine Limitations

### 11.1 Fillet Failures (`StdFail_NotDone`)
*   **Cause**: OpenCASCADE (the geometry kernel) struggles when the fillet radius is too large or when multiple edges intersect at a vertex.
*   **Solution**: Use the mouse to select specific edges (`_ & 1`) rather than applying it to the whole body.

### 11.2 Black or Faceted Shapes
*   **Cause**: FreeCAD defaults to flat lines for performance.
*   **Solution**: Select the object, press `V` then `S` to enable `Shaded` mode.

### 11.3 `ImportError: cannot import name 'sketch'`
*   **Cause**: Circular import. `sketch` must be in the root `utils.py`, not `mod3d/utils.py`.
