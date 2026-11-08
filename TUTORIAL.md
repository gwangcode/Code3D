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

### 5.6 `ellipsoid(a=1, b=1, c=1)`
*   **Description**: Creates an ellipsoid, which is a sphere that has been scaled (stretched or squashed) along the X, Y, and Z axes.
*   **Mathematical Foundation**: 
    *   The standard equation for a unit sphere is \(x^2 + y^2 + z^2 = 1\). 
    *   An ellipsoid is defined by \(\frac{x^2}{a^2} + \frac{y^2}{b^2} + \frac{z^2}{c^2} = 1\).
    *   **Under the Hood**: Code3D creates a native `Part.makeSphere(1.0)` (a perfect unit sphere). It then instantiates a `FreeCAD.Matrix()` and applies a non-uniform 3D scale: `mat.scale(a, b, c)`. Finally, it calls `sphere_shape.transformGeometry(mat)`. 
*   **Topological Properties**: Because it is an affine transformation of a sphere, the B-Rep topology (the number of faces, edges, vertices) remains exactly the same as the original sphere. It remains fully UV-parameterized.
*   **Parameters**:
    *   `a` (float): Semi-axis length along the X-axis (X-radius). Default: 1.
    *   `b` (float): Semi-axis length along the Y-axis (Y-radius). Default: 1.
    *   `c` (float): Semi-axis length along the Z-axis (Z-radius). Default: 1.
*   **Example 1: A flattened disk (oblate spheroid)**
    ```python
    # Stretched in X and Y, squashed in Z
    disk = ellipsoid(a=20, b=20, c=2)
Example 2: A elongated capsule (prolate spheroid)

python
# Stretched vertically
capsule = ellipsoid(a=5, b=5, c=30)
5.7 prism(radius=1, n=3, height=1) & pyramid(radius=1, n=3, height=1)
Description: Creates regular polygonal prisms (extruded n-gons) and pyramids (n-gons tapering to a single apex). Both are anchored at Z=0, extending upwards.

Mathematical Foundation:

prism: Calculates 
n
n vertices of a regular polygon on the XY plane using trigonometry: 
x
=
r
⋅
cos
⁡
(
2
π
i
n
)
x=r⋅cos( 
n
2πi
​
 ), 
y
=
r
⋅
sin
⁡
(
2
π
i
n
)
y=r⋅sin( 
n
2πi
​
 ). It connects them with Part.makePolygon() to form a base wire, converts it to a Part.Face(), and then applies face.extrude(FreeCAD.Vector(0, 0, height)).

pyramid: Uses the same polygonal base. However, instead of extruding, it uses a Lofting algorithm: Part.makeLoft([base_face, Part.Vertex(0, 0, height)], True). It creates a smooth transition from the base face to a single apex point, resulting in a solid pyramid.

Parameters:

radius (float): The circumradius (distance from the geometric center to any vertex of the base polygon). Not the inradius. Default: 1.

n (int): The number of sides for the polygonal base. 
n
≥
3
n≥3 (triangle). Default: 3.

height (float): The total height of the extrusion or pyramid. Default: 1.

Example 1: Hexagonal Prism

python
# A hexagon with circumradius 10, extruded to a height of 25
hex_prism = prism(radius=10, n=6, height=25)
Example 2: Octagonal Pyramid (Gazebo roof)

python
# An 8-sided pyramid with a base radius of 15 and a height of 20
oct_pyramid = pyramid(radius=15, n=8, height=20)
OCC Warning: If 
n
n is set to an extremely large number (e.g., 
n
=
1000
n=1000), the base approximates a circle, but OCC may experience high computation times when calculating the solid's topology. For circles, use cylinder() instead.

### 5.8 Platonic Solids
*   `tetrahedron(a)` (4 faces)
*   `octahedron(a)` (8 faces)
*   `dodecahedron(a)` (12 faces)
*   `icosahedron(a)` (20 faces)
*   **Algorithm**: These are generated by calculating the 3D vertex coordinates mathematically, then feeding them into `convex_hull()`.

### 5.9 `convex_hull(points)`
*   **Description**: Computes the smallest convex polyhedron containing all points.
*   **Algorithm**: Uses `trimesh.convex.convex_hull`, converts the resulting triangle mesh to a FreeCAD `Mesh`, and then solidifies it using `Part.makeSolid()`.

#### 1. Fundamental Definition & Mathematical Concept
In computational geometry, the **Convex Hull** of a set of points is the smallest convex set that contains all the points. 
*   In 2D space, imagine stretching a rubber band around all the given points and letting it snap tight. The shape enclosed by the rubber band is the 2D convex hull.
*   In 3D space, imagine wrapping the points in shrink-wrap plastic. The resulting tightly wrapped 3D volume is the 3D convex hull.

Code3D leverages this mathematical concept to generate a solid polyhedron from any arbitrary, unordered point cloud. It guarantees that all input points will either lie on the surface of the resulting solid or be strictly inside it.

#### 2. The Under-the-Hood Pipeline
The function signature is:
```python
def convex_hull(vertices)
```
It performs a complex series of cross-library operations to translate raw mathematical points into a valid FreeCAD B-Rep (Boundary Representation) Solid.

##### Step 2.1: Array Normalization
```python
mesh = trimesh.convex.convex_hull(np.asarray(vertices, dtype=float))
```
*   **Input**: A list, tuple, or Numpy array of 3D coordinates `[(x1, y1, z1), (x2, y2, z2), ...]`.
*   **Conversion**: `np.asarray(..., dtype=float)` ensures that all inputs are strictly coerced into 64-bit floating-point numbers. This prevents integer overflow or type errors when the underlying C++ libraries process the coordinates.
*   **Trimesh Engine**: The function passes the normalized array to `trimesh.convex.convex_hull`. Trimesh uses the **Qhull** algorithm (specifically Quickhull), which operates in \(O(n \log n)\) average time. It computes the triangle facets required to wrap the points.

##### Step 2.2: Mesh Translation (Trimesh to FreeCAD)
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

##### Step 2.3: Mesh to B-Rep Conversion
```python
shape = Part.Shape()
shape.makeShapeFromMesh(mesh_obj.Topology, 0.1)
```
*   **The Process**: FreeCAD's `Part` module (which wraps OpenCASCADE) can convert a polygonal mesh into a topological B-Rep shape. 
*   **Tolerance**: The second parameter `0.1` is the **sewing tolerance**. OCC will attempt to stitch adjacent triangles together if their vertices are within 0.1mm of each other. This is crucial for closing gaps that might occur due to floating-point inaccuracies.
*   **Result**: `shape` is now a `Part.Shell` (a hollow, zero-thickness collection of joined faces).

##### Step 2.4: Solidification
```python
return Shape(Part.makeSolid(shape))
```
*   **The Final Step**: Since the convex hull algorithm wraps the entire point cloud, the resulting Shell is guaranteed to be perfectly watertight and closed. We pass this shell to `Part.makeSolid()`, which instructs OCC to treat the interior volume as a solid mass.
*   **Return**: The result is wrapped in Code3D's `Shape` class, allowing immediate use with operators like `+`, `-`, `&`, etc.

---

#### 3. Parameters and Return Values

*   **Parameters**:
    *   `vertices`: `list` | `tuple` | `numpy.ndarray`. A list of 3D coordinates. 
        *   **Requirement**: You must provide at least **4 non-coplanar points** to generate a 3D solid. If you provide fewer, the algorithm will fail to create a 3D volume.
*   **Returns**:
    *   `Shape`: A Code3D `Shape` proxy object wrapping a `Part.Solid`.

---

#### 4. Edge Cases, Limitations & Troubleshooting

##### 4.1 Coplanar Points (2D Input)
If all points lie on the exact same plane (e.g., all Z coordinates are 0), Qhull will generate a flat, 2D polygon mesh. When `Part.makeSolid()` is called on a flat shell, it will **fail** because a solid requires an enclosed 3D volume.
*   **Solution**: If you have 2D data, either use `free_curve()` with `make_face=True` or offset one of the points slightly in the Z-axis before calling `convex_hull()`.

##### 4.2 Collinear Points (1D Input)
If all points lie on a single straight line, the algorithm will return a `Wire` (a line) or fail entirely. You need at least 3 non-collinear points to form a flat plane, and 4 non-coplanar points for a 3D solid.

##### 4.3 Non-Manifold Geometry
Because the convex hull mathematically guarantees a watertight surface, the resulting solid will **always** be a valid manifold geometry. You will never see "leaking" or "non-manifold" errors when exporting to STL for 3D printing.

##### 4.4 Concavity Loss (The Shrink-wrap Effect)
The biggest limitation of a Convex Hull is that it **erases all concavities**. If your point cloud forms a C-shape, a donut, or a bowl, the Convex Hull will stretch a tight "skin" over the opening, completely sealing it.
*   **Alternative**: If you need concave shapes, use `smooth_body()` instead, which uses Catmull-Clark subdivision to preserve the unique geometric features of the points.

---

#### 5. Practical Applications & Examples

##### Example 1: The Ultimate Bounding Box
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

##### Example 2: Wrapping a Point Cloud
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

##### Example 3: Combining with Boolean Operations
Because `convex_hull` returns a valid `Solid`, you can immediately use it as a cutting tool or a base body.
```python
# Create a convex hull from a set of points
pts = [(0,0,0), (10,0,0), (0,10,0), (0,0,10), (10,10,10)]
hull = convex_hull(pts)

