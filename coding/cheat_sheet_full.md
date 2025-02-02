# Module: build123d

## Classes

### build123d.Align

- **Signature**: `build123d.Align()`

### build123d.AngularDirection

- **Signature**: `build123d.AngularDirection()`

### build123d.ApproxOption

- **Signature**: `build123d.ApproxOption()`

### build123d.Arrow

- **Signature**: `build123d.Arrow(arrow_size: float, shaft_path: Union[build123d.topology.Edge, build123d.topology.Wire], shaft_width: float, head_at_start: bool = True, head_type: build123d.build_enums.HeadType = <HeadType.CURVED>, mode: build123d.build_enums.Mode = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.ArrowHead

- **Signature**: `build123d.ArrowHead(size: float, head_type: build123d.build_enums.HeadType = <HeadType.CURVED>, rotation: float = 0, mode: build123d.build_enums.Mode = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.AutoNameEnum

- **Signature**: `build123d.AutoNameEnum()`

### build123d.Axis

- **Signature**: `build123d.Axis(*args, **kwargs)`

### build123d.AxisMeta

- **Signature**: `build123d.AxisMeta()`
- **Parent Classes**: type

### build123d.BallJoint

- **Signature**: `build123d.BallJoint(label: 'str', to_part: 'Optional[Union[Solid, Compound]]' = None, joint_location: 'Optional[Location]' = None, angular_range: 'tuple[tuple[float, float], tuple[float, float], tuple[float, float]]' = ((0, 360), (0, 360), (0, 360)), angle_reference: 'Plane' = Plane(o=(0.00, 0.00, 0.00), x=(1.00, 0.00, 0.00), z=(0.00, 0.00, 1.00)))`

### build123d.BaseEdgeObject

- **Signature**: `build123d.BaseEdgeObject(curve: 'Edge', mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.BaseLineObject

- **Signature**: `build123d.BaseLineObject(curve: 'Wire', mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Wire, NodeMixin

### build123d.BasePartObject

- **Signature**: `build123d.BasePartObject(part: 'Union[Part, Solid]', rotation: 'RotationLike' = (0, 0, 0), align: 'Union[Align, tuple[Align, Align, Align]]' = None, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.BaseSketchObject

- **Signature**: `build123d.BaseSketchObject(obj: 'Union[Compound, Face]', rotation: 'float' = 0, align: 'Union[Align, tuple[Align, Align]]' = None, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Bezier

- **Signature**: `build123d.Bezier(*cntl_pnts: 'VectorLike', weights: 'list[float]' = None, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.BoundBox

- **Signature**: `build123d.BoundBox(bounding_box: 'Bnd_Box') -> 'None'`

### build123d.Box

- **Signature**: `build123d.Box(length: 'float', width: 'float', height: 'float', rotation: 'RotationLike' = (0, 0, 0), align: 'Union[Align, tuple[Align, Align, Align]]' = (<Align.CENTER>, <Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.BuildLine

- **Signature**: `build123d.BuildLine(workplane: 'Union[Face, Plane, Location]' = Plane(o=(0.00, 0.00, 0.00), x=(1.00, 0.00, 0.00), z=(0.00, 0.00, 1.00)), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Builder

### build123d.BuildPart

- **Signature**: `build123d.BuildPart(*workplanes: 'Union[Face, Plane, Location]', mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Builder

### build123d.BuildSketch

- **Signature**: `build123d.BuildSketch(*workplanes: 'Union[Face, Plane, Location]', mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Builder

### build123d.Builder

- **Signature**: `build123d.Builder(*workplanes: 'Union[Face, Plane, Location]', mode: 'Mode' = <Mode.ADD>)`

### build123d.CenterArc

- **Signature**: `build123d.CenterArc(center: 'VectorLike', radius: 'float', start_angle: 'float', arc_size: 'float', mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.CenterOf

- **Signature**: `build123d.CenterOf()`

### build123d.Circle

- **Signature**: `build123d.Circle(radius: 'float', align: 'Union[Align, tuple[Align, Align]]' = (<Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Color

- **Signature**: `build123d.Color(*args, **kwargs)`

### build123d.ColorIndex

- **Signature**: `build123d.ColorIndex()`

### build123d.Comparable

- **Signature**: `build123d.Comparable()`

### build123d.Compound

- **Signature**: `build123d.Compound(*args, **kwargs)`
- **Parent Classes**: Shape, Mixin3D, NodeMixin

### build123d.Cone

- **Signature**: `build123d.Cone(bottom_radius: 'float', top_radius: 'float', height: 'float', arc_size: 'float' = 360, rotation: 'RotationLike' = (0, 0, 0), align: 'Union[Align, tuple[Align, Align, Align]]' = (<Align.CENTER>, <Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.CounterBoreHole

- **Signature**: `build123d.CounterBoreHole(radius: 'float', counter_bore_radius: 'float', counter_bore_depth: 'float', depth: 'float' = None, mode: 'Mode' = <Mode.SUBTRACT>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.CounterSinkHole

- **Signature**: `build123d.CounterSinkHole(radius: 'float', counter_sink_radius: 'float', depth: 'float' = None, counter_sink_angle: 'float' = 82, mode: 'Mode' = <Mode.SUBTRACT>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Curve

- **Signature**: `build123d.Curve()`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Cylinder

- **Signature**: `build123d.Cylinder(radius: 'float', height: 'float', arc_size: 'float' = 360, rotation: 'RotationLike' = (0, 0, 0), align: 'Union[Align, tuple[Align, Align, Align]]' = (<Align.CENTER>, <Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.CylindricalJoint

- **Signature**: `build123d.CylindricalJoint(label: 'str', to_part: 'Union[Solid, Compound]' = None, axis: 'Axis' = ((0.0, 0.0, 0.0),(0.0, 0.0, 1.0)), angle_reference: 'VectorLike' = None, linear_range: 'tuple[float, float]' = (0, inf), angular_range: 'tuple[float, float]' = (0, 360))`

### build123d.DimensionLine

- **Signature**: `build123d.DimensionLine(path: Union[build123d.topology.Wire, build123d.topology.Edge, list[Union[build123d.geometry.Vector, build123d.topology.Vertex, tuple[float, float, float]]]], draft: build123d.drafting.Draft = None, sketch: build123d.topology.Sketch = None, label: str = None, arrows: tuple[bool, bool] = (True, True), tolerance: Union[float, tuple[float, float]] = None, label_angle: bool = False, mode: build123d.build_enums.Mode = <Mode.ADD>) -> build123d.topology.Sketch`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.DotLength

- **Signature**: `build123d.DotLength()`

### build123d.DoubleTangentArc

- **Signature**: `build123d.DoubleTangentArc(pnt: 'VectorLike', tangent: 'VectorLike', other: 'Union[Curve, Edge, Wire]', keep: 'Keep' = <Keep.TOP>, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.Draft

- **Signature**: `build123d.Draft(font_size: float = 5.0, font: str = 'Arial', font_style: build123d.build_enums.FontStyle = <FontStyle.REGULAR>, head_type: build123d.build_enums.HeadType = <HeadType.CURVED>, arrow_length: float = 3.0, line_width: float = 0.5, pad_around_text: float = 2.0, unit: build123d.build_enums.Unit = <Unit.MM>, number_display: build123d.build_enums.NumberDisplay = <NumberDisplay.DECIMAL>, display_units: bool = True, decimal_precision: int = 2, fractional_precision: int = 64, extension_gap: float = 2.0) -> None`

### build123d.Drawing

- **Signature**: `build123d.Drawing(shape: build123d.topology.Shape, *, look_at: Union[build123d.geometry.Vector, tuple[float, float], tuple[float, float, float], Iterable[float]] = None, look_from: Union[build123d.geometry.Vector, tuple[float, float], tuple[float, float, float], Iterable[float]] = (1, -1, 1), look_up: Union[build123d.geometry.Vector, tuple[float, float], tuple[float, float, float], Iterable[float]] = (0, 0, 1), with_hidden: bool = True, focus: Optional[float] = None)`

### build123d.Edge

- **Signature**: `build123d.Edge(*args, **kwargs)`
- **Parent Classes**: Shape, Mixin1D, NodeMixin

### build123d.Ellipse

- **Signature**: `build123d.Ellipse(x_radius: 'float', y_radius: 'float', rotation: 'float' = 0, align: 'Union[Align, tuple[Align, Align]]' = (<Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.EllipticalCenterArc

- **Signature**: `build123d.EllipticalCenterArc(center: 'VectorLike', x_radius: 'float', y_radius: 'float', start_angle: 'float' = 0.0, end_angle: 'float' = 90.0, rotation: 'float' = 0.0, angular_direction: 'AngularDirection' = <AngularDirection.COUNTER_CLOCKWISE>, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.EllipticalStartArc

- **Signature**: `build123d.EllipticalStartArc(start: 'VectorLike', end: 'VectorLike', x_radius: 'float', y_radius: 'float', rotation: 'float' = 0.0, large_arc: 'bool' = False, sweep_flag: 'bool' = True, plane: 'Plane' = Plane(o=(0.00, 0.00, 0.00), x=(1.00, 0.00, 0.00), z=(0.00, 0.00, 1.00)), mode: 'Mode' = <Mode.ADD>) -> 'Edge'`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.Export2D

- **Signature**: `build123d.Export2D()`

### build123d.ExportDXF

- **Signature**: `build123d.ExportDXF(version: str = 'AC1027', unit: build123d.build_enums.Unit = <Unit.MM>, color: Optional[build123d.exporters.ColorIndex] = None, line_weight: Optional[float] = None, line_type: Optional[build123d.exporters.LineType] = None)`

### build123d.ExportSVG

- **Signature**: `build123d.ExportSVG(unit: build123d.build_enums.Unit = <Unit.MM>, scale: float = 1, margin: float = 0, fit_to_stroke: bool = True, precision: int = 6, fill_color: Union[build123d.exporters.ColorIndex, ezdxf.colors.RGB, build123d.geometry.Color, NoneType] = None, line_color: Union[build123d.exporters.ColorIndex, ezdxf.colors.RGB, build123d.geometry.Color, NoneType] = <ColorIndex.BLACK: 7>, line_weight: float = 0.09, line_type: build123d.exporters.LineType = <LineType.CONTINUOUS: 'CONTINUOUS'>, dot_length: Union[build123d.exporters.DotLength, float] = <DotLength.INKSCAPE_COMPAT: 0.01>)`

### build123d.ExtensionLine

- **Signature**: `build123d.ExtensionLine(border: Union[build123d.topology.Wire, build123d.topology.Edge, list[Union[build123d.geometry.Vector, build123d.topology.Vertex, tuple[float, float, float]]]], offset: float, draft: build123d.drafting.Draft, sketch: build123d.topology.Sketch = None, label: str = None, arrows: tuple[bool, bool] = (True, True), tolerance: Union[float, tuple[float, float]] = None, label_angle: bool = False, project_line: Union[build123d.geometry.Vector, tuple[float, float], tuple[float, float, float], Iterable[float]] = None, mode: build123d.build_enums.Mode = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Extrinsic

- **Signature**: `build123d.Extrinsic()`

### build123d.Face

- **Signature**: `build123d.Face(*args, **kwargs)`
- **Parent Classes**: Shape, NodeMixin

### build123d.FilletPolyline

- **Signature**: `build123d.FilletPolyline(*pts: 'Union[VectorLike, Iterable[VectorLike]]', radius: 'float', close: 'bool' = False, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Wire, NodeMixin

### build123d.FontStyle

- **Signature**: `build123d.FontStyle()`

### build123d.FrameMethod

- **Signature**: `build123d.FrameMethod()`

### build123d.GeomType

- **Signature**: `build123d.GeomType()`

### build123d.GridLocations

- **Signature**: `build123d.GridLocations(x_spacing: 'float', y_spacing: 'float', x_count: 'int', y_count: 'int', align: 'Union[Align, tuple[Align, Align]]' = (<Align.CENTER>, <Align.CENTER>))`

### build123d.GroupBy

- **Signature**: `build123d.GroupBy(key_f: 'Callable[[T], K]', shapelist: 'Iterable[T]', *, reverse: 'bool' = False)`

### build123d.HeadType

- **Signature**: `build123d.HeadType()`

### build123d.Helix

- **Signature**: `build123d.Helix(pitch: 'float', height: 'float', radius: 'float', center: 'VectorLike' = (0, 0, 0), direction: 'VectorLike' = (0, 0, 1), cone_angle: 'float' = 0, lefthand: 'bool' = False, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.HexLocations

- **Signature**: `build123d.HexLocations(radius: 'float', x_count: 'int', y_count: 'int', major_radius: 'bool' = False, align: 'Union[Align, tuple[Align, Align]]' = (<Align.CENTER>, <Align.CENTER>))`

### build123d.Hole

- **Signature**: `build123d.Hole(radius: 'float', depth: 'float' = None, mode: 'Mode' = <Mode.SUBTRACT>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.IntersectingLine

- **Signature**: `build123d.IntersectingLine(start: 'VectorLike', direction: 'VectorLike', other: 'Union[Curve, Edge, Wire]', mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.Intrinsic

- **Signature**: `build123d.Intrinsic()`

### build123d.JernArc

- **Signature**: `build123d.JernArc(start: 'VectorLike', tangent: 'VectorLike', radius: 'float', arc_size: 'float', mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.Joint

- **Signature**: `build123d.Joint(label: 'str', parent: 'Union[Solid, Compound]')`

### build123d.Keep

- **Signature**: `build123d.Keep()`

### build123d.Kind

- **Signature**: `build123d.Kind()`

### build123d.LengthMode

- **Signature**: `build123d.LengthMode()`

### build123d.Line

- **Signature**: `build123d.Line(*pts: 'Union[VectorLike, Iterable[VectorLike]]', mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.LineType

- **Signature**: `build123d.LineType()`

### build123d.LinearJoint

- **Signature**: `build123d.LinearJoint(label: 'str', to_part: 'Union[Solid, Compound]' = None, axis: 'Axis' = ((0.0, 0.0, 0.0),(0.0, 0.0, 1.0)), linear_range: 'tuple[float, float]' = (0, inf))`

### build123d.Location

- **Signature**: `build123d.Location(*args)`

### build123d.LocationEncoder

- **Signature**: `build123d.LocationEncoder()`
- **Parent Classes**: JSONEncoder

### build123d.LocationList

- **Signature**: `build123d.LocationList(locations: 'list[Location]')`

### build123d.Locations

- **Signature**: `build123d.Locations(*pts: 'Union[VectorLike, Vertex, Location, Face, Plane, Axis, Iterable[VectorLike, Vertex, Location, Face, Plane, Axis]]')`

### build123d.Matrix

- **Signature**: `build123d.Matrix(matrix=None)`

### build123d.MeshType

- **Signature**: `build123d.MeshType()`

### build123d.Mesher

- **Signature**: `build123d.Mesher(unit: build123d.build_enums.Unit = <Unit.MM>)`

### build123d.Mixin1D

- **Signature**: `build123d.Mixin1D()`

### build123d.Mixin3D

- **Signature**: `build123d.Mixin3D()`

### build123d.Mode

- **Signature**: `build123d.Mode()`

### build123d.NumberDisplay

- **Signature**: `build123d.NumberDisplay()`

### build123d.PageSize

- **Signature**: `build123d.PageSize()`

### build123d.Part

- **Signature**: `build123d.Part()`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Plane

- **Signature**: `build123d.Plane(*args, **kwargs)`

### build123d.PlaneMeta

- **Signature**: `build123d.PlaneMeta()`
- **Parent Classes**: type

### build123d.PolarLine

- **Signature**: `build123d.PolarLine(start: 'VectorLike', length: 'float', angle: 'float' = None, direction: 'VectorLike' = None, length_mode: 'LengthMode' = <LengthMode.DIAGONAL>, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.PolarLocations

- **Signature**: `build123d.PolarLocations(radius: 'float', count: 'int', start_angle: 'float' = 0.0, angular_range: 'float' = 360.0, rotate: 'bool' = True, endpoint: 'bool' = False)`

### build123d.Polygon

- **Signature**: `build123d.Polygon(*pts: 'Union[VectorLike, Iterable[VectorLike]]', rotation: 'float' = 0, align: 'Union[Align, tuple[Align, Align]]' = (<Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Polyline

- **Signature**: `build123d.Polyline(*pts: 'Union[VectorLike, Iterable[VectorLike]]', close: 'bool' = False, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Wire, NodeMixin

### build123d.Pos

- **Signature**: `build123d.Pos(*args, **kwargs)`
- **Parent Classes**: Location

### build123d.PositionMode

- **Signature**: `build123d.PositionMode()`

### build123d.PrecisionMode

- **Signature**: `build123d.PrecisionMode()`

### build123d.RadiusArc

- **Signature**: `build123d.RadiusArc(start_point: 'VectorLike', end_point: 'VectorLike', radius: 'float', short_sagitta: 'bool' = True, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.Rectangle

- **Signature**: `build123d.Rectangle(width: 'float', height: 'float', rotation: 'float' = 0, align: 'Union[Align, tuple[Align, Align]]' = (<Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.RectangleRounded

- **Signature**: `build123d.RectangleRounded(width: 'float', height: 'float', radius: 'float', rotation: 'float' = 0, align: 'Union[Align, tuple[Align, Align]]' = (<Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.RegularPolygon

- **Signature**: `build123d.RegularPolygon(radius: 'float', side_count: 'int', major_radius: 'bool' = True, rotation: 'float' = 0, align: 'tuple[Align, Align]' = (<Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.RevoluteJoint

- **Signature**: `build123d.RevoluteJoint(label: 'str', to_part: 'Union[Solid, Compound]' = None, axis: 'Axis' = ((0.0, 0.0, 0.0),(0.0, 0.0, 1.0)), angle_reference: 'VectorLike' = None, angular_range: 'tuple[float, float]' = (0, 360))`

### build123d.RigidJoint

- **Signature**: `build123d.RigidJoint(label: 'str', to_part: 'Optional[Union[Solid, Compound]]' = None, joint_location: 'Union[Location, None]' = None)`

### build123d.Rot

- **Signature**: `build123d.Rot(*args, **kwargs)`
- **Parent Classes**: Location

### build123d.Rotation

- **Signature**: `build123d.Rotation(*args, **kwargs)`
- **Parent Classes**: Location

### build123d.SagittaArc

- **Signature**: `build123d.SagittaArc(start_point: 'VectorLike', end_point: 'VectorLike', sagitta: 'float', mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.Select

- **Signature**: `build123d.Select()`

### build123d.Shape

- **Signature**: `build123d.Shape(obj: 'TopoDS_Shape' = None, label: 'str' = '', color: 'Color' = None, parent: 'Compound' = None)`
- **Parent Classes**: NodeMixin

### build123d.ShapeList

- **Signature**: `build123d.ShapeList()`
- **Parent Classes**: list

### build123d.ShapePredicate

- **Signature**: `build123d.ShapePredicate(*args, **kwargs)`

### build123d.Shell

- **Signature**: `build123d.Shell(*args, **kwargs)`
- **Parent Classes**: Shape, NodeMixin

### build123d.Side

- **Signature**: `build123d.Side()`

### build123d.Sketch

- **Signature**: `build123d.Sketch()`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.SkipClean

- **Signature**: `build123d.SkipClean()`

### build123d.SlotArc

- **Signature**: `build123d.SlotArc(arc: 'Union[Edge, Wire]', height: 'float', rotation: 'float' = 0, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.SlotCenterPoint

- **Signature**: `build123d.SlotCenterPoint(center: 'VectorLike', point: 'VectorLike', height: 'float', rotation: 'float' = 0, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.SlotCenterToCenter

- **Signature**: `build123d.SlotCenterToCenter(center_separation: 'float', height: 'float', rotation: 'float' = 0, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.SlotOverall

- **Signature**: `build123d.SlotOverall(width: 'float', height: 'float', rotation: 'float' = 0, align: 'Union[Align, tuple[Align, Align]]' = (<Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Solid

- **Signature**: `build123d.Solid(*args, **kwargs)`
- **Parent Classes**: Shape, Mixin3D, NodeMixin

### build123d.SortBy

- **Signature**: `build123d.SortBy()`

### build123d.Sphere

- **Signature**: `build123d.Sphere(radius: 'float', arc_size1: 'float' = -90, arc_size2: 'float' = 90, arc_size3: 'float' = 360, rotation: 'RotationLike' = (0, 0, 0), align: 'Union[Align, tuple[Align, Align, Align]]' = (<Align.CENTER>, <Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Spline

- **Signature**: `build123d.Spline(*pts: 'Union[VectorLike, Iterable[VectorLike]]', tangents: 'Iterable[VectorLike]' = None, tangent_scalars: 'Iterable[float]' = None, periodic: 'bool' = False, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.TangentArc

- **Signature**: `build123d.TangentArc(*pts: 'Union[VectorLike, Iterable[VectorLike]]', tangent: 'VectorLike', tangent_from_first: 'bool' = True, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.TechnicalDrawing

- **Signature**: `build123d.TechnicalDrawing(designed_by: str = 'build123d', design_date: Optional[datetime.date] = None, page_size: build123d.build_enums.PageSize = <PageSize.A4>, title: str = 'Title', sub_title: str = 'Sub Title', drawing_number: str = 'B3D-1', sheet_number: int = None, drawing_scale: float = 1.0, nominal_text_size: float = 10.0, line_width: float = 0.5, mode: build123d.build_enums.Mode = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Text

- **Signature**: `build123d.Text(txt: 'str', font_size: 'float', font: 'str' = 'Arial', font_path: 'str' = None, font_style: 'FontStyle' = <FontStyle.REGULAR>, align: 'Union[Align, tuple[Align, Align]]' = (<Align.CENTER>, <Align.CENTER>), path: 'Union[Edge, Wire]' = None, position_on_path: 'float' = 0.0, rotation: 'float' = 0, mode: 'Mode' = <Mode.ADD>) -> 'Compound'`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.ThreePointArc

- **Signature**: `build123d.ThreePointArc(*pts: 'Union[VectorLike, Iterable[VectorLike]]', mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Mixin1D, Edge, NodeMixin

### build123d.Torus

- **Signature**: `build123d.Torus(major_radius: 'float', minor_radius: 'float', minor_start_angle: 'float' = 0, minor_end_angle: 'float' = 360, major_angle: 'float' = 360, rotation: 'RotationLike' = (0, 0, 0), align: 'Union[Align, tuple[Align, Align, Align]]' = (<Align.CENTER>, <Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Transition

- **Signature**: `build123d.Transition()`

### build123d.Trapezoid

- **Signature**: `build123d.Trapezoid(width: 'float', height: 'float', left_side_angle: 'float', right_side_angle: 'float' = None, rotation: 'float' = 0, align: 'Union[Align, tuple[Align, Align]]' = (<Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Triangle

- **Signature**: `build123d.Triangle(*, a: 'float' = None, b: 'float' = None, c: 'float' = None, A: 'float' = None, B: 'float' = None, C: 'float' = None, align: 'Union[None, Align, tuple[Align, Align]]' = None, rotation: 'float' = 0, mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Unit

- **Signature**: `build123d.Unit()`

### build123d.Until

- **Signature**: `build123d.Until()`

### build123d.Vector

- **Signature**: `build123d.Vector(*args, **kwargs)`
- **Parent Classes**: \_vector_add_sub_wrapper

### build123d.Vertex

- **Signature**: `build123d.Vertex(*args, **kwargs)`
- **Parent Classes**: Shape, NodeMixin

### build123d.Wedge

- **Signature**: `build123d.Wedge(xsize: 'float', ysize: 'float', zsize: 'float', xmin: 'float', zmin: 'float', xmax: 'float', zmax: 'float', rotation: 'RotationLike' = (0, 0, 0), align: 'Union[Align, tuple[Align, Align, Align]]' = (<Align.CENTER>, <Align.CENTER>, <Align.CENTER>), mode: 'Mode' = <Mode.ADD>)`
- **Parent Classes**: Shape, Compound, Mixin3D, NodeMixin

### build123d.Wire

- **Signature**: `build123d.Wire(*args, **kwargs)`
- **Parent Classes**: Shape, Mixin1D, NodeMixin

### build123d.WorkplaneList

- **Signature**: `build123d.WorkplaneList(*workplanes: 'Union[Face, Plane, Location]')`

## Functions

### build123d.add

- **Signature**: `build123d.add(objects: Union[build123d.topology.Edge, build123d.topology.Wire, build123d.topology.Face, build123d.topology.Solid, build123d.topology.Compound, build123d.build_common.Builder, Iterable[Union[build123d.topology.Edge, build123d.topology.Wire, build123d.topology.Face, build123d.topology.Solid, build123d.topology.Compound, build123d.build_common.Builder]]], rotation: Union[float, tuple[float, float, float], build123d.geometry.Rotation] = None, clean: bool = True, mode: build123d.build_enums.Mode = <Mode.ADD>) -> build123d.topology.Compound`

### build123d.ansi_pattern

- **Signature**: `build123d.ansi_pattern(*args)`

### build123d.bounding_box

- **Signature**: `build123d.bounding_box(objects: Union[build123d.topology.Shape, Iterable[build123d.topology.Shape]] = None, mode: build123d.build_enums.Mode = <Mode.PRIVATE>) -> Union[build123d.topology.Sketch, build123d.topology.Part]`

### build123d.chamfer

- **Signature**: `build123d.chamfer(objects: Union[build123d.topology.Edge, build123d.topology.Vertex, Iterable[Union[build123d.topology.Edge, build123d.topology.Vertex]]], length: float, length2: float = None, angle: float = None, reference: Union[build123d.topology.Edge, build123d.topology.Face] = None) -> Union[build123d.topology.Sketch, build123d.topology.Part]`

### build123d.delta

- **Signature**: `build123d.delta(shapes_one: 'Iterable[Shape]', shapes_two: 'Iterable[Shape]') -> 'list[Shape]'`

### build123d.downcast

- **Signature**: `build123d.downcast(obj: 'TopoDS_Shape') -> 'TopoDS_Shape'`

### build123d.edge

- **Signature**: `build123d.edge(self, select: 'Select' = <Select.ALL>) -> 'Edge'`

### build123d.edges

- **Signature**: `build123d.edges(self, select: 'Select' = <Select.ALL>) -> 'ShapeList[Edge]'`

### build123d.edges_to_wires

- **Signature**: `build123d.edges_to_wires(edges: 'Iterable[Edge]', tol: 'float' = 1e-06) -> 'list[Wire]'`

### build123d.export_brep

- **Signature**: `build123d.export_brep(to_export: build123d.topology.Shape, file_path: Union[os.PathLike, str, bytes, _io.BytesIO]) -> bool`

### build123d.export_gltf

- **Signature**: `build123d.export_gltf(to_export: build123d.topology.Shape, file_path: Union[os.PathLike, str, bytes], unit: build123d.build_enums.Unit = <Unit.MM>, binary: bool = False, linear_deflection: float = 0.001, angular_deflection: float = 0.1) -> bool`

### build123d.export_step

- **Signature**: `build123d.export_step(to_export: build123d.topology.Shape, file_path: Union[os.PathLike, str, bytes], unit: build123d.build_enums.Unit = <Unit.MM>, write_pcurves: bool = True, precision_mode: build123d.build_enums.PrecisionMode = <PrecisionMode.AVERAGE>) -> bool`

### build123d.export_stl

- **Signature**: `build123d.export_stl(to_export: build123d.topology.Shape, file_path: Union[os.PathLike, str, bytes], tolerance: float = 0.001, angular_tolerance: float = 0.1, ascii_format: bool = False) -> bool`

### build123d.extrude

- **Signature**: `build123d.extrude(to_extrude: 'Union[Face, Sketch]' = None, amount: 'float' = None, dir: 'VectorLike' = None, until: 'Until' = None, target: 'Union[Compound, Solid]' = None, both: 'bool' = False, taper: 'float' = 0.0, clean: 'bool' = True, mode: 'Mode' = <Mode.ADD>) -> 'Part'`

### build123d.face

- **Signature**: `build123d.face(self, select: 'Select' = <Select.ALL>) -> 'Face'`

### build123d.faces

- **Signature**: `build123d.faces(self, select: 'Select' = <Select.ALL>) -> 'ShapeList[Face]'`

### build123d.fillet

- **Signature**: `build123d.fillet(objects: Union[build123d.topology.Edge, build123d.topology.Vertex, Iterable[Union[build123d.topology.Edge, build123d.topology.Vertex]]], radius: float) -> Union[build123d.topology.Sketch, build123d.topology.Part, build123d.topology.Curve]`

### build123d.fix

- **Signature**: `build123d.fix(obj: 'TopoDS_Shape') -> 'TopoDS_Shape'`

### build123d.flatten_sequence

- **Signature**: `build123d.flatten_sequence(*obj: 'T') -> 'list[Any]'`

### build123d.full_round

- **Signature**: `build123d.full_round(edge: 'Edge', invert: 'bool' = False, voronoi_point_count: 'int' = 100, mode: 'Mode' = <Mode.REPLACE>) -> 'tuple[Sketch, Vector, float]'`

### build123d.import_brep

- **Signature**: `build123d.import_brep(file_name: Union[os.PathLike, str, bytes]) -> build123d.topology.Shape`

### build123d.import_step

- **Signature**: `build123d.import_step(filename: Union[os.PathLike, str, bytes]) -> build123d.topology.Compound`

### build123d.import_stl

- **Signature**: `build123d.import_stl(file_name: Union[os.PathLike, str, bytes]) -> build123d.topology.Face`

### build123d.import_svg

- **Signature**: `build123d.import_svg(svg_file: Union[str, pathlib.Path, TextIO], *, flip_y: bool = True, ignore_visibility: bool = False, label_by: str = 'id', is_inkscape_label: bool = False) -> build123d.topology.ShapeList[typing.Union[build123d.topology.Wire, build123d.topology.Face]]`

### build123d.import_svg_as_buildline_code

- **Signature**: `build123d.import_svg_as_buildline_code(file_name: Union[os.PathLike, str, bytes]) -> tuple[str, str]`

### build123d.isclose_b

- **Signature**: `build123d.isclose_b(a: 'float', b: 'float', rel_tol=1e-09, abs_tol=1e-14) -> 'bool'`

### build123d.iso_pattern

- **Signature**: `build123d.iso_pattern(*args)`

### build123d.loft

- **Signature**: `build123d.loft(sections: 'Union[Face, Sketch, Iterable[Union[Vertex, Face, Sketch]]]' = None, ruled: 'bool' = False, clean: 'bool' = True, mode: 'Mode' = <Mode.ADD>) -> 'Part'`

### build123d.make_brake_formed

- **Signature**: `build123d.make_brake_formed(thickness: 'float', station_widths: 'Union[float, Iterable[float]]', line: 'Union[Edge, Wire, Curve]' = None, side: 'Side' = <Side.LEFT>, kind: 'Kind' = <Kind.ARC>, clean: 'bool' = True, mode: 'Mode' = <Mode.ADD>) -> 'Part'`

### build123d.make_face

- **Signature**: `build123d.make_face(edges: 'Union[Edge, Iterable[Edge]]' = None, mode: 'Mode' = <Mode.ADD>) -> 'Sketch'`

### build123d.make_hull

- **Signature**: `build123d.make_hull(edges: 'Union[Edge, Iterable[Edge]]' = None, mode: 'Mode' = <Mode.ADD>) -> 'Sketch'`

### build123d.mirror

- **Signature**: `build123d.mirror(objects: Union[build123d.topology.Edge, build123d.topology.Wire, build123d.topology.Face, build123d.topology.Compound, build123d.topology.Curve, build123d.topology.Sketch, build123d.topology.Part, Iterable[Union[build123d.topology.Edge, build123d.topology.Wire, build123d.topology.Face, build123d.topology.Compound, build123d.topology.Curve, build123d.topology.Sketch, build123d.topology.Part]]] = None, about: build123d.geometry.Plane = Plane(o=(0.00, 0.00, 0.00), x=(1.00, 0.00, 0.00), z=(0.00, -1.00, 0.00)), mode: build123d.build_enums.Mode = <Mode.ADD>) -> Union[build123d.topology.Curve, build123d.topology.Sketch, build123d.topology.Part, build123d.topology.Compound]`

### build123d.modify_copyreg

- **Signature**: `build123d.modify_copyreg()`

### build123d.new_edges

- **Signature**: `build123d.new_edges(*objects: 'Shape', combined: 'Shape') -> 'ShapeList[Edge]'`

### build123d.offset

- **Signature**: `build123d.offset(objects: Union[build123d.topology.Edge, build123d.topology.Face, build123d.topology.Solid, build123d.topology.Compound, Iterable[Union[build123d.topology.Edge, build123d.topology.Face, build123d.topology.Solid, build123d.topology.Compound]]] = None, amount: float = 0, openings: Union[build123d.topology.Face, list[build123d.topology.Face]] = None, kind: build123d.build_enums.Kind = <Kind.ARC>, side: build123d.build_enums.Side = <Side.BOTH>, closed: bool = True, min_edge_length: float = None, mode: build123d.build_enums.Mode = <Mode.REPLACE>) -> Union[build123d.topology.Curve, build123d.topology.Sketch, build123d.topology.Part, build123d.topology.Compound]`

### build123d.pack

- **Signature**: `build123d.pack(objects: 'Collection[Shape]', padding: 'float', align_z: 'bool' = False) -> 'Collection[Shape]'`

### build123d.polar

- **Signature**: `build123d.polar(length: 'float', angle: 'float') -> 'tuple[float, float]'`

### build123d.project

- **Signature**: `build123d.project(objects: Union[build123d.topology.Edge, build123d.topology.Face, build123d.topology.Wire, build123d.geometry.Vector, build123d.topology.Vertex, Iterable[Union[build123d.topology.Edge, build123d.topology.Face, build123d.topology.Wire, build123d.geometry.Vector, build123d.topology.Vertex]]] = None, workplane: build123d.geometry.Plane = None, target: Union[build123d.topology.Solid, build123d.topology.Compound, build123d.topology.Part] = None, mode: build123d.build_enums.Mode = <Mode.ADD>) -> Union[build123d.topology.Curve, build123d.topology.Sketch, build123d.topology.Compound, build123d.topology.ShapeList[build123d.geometry.Vector]]`

### build123d.project_workplane

- **Signature**: `build123d.project_workplane(origin: 'Union[VectorLike, Vertex]', x_dir: 'Union[VectorLike, Vertex]', projection_dir: 'VectorLike', distance: 'float') -> 'Plane'`

### build123d.revolve

- **Signature**: `build123d.revolve(profiles: 'Union[Face, Iterable[Face]]' = None, axis: 'Axis' = ((0.0, 0.0, 0.0),(0.0, 0.0, 1.0)), revolution_arc: 'float' = 360.0, clean: 'bool' = True, mode: 'Mode' = <Mode.ADD>) -> 'Part'`

### build123d.scale

- **Signature**: `build123d.scale(objects: Union[build123d.topology.Shape, Iterable[build123d.topology.Shape]] = None, by: Union[float, tuple[float, float, float]] = 1, mode: build123d.build_enums.Mode = <Mode.REPLACE>) -> Union[build123d.topology.Curve, build123d.topology.Sketch, build123d.topology.Part, build123d.topology.Compound]`

### build123d.section

- **Signature**: `build123d.section(obj: 'Part' = None, section_by: 'Union[Plane, Iterable[Plane]]' = Plane(o=(0.00, 0.00, 0.00), x=(1.00, 0.00, 0.00), z=(0.00, -1.00, 0.00)), height: 'float' = 0.0, clean: 'bool' = True, mode: 'Mode' = <Mode.PRIVATE>) -> 'Sketch'`

### build123d.shapetype

- **Signature**: `build123d.shapetype(obj: 'TopoDS_Shape') -> 'TopAbs_ShapeEnum'`

### build123d.solid

- **Signature**: `build123d.solid(self, select: 'Select' = <Select.ALL>) -> 'Solid'`

### build123d.solids

- **Signature**: `build123d.solids(self, select: 'Select' = <Select.ALL>) -> 'ShapeList[Solid]'`

### build123d.sort_wires_by_build_order

- **Signature**: `build123d.sort_wires_by_build_order(wire_list: 'list[Wire]') -> 'list[list[Wire]]'`

### build123d.split

- **Signature**: `build123d.split(objects: Union[build123d.topology.Edge, build123d.topology.Wire, build123d.topology.Face, build123d.topology.Solid, Iterable[Union[build123d.topology.Edge, build123d.topology.Wire, build123d.topology.Face, build123d.topology.Solid]]] = None, bisect_by: Union[build123d.geometry.Plane, build123d.topology.Face] = Plane(o=(0.00, 0.00, 0.00), x=(1.00, 0.00, 0.00), z=(0.00, -1.00, 0.00)), keep: build123d.build_enums.Keep = <Keep.TOP>, mode: build123d.build_enums.Mode = <Mode.REPLACE>)`

### build123d.sweep

- **Signature**: `build123d.sweep(sections: Union[build123d.topology.Compound, build123d.topology.Edge, build123d.topology.Wire, build123d.topology.Face, build123d.topology.Solid, Iterable[Union[build123d.topology.Compound, build123d.topology.Edge, build123d.topology.Wire, build123d.topology.Face, build123d.topology.Solid]]] = None, path: Union[build123d.topology.Curve, build123d.topology.Edge, build123d.topology.Wire, Iterable[build123d.topology.Edge]] = None, multisection: bool = False, is_frenet: bool = False, transition: build123d.build_enums.Transition = <Transition.TRANSFORMED>, normal: Union[build123d.geometry.Vector, tuple[float, float], tuple[float, float, float], Iterable[float]] = None, binormal: Union[build123d.topology.Edge, build123d.topology.Wire] = None, clean: bool = True, mode: build123d.build_enums.Mode = <Mode.ADD>) -> Union[build123d.topology.Part, build123d.topology.Sketch]`

### build123d.thicken

- **Signature**: `build123d.thicken(to_thicken: 'Union[Face, Sketch]' = None, amount: 'float' = None, normal_override: 'VectorLike' = None, both: 'bool' = False, clean: 'bool' = True, mode: 'Mode' = <Mode.ADD>) -> 'Part'`

### build123d.topo_explore_common_vertex

- **Signature**: `build123d.topo_explore_common_vertex(edge1: 'Union[Edge, TopoDS_Edge]', edge2: 'Union[Edge, TopoDS_Edge]') -> 'Union[Vertex, None]'`

### build123d.topo_explore_connected_edges

- **Signature**: `build123d.topo_explore_connected_edges(edge: 'Edge', parent: 'Shape' = None) -> 'ShapeList[Edge]'`

### build123d.trace

- **Signature**: `build123d.trace(lines: 'Union[Curve, Edge, Wire, Iterable[Union[Curve, Edge, Wire]]]' = None, line_width: 'float' = 1, mode: 'Mode' = <Mode.ADD>) -> 'Sketch'`

### build123d.tuplify

- **Signature**: `build123d.tuplify(obj: 'Any', dim: 'int') -> 'tuple'`

### build123d.unit_conversion_scale

- **Signature**: `build123d.unit_conversion_scale(from_unit: build123d.build_enums.Unit, to_unit: build123d.build_enums.Unit) -> float`

### build123d.unwrapped_shapetype

- **Signature**: `build123d.unwrapped_shapetype(obj: 'Shape') -> 'TopAbs_ShapeEnum'`

### build123d.validate_inputs

- **Signature**: `build123d.validate_inputs(context: 'Builder', validating_class, objects: 'Iterable[Shape]' = None)`

### build123d.vertex

- **Signature**: `build123d.vertex(self, select: 'Select' = <Select.ALL>) -> 'Vertex'`

### build123d.vertices

- **Signature**: `build123d.vertices(self, select: 'Select' = <Select.ALL>) -> 'ShapeList[Vertex]'`

### build123d.wire

- **Signature**: `build123d.wire(self, select: 'Select' = <Select.ALL>) -> 'Wire'`

### build123d.wires

- **Signature**: `build123d.wires(self, select: 'Select' = <Select.ALL>) -> 'ShapeList[Wire]'`

## Variables

- **K** (`TypeVar`): ~K
- **P** (`ParamSpec`): ~P
- **T** (`TypeVar`): ~T
- **T2** (`TypeVar`): ~T2
