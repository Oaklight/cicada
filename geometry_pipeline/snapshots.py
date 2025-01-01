import argparse
import io
import logging
import os
import sys
from typing import List, Optional

import numpy as np
import trimesh
from PIL import Image, ImageEnhance
from tqdm import tqdm

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.append(_parent_dir)
from geometry_pipeline import angles, convert
from common.utils import colorstring

LOG_LEVEL = "DEBUG"

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.addHandler(logging.StreamHandler())


def get_adaptive_camera_distance(
    mesh: trimesh.Trimesh,
    scale_factor=3,
) -> float:
    """Calculates a suitable camera distance based on the mesh's bounding box."""
    bounding_box = mesh.bounding_box.extents  # Get dimensions of the bounding box
    logger.debug(f"Bounding box: {bounding_box}")

    diagonal_length = np.linalg.norm(bounding_box)  # Diagonal of bounding box
    logger.debug(f"Diagonal length: {diagonal_length}")

    logger.debug(f"Adaptive camera distance: {scale_factor * diagonal_length}")
    return scale_factor * diagonal_length  # Scale distance for better fit


def get_camera_pose(
    looking_from_direction="near",
):
    euler_angles = angles.looking_from.get(looking_from_direction.lower())

    return euler_angles


def preview_scene_interactive(
    mesh: trimesh.Trimesh, camera_orientation: np.ndarray, camera_distance: float
):
    """Creates an interactive scene preview using trimesh.SceneViewer."""
    # Create a trimesh Scene for interactive viewing
    scene = trimesh.Scene()
    scene.add_geometry(mesh)

    # Add directional light above the object
    light = trimesh.scene.lighting.autolight(scene)
    scene.add_geometry(light)

    # Set the camera parameters using set_camera
    scene.set_camera(
        angles=camera_orientation,
        distance=camera_distance,
        center=mesh.centroid,
        fov=(45, 45),  # Field of view in degrees (horizontal, vertical)
    )

    logger.debug(f"Camera pose: \n{camera_pose}")
    logger.debug(f"Camera position: \n{scene.camera_transform}")
    logger.debug(f"Camera K: \n{scene.camera.K}")
    logger.debug(f"centroid: \n{mesh.centroid}")

    # Show the interactive viewer
    viewer = scene.show()


def rgba_to_rgb(rgba_image):
    """Convert an RGBA image to RGB."""
    return rgba_image.convert("RGB")


def enhance_color_contrast(image):
    """Enhance the color contrast of the image."""
    enhancer = ImageEnhance.Contrast(image)
    enhanced_image = enhancer.enhance(1.3)  # Increase contrast by a factor of 2
    return enhanced_image


def capture_snapshots(
    mesh: trimesh.Trimesh,
    camera_orientations: np.ndarray,
    camera_distances: List[float],
    out_path: str,
    names: Optional[List[str]] = None,
    resolution=[512, 512],
):
    """Creates an interactive scene preview using trimesh.SceneViewer."""
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    # Create a trimesh Scene for interactive viewing
    scene = trimesh.Scene()
    scene.add_geometry(mesh)

    # Use autolighting
    light = trimesh.scene.lighting.autolight(scene)
    scene.add_geometry(light)

    pbar = tqdm(total=len(camera_orientations))
    for i, cocd in enumerate(zip(camera_orientations, camera_distances)):
        # Set the camera parameters using set_camera
        co, cd = cocd
        scene.set_camera(
            angles=co,
            distance=cd,
            center=mesh.centroid,
            fov=(45, 45),  # Field of view in degrees (horizontal, vertical)
        )

        # save image, 720p
        png = scene.save_image(resolution=resolution, visible=False)

        # Convert RGBA to RGB
        img = Image.open(io.BytesIO(png))
        img_rgb = rgba_to_rgb(img)

        # Enhance color contrast
        img_enhanced = enhance_color_contrast(img_rgb)

        if names is not None:
            img_enhanced.save(os.path.join(out_path, f"{names[i]}.png"))
        else:
            img_enhanced.save(os.path.join(out_path, f"snapshot_{i}.png"))

        pbar.update(1)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--obj_file", type=str)
    group.add_argument("--step_file", type=str)
    group.add_argument("--stl_file", type=str)

    parser.add_argument("-o", "--out_path", type=str, default="../data/snapshots")
    parser.add_argument("-r", "--resolution", type=int, nargs=2, default=[512, 512])
    parser.add_argument(
        "-d",
        "--direction",
        type=str,
        default="front",
        help="Direction or preset collection of directions: 'box', 'common', 'omni', or a comma-separated list of directions.",
    )

    group2 = parser.add_mutually_exclusive_group(required=True)
    group2.add_argument("-p", "--preview", action="store_true", default=False)
    group2.add_argument("-s", "--snapshots", action="store_true", default=False)

    args = parser.parse_args()

    if args.step_file:
        step_file = args.step_file
        obj_path = os.path.dirname(step_file)
        obj_file = os.path.join(
            obj_path, os.path.basename(step_file).replace(".step", ".obj")
        )
        obj_file = convert.step2obj(step_file, obj_path)
    elif args.obj_file:
        obj_file = args.obj_file
    elif args.stl_file:
        obj_file = args.stl_file  # Directly use STL file

    # Use base name without extension for output folder
    obj_name = os.path.splitext(os.path.basename(obj_file))[0]
    pic_path = os.path.join(args.out_path, obj_name)

    mesh = trimesh.load_mesh(obj_file)
    logger.info(colorstring(f"Loaded mesh from {obj_file}", "cyan"))

    if args.direction == "box":
        directions = angles.box_views
    elif args.direction == "common":
        directions = angles.common_views
    elif args.direction == "omni":
        directions = angles.omni_views
    else:
        # Assume it's a comma-separated list of directions
        directions = [d.strip() for d in args.direction.split(",")]

    # Validate directions
    for direction in directions:
        if direction.lower() not in angles.looking_from:
            logger.error(f"Invalid direction: {direction}")
            sys.exit(1)

    logger.info(f"Using directions: {directions}")
    if args.snapshots:
        camera_poses = [get_camera_pose(direction) for direction in directions]
        camera_distances = [get_adaptive_camera_distance(mesh, 1.5)] * len(camera_poses)
        names = [f"snapshot_{direction}" for direction in directions]

        capture_snapshots(
            mesh, camera_poses, camera_distances, pic_path, names, args.resolution
        )

    elif args.preview:
        camera_pose = get_camera_pose(args.direction)
        camera_distance = get_adaptive_camera_distance(mesh, 1.5)
        preview_scene_interactive(mesh, camera_pose, camera_distance)