# Drill a hole through it
drill = cylinder(2, 20) + [0, 0, -5]
final_shape = hull - drill
```

##### Example 4: 2D Convex Hull via 3D Workaround
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

## 6. 2D Geometry & Mathematical Curves

All 2D functions in Code3D return a `Shape2d` object. Under the hood, a `Shape2d` is simply a Python wrapper around a 2D NumPy array of `(x, y)` coordinates. 

**Important Behavior**: When you input a 2D function directly into the Code3D terminal (e.g., `circle(10)`), the engine automatically fills the closed loop and converts it into a `Part.Face` (a 2D planar surface in FreeCAD). 
To turn this flat surface into a 3D solid, you must use the `.extrude(vector)` method in your code, or select the Face in FreeCAD and use the "Extrude" tool in the GUI.

### 6.1 Standard Shapes

These functions generate standard geometric primitives based on polygons and rectangles.

#### `polygon(R=1, n=6)`
*   **Description**: Generates a regular n-sided polygon. A regular polygon is equiangular (all angles are equal) and equilateral (all sides have the same length).
*   **Parameters**:
    *   `R` (float): The **circumradius**. This is the distance from the exact center of the polygon to any of its vertices. (Default: 1).
    *   `n` (int): The number of sides/vertices. Must be >= 3. (Default: 6).
*   **Math Behind It**: Uses `np.linspace(0, 2*np.pi, n, endpoint=False)` to evenly distribute points along a circle of radius `R`, then connects them.
*   **Example**:
    ```python
    # Creates a 10-sided polygon (decagon) with a radius of 15
    poly = polygon(R=15, n=10)
    ```

#### `circle(R=1, step=0.1)`
*   **Description**: Generates a perfect circle. In CAD, a true circle is a continuous curve, but `Shape2d` approximates it using a dense polygon. 
*   **Parameters**:
    *   `R` (float): The radius of the circle. (Default: 1).
    *   `step` (float): The **arc length step**. This controls the density of the polygon approximation. A smaller step results in more segments, making the circle smoother. (Default: 0.1).
*   **Math Behind It**: The function calculates the circumference using \(2 \pi R\), divides it by the `step` parameter to determine how many segments (`n`) are needed, and then calls `polygon(R, n)`. It enforces a minimum of 20 segments.
*   **Example**:
    ```python
    # A smooth circle with radius 50
    c = circle(R=50, step=0.05) 
    # To make it 3D (a cylinder):
    import FreeCAD
    cylinder_solid = c.to_face().extrude(FreeCAD.Vector(0, 0, 20))
    ```

#### `rectangle(a=2, b=1)` & `square(a=1)`
*   **Description**: Generates an axis-aligned rectangle or a perfect square.
*   **Parameters**:
    *   `a` (float): The length along the X-axis. (Default: 2 for rect, 1 for square).
    *   `b` (float): The length along the Y-axis. (Default: 1).
*   **Origin**: The rectangle is anchored at the origin `(0,0)` and extends into the positive X and Y quadrants.
*   **Example**:
    ```python
    rect = rectangle(a=20, b=10)
    sq = square(a=15)
    ```

#### `trapezoid(upper_side=1, lower_side=2, height=1)`
*   **Description**: Generates an isosceles trapezoid (a quadrilateral with one pair of parallel sides).
*   **Parameters**:
    *   `upper_side` (float): The length of the top parallel edge. (Default: 1).
    *   `lower_side` (float): The length of the bottom parallel edge. (Default: 2).
    *   `height` (float): The vertical distance between the parallel sides. (Default: 1).
*   **Example**:
    ```python
    trap = trapezoid(upper_side=10, lower_side=20, height=8)
    ```

#### `ellipse(a=2, b=1, step=0.1)`
*   **Description**: Generates an ellipse. An ellipse is a curve on a plane surrounding two focal points such that a straight line drawn from one focal point to any point on the curve and then to the other focal point has a constant sum of distances.
*   **Parameters**:
    *   `a` (float): The semi-major axis (X-radius). (Default: 2).
    *   `b` (float): The semi-minor axis (Y-radius). (Default: 1).
    *   `step` (float): Controls the segment density, identical to `circle`.
*   **Math Behind It**: Uses Ramanujan's approximation to calculate the ellipse perimeter, dividing by `step` to find the number of segments.
*   **Example**:
    ```python
    oval = ellipse(a=30, b=10)
    ```

#### Regular Polygons (Wrappers)
Code3D provides shortcut functions for common polygons by wrapping `polygon()`:
*   `pentagon(R=1)`: 5 sides.
*   `hexagon(R=1)`: 6 sides.
*   `heptagon(R=1)`: 7 sides.
*   `octagon(R=1)`: 8 sides.
*   `nonagon(R=1)`: 9 sides.
*   `decagon(R=1)`: 10 sides.
*   **Example**: `hexagon(R=10)` creates a 10mm radius hexagon.

---

### 6.2 Parametric Curves

These functions generate mathematically defined curves based on parametric equations. Unlike closed polygons, these curves are inherently **open** (unless explicitly closed by their mathematical nature). Because they do not enclose a volume, Code3D will render them as a `Wire` or a degenerate `Face`. They are highly recommended for path sweeps or lofting operations.

#### `parabola(a=1, b=2, w=1, step=0.1)`
*   **Description**: A plane curve which is mirror-symmetrical and is approximately U-shaped.
*   **Parameters**:
    *   `a` (float): Controls the "width" or sharpness of the parabola. Equation: \(y = \frac{x^2}{4a}\). (Default: 1).
    *   `b` (float): The boundary limits. The curve will span from \(x = -b\) to \(x = +b\). (Default: 2).
    *   `w` (float): Width multiplier used to calculate the total number of points (density). (Default: 1).
    *   `step` (float): The resolution of the curve. (Default: 0.1).
*   **Example**:
    ```python
    # A sharp, narrow parabola stretching from x=-5 to x=5
    p = parabola(a=0.5, b=5)
    ```

#### `hyperbola(a=1, b=1, w=1, step=0.1)`
*   **Description**: A curve formed by the intersection of a double cone and a plane, consisting of two separate branches.
*   **Parameters**:
    *   `a` (float): The distance from the center to the vertex on the X-axis. (Default: 1).
    *   `b` (float): The distance from the center to the asymptote intersection on the Y-axis. (Default: 1).
    *   `w` (float): Angle multiplier. The parameter \(t\) (used in \(\cosh(t)\) and \(\sinh(t)\)) spans from \(-w\pi\) to \(+w\pi\). (Default: 1).
    *   `step` (float): Resolution. (Default: 0.1).
*   **Math Behind It**: Uses parametric equations \(x = a \cosh(t)\), \(y = b \sinh(t)\).
*   **Example**:
    ```python
    h = hyperbola(a=2, b=3)
    ```

#### `spiral(a=1, b=1, num_turns=2, step=0.1)`
*   **Description**: Generates an Archimedean spiral. This is the classic spiral where the distance between successive turns remains constant.
*   **Parameters**:
    *   `a` (float): Growth rate along the X-axis. (Default: 1).
    *   `b` (float): Growth rate along the Y-axis. (Default: 1).
    *   `num_turns` (int): How many full revolutions the spiral makes around the origin. (Default: 2).
    *   `step` (float): Resolution. (Default: 0.1).
*   **Math Behind It**: \(x = a \cdot t \cdot \cos(t)\), \(y = b \cdot t \cdot \sin(t)\).
*   **Example**:
    ```python
    # A tight spring-like 2D spiral with 5 loops
    s = spiral(a=1, b=1, num_turns=5)
    ```

#### `cardioid(a=1, step=0.1)`
*   **Description**: A mathematically perfect heart shape.
*   **Parameters**:
    *   `a` (float): The overall scale of the heart. (Default: 1).
    *   `step` (float): Resolution. (Default: 0.1).
*   **Math Behind It**: Uses the parametric equations \(x = a(2\cos t - \cos 2t)\), \(y = a(2\sin t - \sin 2t)\). 
*   **Example**:
    ```python
    heart = cardioid(a=10)
    ```

#### `cycloid(a=1, num_cycles=2, step=0.1)`
*   **Description**: The curve traced by a point on the rim of a circular wheel as the wheel rolls along a straight line without slipping. Also known as the Brachistochrone curve.
*   **Parameters**:
    *   `a` (float): The radius of the rolling circle. (Default: 1).
    *   `num_cycles` (int): How many complete rotations the circle makes. (Default: 2).
    *   `step` (float): Resolution. (Default: 0.1).
*   **Example**:
    ```python
    cyc = cycloid(a=5, num_cycles=3)
    ```

#### `epicycloid(R=10, r=1, step=0.1)`
*   **Description**: A plane curve produced by tracing the path of a chosen point on the circumference of a circle (radius `r`) which rolls without slipping around a fixed circle (radius `R`).
*   **Parameters**:
    *   `R` (float): The radius of the fixed base circle. (Default: 10).
    *   `r` (float): The radius of the rolling outer circle. (Default: 1).
    *   `step` (float): Resolution. (Default: 0.1).
*   **Example**:
    ```python
    epi = epicycloid(R=20, r=5)
    ```

#### `hypocycloid(R=6, r=1, step=0.1)`
*   **Description**: Similar to the epicycloid, but the smaller circle rolls on the **inside** of the larger fixed circle.
*   **Parameters**:
    *   `R` (float): The radius of the fixed base circle. (Default: 6).
    *   `r` (float): The radius of the rolling inner circle. (Default: 1).
    *   `step` (float): Resolution. (Default: 0.1).
*   **Example**:
    ```python
    hypo = hypocycloid(R=15, r=3)
    ```

#### `astroid(a=1, step=0.1)`
*   **Description**: A specific type of hypocycloid where the rolling circle's radius is 1/4th of the fixed circle's radius. It looks like a 4-pointed star.
*   **Parameters**:
    *   `a` (float): The scale of the star. (Default: 1).
    *   `step` (float): Resolution. (Default: 0.1).
*   **Math Behind It**: \(x = a\cos^3(t)\), \(y = a\sin^3(t)\).
*   **Example**:
    ```python
    star = astroid(a=10)
    ```

#### `catenary(a=1, step=0.1)`
*   **Description**: The curve that an idealized hanging chain or cable assumes under its own weight when supported only at its ends.
*   **Parameters**:
    *   `a` (float): The scaling factor (related to the tension and weight of the chain). (Default: 1).
    *   `step` (float): Resolution. (Default: 0.1).
*   **Example**:
    ```python
    chain = catenary(a=15)
    ```

#### `lemniscate(a=1, step=0.1)`
*   **Description**: A figure-eight shaped curve (infinity symbol).
*   **Parameters**:
    *   `a` (float): The scale of the curve. (Default: 1).
    *   `step` (float): Resolution. (Default: 0.1).
*   **Example**:
    ```python
    infinity = lemniscate(a=10)
    ```

#### `semicircle(radius=1, step=0.1)`
*   **Description**: A perfect half-circle starting from the right (X=radius) and sweeping counter-clockwise to the left (X=-radius).
*   **Parameters**:
    *   `radius` (float): The radius of the full circle. (Default: 1).
    *   `step` (float): Resolution. (Default: 0.1).
*   **Example**:
    ```python
    half_moon = semicircle(radius=20)
    ```

#### `sine(amplitude=1, frequency=1, x_start=0, x_end=2*np.pi, step=0.1)`
*   **Description**: Generates a standard trigonometric sine wave.
*   **Parameters**:
    *   `amplitude` (float): The peak deviation from the center. (Default: 1).
    *   `frequency` (float): The number of wave cycles per unit of X. (Default: 1).
    *   `x_start` (float): The starting X coordinate. (Default: 0).
    *   `x_end` (float): The ending X coordinate. (Default: \(2\pi\), exactly one full cycle).
    *   `step` (float): Resolution. (Default: 0.1).
*   **Example**:
    ```python
    # A high-frequency wave
    wave = sine(amplitude=5, frequency=3, x_end=4*np.pi)
    ```

#### `tangent(x_start=-0.5*np.pi, x_end=0.5*np.pi, step=0.1, height=100)`
*   **Description**: Generates a tangent curve. Because the tangent function goes to infinity at \(\pm \pi/2\), this function automatically clips the vertical asymptotes.
*   **Parameters**:
    *   `x_start`, `x_end` (float): The angular bounds (in radians).
    *   `step` (float): Resolution. (Default: 0.1).
    *   `height` (float): The clipping height limit. Y values exceeding this are automatically masked out to prevent infinite coordinate errors. (Default: 100).
*   **Example**:
    ```python
    t_curve = tangent(x_start=-1.0, x_end=1.0, height=20)
    ```

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

Here is the fully integrated, ultra-detailed manual section. The 1D and 2D examples have been seamlessly merged into Section 7.1, creating a comprehensive, 50-page manual quality guide.

---

# 7. Advanced Surface & Point-Cloud Algorithms

In standard CAD, you usually build shapes by sketching and extruding. In Code3D, we provide algorithmic tools to let you "grow" complex, organic geometry directly from raw coordinates or mathematical grids. 

### 7.1 `bspline_surface(points, thickness=0.0)`

#### 1. Mathematical Concept
A B-Spline (Basis Spline) surface is a piecewise polynomial surface defined by a set of control points. Unlike standard polygons, a B-Spline surface is completely smooth (C2 continuous) across its entire domain. In Code3D, we use **Interpolation**, meaning the resulting mathematical surface will pass *exactly* through every single coordinate you provide.

#### 2. The Execution Pipeline
This function is highly **polymorphic**. Its behavior and underlying mathematical execution change drastically based on whether you feed it a 1D list or a 2D grid.

**Scenario A: 1D Input (A contour)**
*   **Format**: `[(x1, y1, z1), (x2, y2, z2), ...]`
*   **Algorithm**: 
    1. It extracts the points into native `FreeCAD.Vector` objects.
    2. It creates a `Part.BSplineCurve` and calls `.interpolate(vecs, PeriodicFlag=True)`. The `PeriodicFlag=True` forces the curve to automatically close back on itself smoothly (C2 continuous at the seam).
    3. It wraps the curve into a `Part.Wire`.
    4. **Coplanar check**: It attempts to call `Part.Face(wire)`. If the points are perfectly flat (all on the same plane), it succeeds and returns a filled 2D surface. If the points are 3D (non-coplanar), OCC will throw an error, and the function will gracefully return the 3D Wire (the naked curve) instead.

**Scenario B: 2D Input (A grid)**
*   **Format**: `[[(x1, y1, z1), (x2, y2, z2), ...], [...], ...]` (A list of lists, representing a grid of rows and columns).
*   **Algorithm**:
    1. It converts the nested lists into a 2D matrix of `FreeCAD.Vector`.
    2. It initializes a `Part.BSplineSurface()`.
    3. It calls `.interpolate(vecs_2d)`. The OpenCASCADE engine calculates the polynomial basis functions required to create a smooth patch that hits every point.
    4. It converts the surface into a topological `Part.Face`.

#### 3. Parameters
*   **`points`** (`list`): The coordinates defining the shape.
*   **`thickness`** (`float`): If `thickness > 0.0`, the engine takes the generated `Face` and calls `face.thicken(thickness, 1e-5)`. This performs a 3D offset operation, generating a solid shell with the specified thickness and capping the edges. 
    *   *Warning*: If `thickness` is greater than the local radius of curvature, the self-intersecting geometry will cause OCC to crash or return an invalid shape.

#### 4. Detailed Examples: 1D vs. 2D Inputs

##### 🔹 1D Input Examples (Flat Lists)

**Example A: Coplanar 1D Point Set — Generates a Planar Face**
If all points share the same Z coordinate (they are coplanar), the engine successfully closes the wire and automatically fills the interior to create a 2D planar Face.
```python
# 1. Define a set of points all lying flat on the XY plane
pts_1d_coplanar = [
    (0, 0, 0), 
    (10, -5, 0), 
    (20, 0, 0), 
    (15, 10, 0), 
    (5, 15, 0), 
    (-5, 5, 0)
]

