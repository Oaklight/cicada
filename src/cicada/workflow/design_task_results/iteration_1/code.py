from build123d import *

# Step 1: Create the tabletop
tabletop = Box(120, 60, 2)  # Create a box with dimensions 120 (length) x 60 (width) x 2 (thickness)

# Step 2: Create the legs
leg = Box(5, 5, 70)  # Create a box with dimensions 5 (width) x 5 (depth) x 70 (height)

# Step 3: Position the legs at each corner of the tabletop
# Calculate the positions for the legs, inset 5 units from the edges
leg_positions = [
    Pos(-55, -25, -36),  # Bottom-left corner
    Pos(55, -25, -36),   # Bottom-right corner
    Pos(-55, 25, -36),   # Top-left corner
    Pos(55, 25, -36)     # Top-right corner
]

# Create the legs at the calculated positions
legs = [loc * leg for loc in leg_positions]

# Step 4: Combine the tabletop and legs into a single assembly
table = Compound(children=[tabletop] + legs)

# Save the result
result = table