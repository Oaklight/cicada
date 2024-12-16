from build123d import *

# Create the main cylindrical container
container = Cylinder(radius=20, height=50)

# Create the smaller cylindrical hole
hole = Cylinder(radius=5, height=50)

# Subtract the hole from the container to create the final shape
result = container - hole

# Export the result to stl format
from build123d import export_stl
export_stl(to_export=result, file_path="./exported_model.stl")