# 2. Generate the surface (actually a Face)
# Because thickness is 0.0, it is a zero-thickness mathematical surface
flat_face = bspline_surface(pts_1d_coplanar)
```

**Example B: Non-Coplanar 1D Point Set — Generates a 3D Wire**
If the Z coordinates vary, the engine cannot flatten it into a single plane. It gracefully degrades and returns a 3D closed spatial curve (a Wire).
```python
import math

# 1. Define a 3D spiral path
pts_1d_3d = []
for i in range(20):
    angle = i * (2 * math.pi / 20)
    x = 10 * math.cos(angle)
    y = 10 * math.sin(angle)
    z = i * 2  # Z axis gradually rises
    pts_1d_3d.append((x, y, z))

# 2. Generate the 3D curve
# Note: Because it cannot generate a Face, the `thickness` parameter is ignored here
spatial_wire = bspline_surface(pts_1d_3d)
```

**Example C: 1D Point Set + Thickness — Solidifying a Planar Face**
If the 1D input is coplanar and successfully generates a Face, you can use the `thickness` parameter to extrude/offset it into a 3D solid plate.
```python
# A leaf-like shape
pts_1d_leaf = [(0,0,0), (5,5,0), (10,0,0), (5,-5,0)]

# Generates a solid plate with a thickness of 2.0mm
solid_plate = bspline_surface(pts_1d_leaf, thickness=2.0)
```

##### 🔹 2D Input Examples (Grids)

**Example D: Classic Wavy Surface (Terrain or Ocean)**
Generate a \(5 \times 5\) grid using loops, and apply trigonometric functions to the Z-axis to create mathematical undulations.
```python
import math

