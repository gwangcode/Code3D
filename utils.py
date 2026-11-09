import FreeCAD
import Part

def show(shape, name="Mod3D_Object"):
    from mod3d.patch import Shape
    from mod3d.shapes import Shape2d
    
    if isinstance(shape, Shape):
        shape = shape.shape
    elif isinstance(shape, Shape2d):
        shape = shape.to_face()
        
    if not isinstance(shape, Part.Shape):
        FreeCAD.Console.PrintError("Input is not a Part.Shape!\n")
        return None
        
    doc = FreeCAD.ActiveDocument
    if not doc:
        docs = FreeCAD.listDocuments()
        doc = list(docs.values())[0] if docs else FreeCAD.newDocument()
            
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    doc.recompute()
    
    FreeCAD.Console.PrintMessage(f"✅ Created FreeCAD object: {name}\n")
    return obj

def sketch(shape_obj, sketch_name=None):
    doc = FreeCAD.ActiveDocument
    if not doc:
        doc = FreeCAD.newDocument("Code3D_Sketch")
        FreeCAD.setActiveDocument(doc.Name)

    shape = shape_obj.Shape if hasattr(shape_obj, "Shape") else shape_obj
    faces = shape.Faces
    if not faces:
        raise ValueError("The given object has no faces to extract.")

    if not sketch_name:
        idx = 1
        sketch_name = f"Sketch_{idx:03d}"
        while doc.getObject(sketch_name):
            idx += 1
            sketch_name = f"Sketch_{idx:03d}"

    sk = doc.getObject(sketch_name)
    if not sk:
        sk = doc.addObject("Sketcher::SketchObject", sketch_name)
    elif sk.TypeId != "Sketcher::SketchObject":
        raise TypeError(f"'{sketch_name}' already exists but is not a Sketch object.")

    first_face = faces[0]
    try:
        if hasattr(first_face.Surface, "Axis") and hasattr(first_face.Surface, "Position"):
            plane_axis = first_face.Surface.Axis
            plane_pos = first_face.Surface.Position
            rot = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), plane_axis)
            sk.Placement = FreeCAD.Placement(plane_pos, rot)
    except Exception:
        pass

    count = 0
    for face in faces:
        for edge in face.Edges:
            try:
                sk.addGeometry(edge, False)
                count += 1
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Failed to add edge: {e}\n")

    doc.recompute()
    FreeCAD.Console.PrintMessage(f"✅ Successfully added {count} edges to Sketch '{sketch_name}'.\n")
    return sk
