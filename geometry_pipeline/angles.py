import numpy as np

# Imagine a polar coordinate system where the camera is at the origin, facing into the screen.
# Each basic angle is represented by a triplet of (pitch, yaw, roll), measured in units of π/2.
camera_orientation = {  # looking to
    # basics
    "in": np.array([0, 0, 0]),
    "out": np.array([0, 2, 0]),
    "left": np.array([0, 1, 0]),
    "right": np.array([0, -1, 0]),
    "up": np.array([1, 0, 0]),
    "down": np.array([-1, 0, 0]),
    # from bounding box corners, starting with the near facade's corners in a clockwise
    # direction from the lower-left, assuming the box's front faces you.
    # Then, count the far facade's corners clockwise from its lower-left.
    "in_upper_right": np.array([0.5, -0.5, 0]),  # looking to in upper right
    "in_lower_right": np.array([-0.5, -0.5, 0]),  # looking to in lower right
    "in_lower_left": np.array([-0.5, 0.5, 0]),  # looking to in lower left
    "in_upper_left": np.array([0.5, 0.5, 0]),  # looking to in upper left
    "out_upper_right": np.array([0.5, -1.5, 0]),  # looking to out upper right
    "out_lower_right": np.array([-0.5, -1.5, 0]),  # looking to out lower right
    "out_lower_left": np.array([-0.5, 1.5, 0]),  # looking to out lower left
    "out_upper_left": np.array([0.5, 1.5, 0]),  # looking to out upper left
}

# convert to radians
camera_orientation = {k: v * np.pi / 2 for k, v in camera_orientation.items()}

looking_from = {
    "near": camera_orientation["in"],
    "far": camera_orientation["out"],
    "left": camera_orientation["right"],
    "right": camera_orientation["left"],
    "top": camera_orientation["down"],
    "bottom": camera_orientation["up"],
    # bounding box corners
    "near_lower_left": camera_orientation[
        "in_upper_right"
    ],  # looking from near lower left, to in upper right
    "near_upper_left": camera_orientation[
        "in_lower_right"
    ],  # looking from near upper left, to in lower right
    "near_upper_right": camera_orientation[
        "in_lower_left"
    ],  # looking from near upper right, to in lower left
    "near_lower_right": camera_orientation[
        "in_upper_left"
    ],  # looking from near lower right, to in upper left
    "far_lower_left": camera_orientation[
        "out_upper_right"
    ],  # looking from far lower left, to out upper right
    "far_upper_left": camera_orientation[
        "out_lower_right"
    ],  # looking from far upper left, to out lower right
    "far_upper_right": camera_orientation[
        "out_lower_left"
    ],  # looking from far upper right, to out lower left
    "far_lower_right": camera_orientation[
        "out_upper_left"
    ],  # looking from far lower right, to out upper left
}

# aliasing
looking_from["front"] = looking_from["near"]
looking_from["back"] = looking_from["far"]
looking_from["front_lower_left"] = looking_from["near_lower_left"]
looking_from["front_upper_left"] = looking_from["near_upper_left"]
looking_from["front_upper_right"] = looking_from["near_upper_right"]
looking_from["front_lower_right"] = looking_from["near_lower_right"]
looking_from["back_lower_left"] = looking_from["far_lower_left"]
looking_from["back_upper_left"] = looking_from["far_upper_left"]
looking_from["back_upper_right"] = looking_from["far_upper_right"]
looking_from["back_lower_right"] = looking_from["far_lower_right"]

primary_views = [
    "front",
    "back",
    "left",
    "right",
    "top",
    "bottom",
    "front_lower_left",
    "front_upper_left",
    "front_upper_right",
    "front_lower_right",
    "back_lower_left",
    "back_upper_left",
    "back_upper_right",
    "back_lower_right",
]

box_views = [
    "front_lower_left",
    "front_upper_left",
    "front_upper_right",
    "front_lower_right",
    "back_lower_left",
    "back_upper_left",
    "back_upper_right",
    "back_lower_right",
]

common_views = [
    "front",
    "back",
    "left",
    "right",
    "top",
    "bottom",
]

omni_views = primary_views  # includes both common and box views