# 1. Build a 2D grid of points
grid_points = []
for i in range(5):
    row = []
    for j in range(5):
        x = i * 10
        y = j * 10
        # Create a wave pattern using sine and cosine
        z = 5 * math.sin(i) * math.cos(j) 
        row.append((x, y, z))
    grid_points.append(row)

# 2. Generate the free-form surface
wavy_surface = bspline_surface(grid_points)
```

**Example E: Tubular/Cylindrical Surface (Closed Grid)**
If the coordinates of the first and last rows are identical, the generated surface will be mathematically closed in the U-direction, forming a seamless tube.
```python
import math

# 1. Generate a cylindrical grid (10 rows, 8 columns)
cyl_grid = []
for i in range(10):
    z = i * 2  # Height of each ring
    row = []
    for j in range(8):
        # Angles from 0 to 2pi to ensure the loop closes perfectly
        angle = j * (2 * math.pi / 7) 
        x = 10 * math.cos(angle)
        y = 10 * math.sin(angle)
        row.append((x, y, z))
    cyl_grid.append(row)

# 2. Generate the tubular surface
tube_surface = bspline_surface(cyl_grid)
```

**Example F: 2D Grid + Thickness — Creating Solid Shells**
This is a highly common industrial design workflow. First, generate a smooth free-form surface, then add thickness to make it a 3D printable solid.
```python
# Assume we already have `grid_points` from Example D

