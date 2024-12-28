# Cheat Sheet

## Stateful Contexts

* **BuildLine** (`build_line.BuildLine`)
* **BuildPart** (`build_part.BuildPart`)
* **BuildSketch** (`build_sketch.BuildSketch`)
* **GridLocations** (`build_common.GridLocations`)
* **HexLocations** (`build_common.HexLocations`)
* **Locations** (`build_common.Locations`)
* **PolarLocations** (`build_common.PolarLocations`)

## Objects

### 1D - BuildLine

* **Bezier** (`objects_curve.Bezier`)
* **CenterArc** (`objects_curve.CenterArc`)
* **DoubleTangentArc** (`objects_curve.DoubleTangentArc`)
* **EllipticalCenterArc** (`objects_curve.EllipticalCenterArc`)
* **FilletPolyline** (`objects_curve.FilletPolyline`)
* **Helix** (`objects_curve.Helix`)
* **IntersectingLine** (`objects_curve.IntersectingLine`)
* **JernArc** (`objects_curve.JernArc`)
* **Line** (`objects_curve.Line`)
* **PolarLine** (`objects_curve.PolarLine`)
* **Polyline** (`objects_curve.Polyline`)
* **RadiusArc** (`objects_curve.RadiusArc`)
* **SagittaArc** (`objects_curve.SagittaArc`)
* **Spline** (`objects_curve.Spline`)
* **TangentArc** (`objects_curve.TangentArc`)
* **ThreePointArc** (`objects_curve.ThreePointArc`)

### 2D - BuildSketch

* **Arrow** (`drafting.Arrow`)
* **ArrowHead** (`drafting.ArrowHead`)
* **Circle** (`objects_sketch.Circle`)
* **DimensionLine** (`drafting.DimensionLine`)
* **Ellipse** (`objects_sketch.Ellipse`)
* **ExtensionLine** (`drafting.ExtensionLine`)
* **Polygon** (`objects_sketch.Polygon`)
* **Rectangle** (`objects_sketch.Rectangle`)
* **RectangleRounded** (`objects_sketch.RectangleRounded`)
* **RegularPolygon** (`objects_sketch.RegularPolygon`)
* **SlotArc** (`objects_sketch.SlotArc`)
* **SlotCenterPoint** (`objects_sketch.SlotCenterPoint`)
* **SlotCenterToCenter** (`objects_sketch.SlotCenterToCenter`)
* **SlotOverall** (`objects_sketch.SlotOverall`)
* **Text** (`objects_sketch.Text`)
* **TechnicalDrawing** (`drafting.TechnicalDrawing`)
* **Trapezoid** (`objects_sketch.Trapezoid`)
* **Triangle** (`objects_sketch.Triangle`)

### 3D - BuildPart

* **Box** (`objects_part.Box`)
* **Cone** (`objects_part.Cone`)
* **CounterBoreHole** (`objects_part.CounterBoreHole`)
* **CounterSinkHole** (`objects_part.CounterSinkHole`)
* **Cylinder** (`objects_part.Cylinder`)
* **Hole** (`objects_part.Hole`)
* **Sphere** (`objects_part.Sphere`)
* **Torus** (`objects_part.Torus`)
* **Wedge** (`objects_part.Wedge`)

## Operations

### 1D - BuildLine

* **add** (`operations_generic.add`)
* **bounding_box** (`operations_generic.bounding_box`)
* **mirror** (`operations_generic.mirror`)
* **offset** (`operations_generic.offset`)
* **scale** (`operations_generic.scale`)
* **split** (`operations_generic.split`)

### 2D - BuildSketch

* **add** (`operations_generic.add`)
* **chamfer** (`operations_generic.chamfer`)
* **fillet** (`operations_generic.fillet`)
* **full_round** (`operations_sketch.full_round`)
* **make_face** (`operations_sketch.make_face`)
* **make_hull** (`operations_sketch.make_hull`)
* **mirror** (`operations_generic.mirror`)
* **offset** (`operations_generic.offset`)
* **scale** (`operations_generic.scale`)
* **split** (`operations_generic.split`)
* **sweep** (`operations_generic.sweep`)
* **trace** (`operations_sketch.trace`)

### 3D - BuildPart

* **add** (`operations_generic.add`)
* **chamfer** (`operations_generic.chamfer`)
* **extrude** (`operations_part.extrude`)
* **fillet** (`operations_generic.fillet`)
* **loft** (`operations_part.loft`)
* **make_brake_formed** (`operations_part.make_brake_formed`)
* **mirror** (`operations_generic.mirror`)
* **offset** (`operations_generic.offset`)
* **revolve** (`operations_part.revolve`)
* **scale** (`operations_generic.scale`)
* **section** (`operations_part.section`)
* **split** (`operations_generic.split`)
* **sweep** (`operations_generic.sweep`)

## Selectors

### 1D - BuildLine

* **vertices** (`build_common.Builder.vertices`)
* **edges** (`build_common.Builder.edges`)
* **wires** (`build_common.Builder.wires`)

### 2D - BuildSketch

