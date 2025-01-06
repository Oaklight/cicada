import argparse
import io
import logging
import os
import sys
from typing import List, Literal, Optional

import numpy as np
import trimesh
from PIL import Image, ImageEnhance
from tqdm import tqdm

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
sys.path.append(_parent_dir)
from common.utils import colorstring
from geometry_pipeline import angles, convert

LOG_LEVEL = "DEBUG"

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.addHandler(logging.StreamHandler())


def get_adaptive_camera_distance(
    mesh: trimesh.Trimesh,
    scale_factor: float = 3,
) -> float:
    """Calculates a suitable camera distance based on the mesh's bounding box.

    Args:
        mesh (trimesh.Trimesh): The mesh for which to calculate the camera distance.
        scale_factor (float, optional): Scaling factor for the camera distance. Defaults to 3.

    Returns:
        float: The calculated camera distance.
    """
    bounding_box = mesh.bounding_box.extents
    logger.debug(f"Bounding box: {bounding_box}")

    diagonal_length = np.linalg.norm(bounding_box)  # Diagonal of bounding box
    logger.debug(f"Diagonal length: {diagonal_length}")

    logger.debug(f"Adaptive camera distance: {scale_factor * diagonal_length}")
    return scale_factor * diagonal_length  # Scale distance for better fit


def get_camera_pose(
    looking_from_direction: str = "near",
) -> np.ndarray:
    """Retrieves the camera pose (Euler angles) for a given direction.

    Args:
        looking_from_direction (str, optional): The direction from which the camera is looking. Defaults to "near".

    Returns:
        np.ndarray: The Euler angles representing the camera pose.
    """
    euler_angles = angles.looking_from.get(looking_from_direction.lower())
    return euler_angles


def preview_scene_interactive(
    mesh: trimesh.Trimesh, camera_orientation: np.ndarray, camera_distance: float
) -> None:
    """Creates an interactive scene preview using trimesh.SceneViewer.

    Args:
        mesh (trimesh.Trimesh): The mesh to be displayed in the scene.
        camera_orientation (np.ndarray): The Euler angles for the camera orientation.
        camera_distance (float): The distance of the camera from the mesh.
    """
    scene = trimesh.Scene()
    scene.add_geometry(mesh)

    light = trimesh.scene.lighting.autolight(scene)
    scene.add_geometry(light)

    scene.set_camera(
        angles=camera_orientation,
        distance=camera_distance,
        center=mesh.centroid,
        fov=(45, 45),  # Field of view in degrees (horizontal, vertical)
    )

    logger.debug(f"Camera position: \n{scene.camera_transform}")
    logger.debug(f"Camera K: \n{scene.camera.K}")
    logger.debug(f"centroid: \n{mesh.centroid}")

    viewer = scene.show()


def rgba_to_rgb(rgba_image: Image.Image) -> Image.Image:
    """Converts an RGBA image to RGB.

    Args:
        rgba_image (Image.Image): The RGBA image to convert.

    Returns:
        Image.Image: The converted RGB image.
    """
    return rgba_image.convert("RGB")


def enhance_color_contrast(image: Image.Image, factor: float = 1.2) -> Image.Image:
    """Enhances the color contrast of the image.

    Args:
        image (Image.Image): The image to enhance.

    Returns:
        Image.Image: The enhanced image.
    """
    enhancer = ImageEnhance.Contrast(image)
    enhanced_image = enhancer.enhance(factor)
    return enhanced_image