# Generate a wavy solid shell with a thickness of 1.5mm
thick_shell = bspline_surface(grid_points, thickness=1.5)
```

##### 💡 Core Comparison: 1D vs. 2D Input

| Feature | 1D Input (Flat List) | 2D Input (Nested List) |
| :--- | :--- | :--- |
| **Data Format** | `[(x,y,z), ...]` | `[[(x,y,z), ...], ...]` |
| **Path Direction** | Only one linear path | Two directions: U and V (Rows & Columns) |
| **Closure Method** | Automatically loops back (Periodic Curve) | Depends on whether the first/last rows or columns overlap |
| **Generated Result** | Generates a **Face** (if coplanar) or a **Wire** (if 3D) | Always generates a **Face** (Free-form surface) |
| **`thickness` Support** | Only works if a Face is successfully generated | Fully supported |

---

### 7.2 `smooth_body(points, iterations=3)`

#### 1. Mathematical Concept
The `smooth_body` algorithm is a **Reverse Engineering** pipeline. It solves a fundamental problem: *"Given a chaotic pile of 3D scan data (points), how do I create a mathematically beautiful, watertight, 3D printable solid?"*

It uses Mesh Subdivision and Laplacian Smoothing. This is the exact same technology used in Hollywood VFX to smooth low-poly character models into high-res organic forms.

#### 2. The Execution Pipeline (Step-by-Step)

**Step 1: Coplanarity Check & Initialization**
*   Converts your points to a NumPy array.
*   Uses SVD (Singular Value Decomposition) to check if all points lie perfectly on a 2D plane. If they do, it gracefully degrades to a 2D Face. If they are 3D, it proceeds.

**Step 2: Convex Hull (The Shrink-Wrap)**
*   Utilizes `trimesh.convex.convex_hull`.
*   It mathematically calculates the tightest polyhedron that contains all your points. The result is a faceted, low-polygon mesh (often looking like a jagged crystal or a rock).

**Step 3: Catmull-Clark Subdivision (`iterations`)**
*   The Convex Hull is a coarse mesh. Subdivision is the process of splitting every polygon into smaller polygons.
*   In each iteration, every face is split into 4 quad faces. A new vertex is added at the center of every original face, and at the midpoint of every original edge.
*   **Parameter `iterations`**: 
    *   `1`: Slightly smoother, low face count.
    *   `3` (Default): Very smooth, moderate face count.
    *   `5+`: Extremely smooth, but generates millions of faces and will severely slow down FreeCAD.

**Step 4: Taubin Smoothing**
*   Standard Laplacian smoothing (moving every vertex to the average position of its neighbors) causes the overall volume to shrink dramatically (like a melting ice cube).
*   Code3D uses **Taubin Smoothing**, which applies a positive smoothing pass (\(\lambda\)) followed by a negative inflation pass (\(\mu\)). This eliminates high-frequency noise (jagged edges) while *preserving the overall volume* of the object.

**Step 5: Solidification**
*   The smoothed mesh is converted to a FreeCAD `Mesh.Topology`.
*   `Part.makeShapeFromMesh()` converts the triangles into a B-Rep Shell.
*   `Part.makeSolid()` turns the closed shell into a mass-bearing Solid.

#### 3. Parameters
*   **`points`** (`list`): A list of `(x, y, z)` tuples. Requires at least 4 non-coplanar points.
*   **`iterations`** (`int`): The number of subdivision passes. Higher values mean a smoother surface but exponentially higher file sizes and computation time. Default is 3.

#### 4. Caveats & Warnings
*   **Convexity Limitation (The Shrink-Wrap Effect)**: Because the pipeline starts with a Convex Hull, **it cannot generate concave shapes**. If your points form a bowl, a donut, or a crescent moon, the algorithm will stretch a flat skin over the hole, sealing it completely. 
*   **Face Count Explosion**: A Convex hull of 100 points might have ~196 faces. After `iterations=3`, that becomes \(196 \times 4^3 = 12,544\) faces. Generating this on the fly in Python takes a few seconds. Setting `iterations=10` would generate billions of faces and crash your computer.

#### 5. Detailed Examples

**Example 1: Procedural Asteroid**
Generating a natural-looking space rock from random data points.
```python
import random
import math

