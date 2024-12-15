from build123d import *

# Define the side lengths of each cube
side_lengths = [10, 9, 8]

# Create a list to hold the cubes
cubes = []

# Create each cube and position them correctly
current_z = 0
for length in side_lengths:
    cube = Solid.make_box(length, length, length)
    # Move cube in the z-axis with 1 unit gap
    cube = cube.translate((0, 0, current_z))
    cubes.append(cube)
    current_z += length + 1

# Combine all cubes into a single compound
model = Compound.make_compound(cubes)
