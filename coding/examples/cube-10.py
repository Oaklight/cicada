from build123d import *

# Define the side length of the cube
side_length = 10

# Create a cube with the specified side length
cube = Solid.make_box(side_length, side_length, side_length)

# Exporting the cube to a file if needed, for example as an STL file
# cube.export_stl("cube.stl")

# Output the cube object for visualization or further processing
print(cube)