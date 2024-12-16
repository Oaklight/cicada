from build123d import *

# Create the main cylindrical container
container = Cylinder(radius=20, height=50)

# Create the smaller cylindrical hole
hole = Cylinder(radius=5, height=50)

# Subtract the hole from the container to create the final shape
result = container - hole