def capture_snapshots(
    mesh: trimesh.Trimesh,
    camera_orientations: np.ndarray,
    camera_distances: List[float],
    output_dir: str,
    names: Optional[List[str]] = None,
    resolution: List[int] = [512, 512],
    contrast_factor: float = 1.2,
) -> List[str]:
    """Captures snapshots of the mesh from different camera orientations and distances.

    Args:
        mesh (trimesh.Trimesh): The mesh to capture snapshots of.
        camera_orientations (np.ndarray): List of camera orientations (Euler angles).
        camera_distances (List[float]): List of camera distances.
        output_dir (str): The output directory to save the snapshots.
        names (Optional[List[str]], optional): List of names for the snapshots. Defaults to None.
        resolution (List[int], optional): The resolution of the snapshots. Defaults to [512, 512].

    Returns:
        List[str]: A list of paths to the saved snapshot images.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a trimesh Scene for interactive viewing
    scene = trimesh.Scene()
    scene.add_geometry(mesh)

    # Use autolighting
    light = trimesh.scene.lighting.autolight(scene)
    scene.add_geometry(light)

    # List to store the paths of the saved images
    snapshot_paths = []

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
        img_enhanced = enhance_color_contrast(img_rgb, contrast_factor)

        # Determine the output file path
        if names is not None:
            file_path = os.path.join(output_dir, f"{names[i]}.png")
        else:
            file_path = os.path.join(output_dir, f"snapshot_{i}.png")

        # Save the image and store the path
        img_enhanced.save(file_path)
        snapshot_paths.append(file_path)

        pbar.update(1)

    return snapshot_paths


def generate_snapshots(
    file_path: str,
    output_dir: str = "../data/snapshots",
    resolution: List[int] = [512, 512],
    direction: str | Literal["common", "box", "omni"] = "common",
    preview: bool = False,
    **kwargs,
) -> List[str]:
    """Generates snapshots or previews of a 3D mesh from different camera orientations and distances.

    Args:
        file_path (str): Path to the 3D file (OBJ, STEP, or STL).
        output_dir (str, optional): The output directory to save the snapshots. Defaults to "../data/snapshots".
        resolution (List[int], optional): The resolution of the snapshots. Defaults to [512, 512].
        direction (str | Literal["common", "box", "omni"], optional): Direction or preset collection of directions: 'box', 'common', 'omni', or a comma-separated list of directions. Defaults to "common".
        preview (bool, optional): Whether to preview the scene interactively. Defaults to False.

    Returns:
        List[str]: A list of paths to the saved snapshot images.
    """
    if not file_path:
        raise ValueError("A file path must be provided.")

    # Infer file type from the extension
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".step":
        obj_path = os.path.dirname(file_path)
        obj_file = os.path.join(
            obj_path, os.path.basename(file_path).replace(".step", ".obj")
        )
        obj_file = convert.step2obj(file_path, obj_path)
    elif file_extension == ".obj":
        obj_file = file_path  # Directly use OBJ file
    elif file_extension == ".stl":
        obj_file = file_path  # Directly use STL file
    else:
        raise ValueError(
            "Unsupported file type. Only OBJ, STEP, and STL files are supported."
        )

    # Use base name without extension for output folder
    obj_name = os.path.splitext(os.path.basename(obj_file))[0]
    pic_path = os.path.join(output_dir, obj_name)

    mesh = trimesh.load_mesh(obj_file)
    logger.info(f"Loaded mesh from {obj_file}")

    if direction == "box":
        directions = angles.box_views
    elif direction == "common":
        directions = angles.common_views
    elif direction == "omni":
        directions = angles.omni_views
    else:
        # Assume it's a comma-separated list of directions
        directions = [d.strip() for d in direction.split(",") if d.strip()]

    # Validate directions
    for direction in directions:
        if direction.lower() not in angles.looking_from:
            logger.error(f"Invalid direction: {direction}")
            sys.exit(1)

    logger.info(f"Using directions: {directions}")

    if preview:
        camera_pose = get_camera_pose(direction)
        camera_distance = get_adaptive_camera_distance(mesh, 1.5)
        preview_scene_interactive(mesh, camera_pose, camera_distance)
        return []  # Return an empty list if previewing

    else:
        camera_poses = [get_camera_pose(direction) for direction in directions]
        camera_distances = [get_adaptive_camera_distance(mesh, 1.5)] * len(camera_poses)
        names = [f"snapshot_{direction}" for direction in directions]

        if contrast_factor := kwargs.get("contrast_factor", 1.2):
            logger.info(f"Using contrast factor: {contrast_factor}")
        # Capture snapshots and return the list of image paths
        return capture_snapshots(
            mesh,
            camera_poses,
            camera_distances,
            pic_path,
            names,
            resolution,
            contrast_factor=contrast_factor,
        )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--obj_file", type=str)
    group.add_argument("--step_file", type=str)
    group.add_argument("--stl_file", type=str)

    parser.add_argument("-o", "--output_dir", type=str, default="../data/snapshots")
    parser.add_argument("-r", "--resolution", type=int, nargs=2, default=[512, 512])
    parser.add_argument(
        "-d",
        "--direction",
        type=str,
        default="front",
        help="Direction or preset collection of directions: 'box', 'common', 'omni', or a comma-separated list of directions.",
    )
    parser.add_argument("-p", "--preview", action="store_true", default=False)

    args = parser.parse_args()

    generate_snapshots(
        obj_file=args.obj_file,
        step_file=args.step_file,
        stl_file=args.stl_file,
        output_dir=args.output_dir,
        resolution=args.resolution,
        direction=args.direction,
        preview=args.preview,
    )