* **vertices** (`build_common.Builder.vertices`)
* **edges** (`build_common.Builder.edges`)
* **wires** (`build_common.Builder.wires`)
* **faces** ( `build_common.Builder.faces` )

### 3D - BuildPart

* **vertices** (`build_common.Builder.vertices`)
* **edges** (`build_common.Builder.edges`)
* **wires** (`build_common.Builder.wires`)
* **faces** ( `build_common.Builder.faces` )
* **solids** ( `build_common.Builder.solids` )

## Selector Operators

| Operator | Operand                                                                 | Method                          |
|----------|-------------------------------------------------------------------------|---------------------------------|
| >        | **Axis**, **Edge**, **Wire**, **SortBy**                                | **ShapeList.sort_by**           |
| <        | **Axis**, **Edge**, **Wire**, **SortBy**                                | **ShapeList.sort_by**           |
| >>       | **Axis**, **Edge**, **Wire**, **SortBy**                                | **ShapeList.group_by[-1]**      |
| <<       | **Axis**, **Edge**, **Wire**, **SortBy**                                | **ShapeList.group_by[0]**       |
| \|       | **Axis**, **Plane**, **GeomType**                                       | **ShapeList.filter_by**         |
| []       |                                                                         | Python indexing / slicing       |
|          | **Axis**                                                                | **ShapeList.filter_by_position**|

## Edge and Wire Operators

| Operator | Operand             | Method                          | Description                     |
|----------|---------------------|---------------------------------|---------------------------------|
| @        | 0.0 <= float <= 1.0 | **Mixin1D.position_at**         | Position as Vector along object |
| %        | 0.0 <= float <= 1.0 | **Mixin1D.tangent_at**          | Tangent as Vector along object  |
| ^        | 0.0 <= float <= 1.0 | **Mixin1D.location_at**         | Location along object           |

## Shape Operators

| Operator | Operand | Method                  | Description                             |
|----------|---------|-------------------------|-----------------------------------------|
| ==       | Any     | **Shape.is_same**       | Compare CAD objects not including meta data |

## Plane Operators

| Operator | Operand          | Description                 |
|----------|------------------|-----------------------------|
| ==       | **Plane**        | Check for equality          |
| !=       | **Plane**        | Check for inequality        |
| \-       | **Plane**        | Reverse direction of normal |
| \*       | **Plane**        | Relocate by Location        |

## Vector Operators

| Operator | Operand           | Method                      | Description         |
|----------|-------------------|-----------------------------|---------------------|
| \+       | **Vector**        | **Vector.add**              | Add                 |
| \-       | **Vector**        | **Vector.sub**              | Subtract            |
| \*       | `float` | **Vector.multiply**         | Multiply by scalar  |
| \/       | `float` | **Vector.multiply**         | Divide by scalar    |

## Vertex Operators

| Operator | Operand           | Method                      |
|----------|-------------------|-----------------------------|
| \+       | **Vertex**        | **Vertex.add**              |
| \-       | **Vertex**        | **Vertex.sub**              |

## Enums

| Enum                     | Values                                                                 |
|--------------------------|------------------------------------------------------------------------|
| **Align**                | MIN, CENTER, MAX                                                       |
| **ApproxOption**         | ARC, NONE, SPLINE                                                      |
| **AngularDirection**     | CLOCKWISE, COUNTER_CLOCKWISE                                           |
| **CenterOf**             | GEOMETRY, MASS, BOUNDING_BOX                                           |
| **FontStyle**            | REGULAR, BOLD, ITALIC                                                  |
| **FrameMethod**          | CORRECTED, FRENET                                                      |
| **GeomType**             | BEZIER, BSPLINE, CIRCLE, CONE, CYLINDER, ELLIPSE, EXTRUSION, HYPERBOLA, LINE, OFFSET, OTHER, PARABOLA, PLANE, REVOLUTION, SPHERE, TORUS |
| **HeadType**             | CURVED, FILLETED, STRAIGHT                                             |
| **Keep**                 | TOP, BOTTOM, BOTH, INSIDE, OUTSIDE                                     |
| **Kind**                 | ARC, INTERSECTION, TANGENT                                             |
| **LengthMode**           | DIAGONAL, HORIZONTAL, VERTICAL                                         |
| **MeshType**             | OTHER, MODEL, SUPPORT, SOLIDSUPPORT                                    |
| **Mode**                 | ADD, SUBTRACT, INTERSECT, REPLACE, PRIVATE                             |
| **NumberDisplay**        | DECIMAL, FRACTION                                                      |
| **PageSize**             | A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, LEDGER, LEGAL, LETTER     |
| **PositionMode**         | LENGTH, PARAMETER                                                      |
| **PrecisionMode**        | LEAST, AVERAGE, GREATEST, SESSION                                      |
| **Select**               | ALL, LAST                                                              |
| **Side**                 | BOTH, LEFT, RIGHT                                                      |
| **SortBy**               | LENGTH, RADIUS, AREA, VOLUME, DISTANCE                                 |
| **Transition**           | RIGHT, ROUND, TRANSFORMED                                              |
| **Unit**                 | MC, MM, CM, M, IN, FT                                                  |
| **Until**                | FIRST, LAST, NEXT, PREVIOUS                                            |
