from build123d import *

# Create the table top
table_top = Rectangle(160, 80)  # Sketch the rectangle for the table top
table_top = extrude(table_top, amount=2)  # Extrude to form the table top with 2 units thickness

# Create the legs
leg_radius = 5
leg_length = 50
leg = Circle(leg_radius)  # Sketch the circle for the legs
leg = extrude(leg, amount=leg_length)  # Extrude to form the legs

# Position the legs at the corners of the table top
leg_positions = [
    Pos(leg_radius, leg_radius, 0),  # Bottom-left corner
    Pos(160 - leg_radius, leg_radius, 0),  # Bottom-right corner
    Pos(leg_radius, 80 - leg_radius, 0),  # Top-left corner
    Pos(160 - leg_radius, 80 - leg_radius, 0),  # Top-right corner
]

legs = [leg.locate(pos) for pos in leg_positions]  # Position the legs at the corners
legs = legs[0] + legs[1] + legs[2] + legs[3]  # Combine all legs into a single object

# Create the connectors
connector = Rectangle(2, 2)  # Sketch the rectangle for the connectors
connector = extrude(connector, amount=5)  # Extrude to form the connectors

# Position the connectors at the intersection of the legs and the table top
connector_positions = [
    Pos(leg_radius - 1, leg_radius - 1, 2),  # Bottom-left corner
    Pos(160 - leg_radius - 1, leg_radius - 1, 2),  # Bottom-right corner
    Pos(leg_radius - 1, 80 - leg_radius - 1, 2),  # Top-left corner
    Pos(160 - leg_radius - 1, 80 - leg_radius - 1, 2),  # Top-right corner
]

connectors = [connector.locate(pos) for pos in connector_positions]  # Position the connectors
connectors = connectors[0] + connectors[1] + connectors[2] + connectors[3]  # Combine all connectors into a single object

# Create the gusset plates
gusset_plate = Rectangle(20, 20)  # Sketch the square for the gusset plates
gusset_plate = extrude(gusset_plate, amount=1)  # Extrude to form the gusset plates

# Position the gusset plates at the intersection of the legs and the table top
gusset_positions = [
    Pos(leg_radius - 10, leg_radius - 10, 2),  # Bottom-left corner
    Pos(160 - leg_radius - 10, leg_radius - 10, 2),  # Bottom-right corner
    Pos(leg_radius - 10, 80 - leg_radius - 10, 2),  # Top-left corner
    Pos(160 - leg_radius - 10, 80 - leg_radius - 10, 2),  # Top-right corner
]

gusset_plates = [gusset_plate.locate(pos) for pos in gusset_positions]  # Position the gusset plates
gusset_plates = gusset_plates[0] + gusset_plates[1] + gusset_plates[2] + gusset_plates[3]  # Combine all gusset plates into a single object

# Assemble all parts to form the table
table = table_top + legs + connectors + gusset_plates

# Final result
result = table