# 1. Generate a chaotic cloud of 80 random points
# We give them a slight bias to form a spherical shape
pts = []
for _ in range(80):
    theta = random.uniform(0, 3.14159)
    phi = random.uniform(0, 6.28318)
    r = random.uniform(8.0, 12.0) # Radius between 8 and 12
    x = r * math.sin(theta) * math.cos(phi)
    y = r * math.sin(theta) * math.sin(phi)
    z = r * math.cos(theta)
    pts.append((x, y, z))

# 2. Generate the smooth solid
# 4 iterations gives it a very organic, melted look
asteroid = smooth_body(pts, iterations=4)

# 3. Optional: Add procedural noise for surface detail
detailed_asteroid = apply_noise(asteroid, density=0.5, amplitude=0.8, seed=42)
```

**Example 2: Repairing a Scanned Object**
If you have raw LIDAR data (say, a scanned apple), the point cloud will have holes and noise.
```python
# Assume 'apple_scan' is a list of 500 points from a scanner
apple_scan = [...] 

# iterations=2 keeps the shape closer to the original data
# Higher iterations will smooth out the dimple of the apple entirely
clean_apple = smooth_body(apple_scan, iterations=2)
```

**Example 3: The Teardrop Crystal (Low-Poly Aesthetic)**
You don't always want it perfectly smooth. Sometimes you want a faceted gemstone.
```python
# Generate points in a teardrop shape
pts = [(random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(0, 20)) for _ in range(50)]

