from build123d import *
import math

# Parameters
tabletop_radius = 60
tabletop_thickness = 5
leg_height = 45
leg_radius = 5
leg_positions_radius = 40
leg_angles_degrees = [45, 135, 225, 315]

with BuildPart() as table:
    # Create the legs
    for angle in leg_angles_degrees:
        theta = math.radians(angle)
        x = leg_positions_radius * math.cos(theta)
        y = leg_positions_radius * math.sin(theta)
        with Locations((x, y, 0)):
            Cylinder(
                radius=leg_radius,
                height=leg_height,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    # Create the tabletop
    with Locations((0, 0, leg_height)):
        Cylinder(
            radius=tabletop_radius,
            height=tabletop_thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

# Export the model
table.part.export_stl("table.stl")
