from build123d import *


def create_stacked_cubes():
    # Create three cubes with side lengths 10, 9, and 8 units
    cube1 = Solid.make_box(10, 10, 10)
    cube2 = Solid.make_box(9, 9, 9)
    cube3 = Solid.make_box(8, 8, 8)

    # Translate the smaller cubes to create a 1-unit gap between them
    # Place the first cube at origin
    cube2.translate((0.5, 0.5, 11))  # Translate cube2 up by 11 units (10 + 1)
    cube3.translate((1, 1, 21))  # Translate cube3 up by 21 units (10 + 1 + 9 + 1)

    # Combine cubes into a single compound
    stacked_cubes = Compound.make_compound([cube1, cube2, cube3])

    return stacked_cubes


# Call the function and get the stacked cubes model
stacked_cubes_model = create_stacked_cubes()

# Optionally, visualize or export the model
# visualize(stacked_cubes_model)  # Uncomment this line if you have a visualization tool integrated
# stacked_cubes_model.export_to("stacked_cubes_model.step")  # Export to STEP file if desired