# iterations=0 applies just the Convex Hull (or minimal subdivision)
# iterations=1 retains the faceted crystal look but slightly softens the edges
crystal = smooth_body(pts, iterations=1)
```

---

## 8. Interactive Modeling: The `_` Proxy & Fillets

### 8.1 The `SelectionProxy` Class
Code3D injects `_` as a special object that dynamically hooks into your mouse selection.
*   **Usage**: `_ & 2` applies a Fillet.
*   **Mechanism**: It queries `FreeCADGui.Selection.getSelectionEx()`. If specific edges are selected, it applies the operation only to those edges. If a whole body is selected, it applies the operation to all edges.

### 8.2 Perfect Tree Folding for Fillet & Chamfer
When you execute `_ & 2` (Fillet) or `_ & -2` (Chamfer), the underlying `TransformFeature` and `ViewProviderTransform` classes perfectly replicate native CAD behavior in the Tree View:
1. **Sign Check**: `> 0` executes Fillet; `< 0` executes Chamfer.
2. **Node Generation**: Creates a `Part::FeaturePython` named `Fillet` or `Chamfer`.
3. **Child Folding**: By overriding `getSubObjects()` and `claimChildren()` in the Proxy classes, it forces the original body to become its child, **automatically indenting** it in the Tree View.
4. **Native Icon**: The `ViewProvider` pulls the blue `Part_Fillet.svg` or `Part_Chamfer.svg` from FreeCAD's resources.

---

Here is the ultra-detailed, exhaustive expansion for Section 9 of your manual. It includes deep-dive algorithmic explanations, parameter breakdowns, and multiple practical examples.

---

# 9. Utility Functions & Document Management

Beyond basic geometry generation, Code3D provides powerful utility functions that bridge the gap between 3D space, 2D sketching, and procedural mesh manipulation. These functions allow you to reverse-engineer 3D shapes into 2D profiles, and apply complex mathematical textures to your models.

### 9.1 `sketch(shape_obj, sketch_name=None)`

#### 1. Functional Concept
The `sketch()` function is a reverse-engineering tool. In CAD, you usually create a 2D sketch and extrude it into a 3D solid. This function does the exact opposite: it takes a **3D Face** (like the top of a box or a curved cut surface) and extracts all of its boundary edges, pushing them into a native FreeCAD `Sketcher::SketchObject`.

#### 2. The Mathematical Pipeline (Under the Hood)
Extracting edges from a 3D face is easy. The hard part is making sure the resulting 2D Sketch doesn't look distorted. If you just dump 3D edges into a Sketch, they might be projected onto the default XY plane, destroying the true shape. 

Code3D solves this with a 4-step coordinate alignment:
1. **Plane Extraction**: It accesses the first `Face` of the geometry and inspects its underlying `Surface` (e.g., `Part.Plane`). It extracts the **Normal Vector** (`Surface.Axis`) and a **Point on the Plane** (`Surface.Position`).
2. **Rotation Calculation**: It calculates the quaternion rotation required to align the default Z-axis `(0, 0, 1)` with the Face's Normal Vector.
3. **Placement Application**: It applies this rotation and position to the `Sketcher::SketchObject`'s `Placement` property. This ensures the Sketch is perfectly parallel to the 3D face.
4. **Geometry Injection**: It iterates through `face.Edges` and calls `sketch.addGeometry(edge, False)`. The `False` parameter indicates these are normal construction lines, not reference geometry.

#### 3. Parameters
*   **`shape_obj`** (`Shape` | `Part.Shape`): The 3D object containing the Face you want to extract.
*   **`sketch_name`** (`str`, optional): The desired name for the Sketch object in the FreeCAD tree. If left as `None`, the engine will auto-generate names like `Sketch_001`, `Sketch_002`, etc., preventing name collisions.

#### 4. Examples

**Example 1: Extracting a Slanted Face**
```python
# 1. Create a cube and rotate it slightly
import FreeCAD
my_cube = cube(20)
my_cube @ [0.5, 0.5, 0] # Rotate in X and Y

# 2. Extract the top face (using index 5, which is usually the top)
top_face = my_cube.Faces[5]

