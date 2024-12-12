from build123d import *

# Create cube1 (size 10 units), centered at origin and move it up so its base is at z=0
cube1 = Box(10, 10, 10).move(Location(Vector(0, 0, 5)))

# Create cube2 (size 9 units), move it up so there's a 1-unit gap above cube1
# The base of cube2 is at z = top of cube1 (10 units) + 1-unit gap = 11 units
# Since cube2 is centered, move it to z = 11 units + (9/2) = 15.5 units
cube2 = Box(9, 9, 9).move(Location(Vector(0, 0, 15.5)))

# Create cube3 (size 8 units), move it up so there's a 1-unit gap above cube2
# The base of cube3 is at z = top of cube2 (20 units) + 1-unit gap = 21 units
# Since cube3 is centered, move it to z = 21 units + (8/2) = 25 units
cube3 = Box(8, 8, 8).move(Location(Vector(0, 0, 25)))

# Combine the cubes into one model
model = cube1 + cube2 + cube3

# Optionally, export the model to a file (e.g., STL)
# model.export_stl('stacked_cubes.stl')