# 3. Push it into a Sketch
# Because the cube is rotated, the Sketch will automatically align its plane to match the slanted face!
my_sketch = sketch(top_face, "Slanted_Profile")
```

**Example 2: Extracting a Complex Boolean Cut**
```python
# 1. Create a block with a hole
base = cube(30)
hole = cylinder(10, 40) + [15, 15, -5]
perforated_block = base - hole

# 2. Find the face with the hole in it (usually the top)
# We look for a face that has an inner wire (a hole)
face_with_hole = [f for f in perforated_block.Faces if len(f.Wires) > 1][0]

# 3. Extract the outer boundary and the inner hole into a Sketch
final_sketch = sketch(face_with_hole, "Washer_Profile")
```

> 💡 **Pro Tip**: This function is extremely useful when you want to re-use a complex 3D contour for a 2D laser-cut or CNC operation.

---

### 9.2 `apply_noise(shape, density=0.5, smoothness=2.0, amplitude=1.0, seed=0)`

#### 1. Functional Concept
This function applies **Procedural 3D Noise** to a shape. It simulates natural erosion, rocky textures, and organic imperfections. It is the difference between a "perfect mathematical sphere" and a "rough asteroid". 

#### 2. The Mathematical Pipeline (Under the Hood)
Instead of using a simple random offset (which would create a spiky, chaotic mess), Code3D uses **Gaussian-blurred 3D Noise**:

1. **Tessellation**: The B-Rep solid is temporarily converted into a triangulated mesh (vertices and faces) using `_tessellate()`.
2. **Bounding Box & Padding**: It calculates the bounding box of the mesh and adds a 10% padding to ensure the noise field completely envelops the object.
3. **Grid Generation**: It generates a 3D grid of random floating-point numbers. The resolution of this grid is determined by the `density` parameter.
4. **Gaussian Smoothing**: It applies `scipy.ndimage.gaussian_filter` to the grid. This blurs the random noise, turning it into smooth, organic hills and valleys (similar to Perlin Noise). The `smoothness` parameter controls the blur radius.
5. **Coordinate Mapping**: It maps every mesh vertex to a coordinate inside this 3D noise grid.
6. **Normal Displacement**: It calculates the normal vector of every vertex. It then pushes or pulls the vertex along its normal direction. The distance pushed is determined by the interpolated noise value multiplied by the `amplitude`.
7. **Solidification**: It rebuilds the modified mesh back into a B-Rep solid using `_tri_mesh_to_shape()`.

#### 3. Parameters
*   **`shape`** (`Shape`): The input object to deform.
*   **`density`** (float): Controls the frequency of the noise. 
    *   *High density (e.g., 1.0)*: Sharp, high-frequency bumps (looks like sandpaper or coral).
    *   *Low density (e.g., 0.1)*: Broad, slow-changing bumps (looks like planetary continents).
*   **`smoothness`** (float): Controls the `sigma` of the Gaussian blur. Higher values make the noise softer and rounder.
*   **`amplitude`** (float): The physical distance (in millimeters) the surface is pushed in or out. 
*   **`seed`** (int): The random seed. Using the same seed guarantees identical results every time, which is crucial for reproducible parametric models.

#### 4. Examples

**Example 1: The Perfect Asteroid**
```python
# 1. Start with a perfect sphere
base_sphere = sphere(20)

# 2. Apply noise to make it look like a space rock
# High density, moderate amplitude
asteroid = apply_noise(
    base_sphere, 
    density=0.8,   # High frequency bumps
    smoothness=1.5,# Slightly jagged
    amplitude=2.5, # 2.5mm displacement
    seed=42        # Fixed seed for determinism
)
```

**Example 2: Realistic Terrain/Topography**
```python
# 1. Create a flat plate
plate = cuboid(100, 100, 5)

# 2. Apply very smooth, low-frequency noise to the top to simulate mountains
# Low density, high amplitude, very smooth
terrain = apply_noise(
    plate, 
    density=0.05,  # Large, sweeping hills
    smoothness=5.0,# Very smooth, rolling mountains
    amplitude=15.0,# High peaks
    seed=100
)
```

**Example 3: Combining Noise with Real-time Parametric Updates**
If you execute `apply_noise()` in the terminal, Code3D creates a **Parametric `Noise` Node** in the FreeCAD tree. 
1. Click on the `Noise` node in the tree view.
2. Look at the **Data** tab in the FreeCAD property panel.
3. You will see `Density`, `Smoothness`, `Amplitude`, and `Seed` are all fully editable!
4. Change `Seed` from `42` to `99`, and press `Enter`. The asteroid will instantly generate a completely new, unique shape without you having to type a single line of Python again.

> ⚠️ **Warning**: Applying an extreme `amplitude` (e.g., 50mm on a 10mm sphere) will cause the mesh vertices to cross over each other (self-intersection). OpenCASCADE will likely throw an error or generate a corrupted, non-manifold solid when trying to rebuild the B-Rep. Always keep the amplitude relative to the size of your object.

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
# 1. Create a smooth 2D profile (make_face=True ensures it closes into a Face)
# Without it, an open wire cannot be extruded into a solid.
profile = free_curve([(0,0), (10,20), (5,40), (8,60)], closed=True, make_face=True)

# 2. Extract the face and extrude it upwards by 80mm
vase_solid = profile.Shape.extrude(FreeCAD.Vector(0, 0, 80))

# 3. Show the base vase in the document
show(vase_solid, "Vase_Base")

# 4. Apply spiral twist using the ^ operator (0.1 radians per unit of height)
part("Vase_Base") ^ [0, 0, 0.1]
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
