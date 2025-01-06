import argparse
import io
import logging
import os
import sys
from typing import List, Literal, Optional

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
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
    scale_factor: float = 1,
    fov: float = 30,  # Field of view in degrees
) -> float:
    """Calculates a suitable camera distance based on the mesh's bounding box.

    Args:
        mesh (trimesh.Trimesh): The mesh for which to calculate the camera distance.
        scale_factor (float, optional): Scaling factor for the camera distance. Defaults to 1.
        fov (float, optional): Field of view in degrees. Defaults to 30.

    Returns:
        float: The calculated camera distance.
    """
    bounding_box = mesh.bounding_box.extents
    logger.debug(f"Bounding box: {bounding_box}")

    diagonal_length = np.linalg.norm(bounding_box)  # Diagonal of bounding box
    logger.debug(f"Diagonal length: {diagonal_length}")

    # Calculate the required distance based on the diagonal length and FoV
    # The formula ensures that the entire bounding box fits within the camera's view
    # The factor 1.2 is a safety margin to ensure the entire object is visible
    required_distance = (diagonal_length / 2) / np.tan(np.radians(fov / 2)) * 1.2

    # Scale the distance by the provided scale_factor
    camera_distance = scale_factor * required_distance

    logger.debug(f"Adaptive camera distance: {camera_distance}")
    return camera_distance


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
        fov=(30, 30),  # Adjust FoV
    )
    scene.camera.orthographic = True  # Enable orthographic view

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
    font_path: Optional[str] = None,  # Path to a .ttf font file
    font_size: int = 20,  # Font size for the caption
) -> List[str]:
    """Captures snapshots of the mesh from different camera orientations and distances.

    Args:
        mesh (trimesh.Trimesh): The mesh to capture snapshots of.
        camera_orientations (np.ndarray): List of camera orientations (Euler angles).
        camera_distances (List[float]): List of camera distances.
        output_dir (str): The output directory to save the snapshots.
        names (Optional[List[str]], optional): List of names for the snapshots. Defaults to None.
        resolution (List[int], optional): The resolution of the snapshots. Defaults to [512, 512].
        contrast_factor (float, optional): Contrast factor for image enhancement. Defaults to 1.2.
        font_path (Optional[str], optional): Path to a .ttf font file. Defaults to None.
        font_size (int, optional): Font size for the caption. Defaults to 20.

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

    # Load font if provided
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        font = ImageFont.load_default()

    pbar = tqdm(total=len(camera_orientations))
    for i, cocd in enumerate(zip(camera_orientations, camera_distances)):
        # Set the camera parameters using set_camera
        co, cd = cocd
        scene.set_camera(
            angles=co,
            distance=cd,
            center=mesh.centroid,
            fov=(30, 30),  # Field of view in degrees (horizontal, vertical)
        )
        scene.camera.orthographic = True

        # save image, 720p
        png = scene.save_image(resolution=resolution, visible=False)

        # Convert RGBA to RGB
        img = Image.open(io.BytesIO(png))
        img_rgb = rgba_to_rgb(img)

        # Enhance color contrast
        img_enhanced = enhance_color_contrast(img_rgb, contrast_factor)

        # Add caption text
        draw = ImageDraw.Draw(img_enhanced)
        if names is not None:
            caption = f"{names[i]}"
        else:
            caption = f"Snapshot {i}"
        # Use textbbox to get the bounding box of the text
        bbox = draw.textbbox((0, 0), caption, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        margin = 10  # Margin from the top-right corner
        position = (img_enhanced.width - text_width - margin, margin)
        draw.text(position, caption, font=font, fill="black")

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


# Add this new function
def recenter_and_reaxis_mesh_in_scene(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """
    Reaxis and recenter the mesh using the `recenter_and_reaxis_mesh` function.

    Args:
        mesh (trimesh.Trimesh): The input mesh.

    Returns:
        trimesh.Trimesh: The transformed mesh.
    """
    transformed_mesh, _ = convert.recenter_and_reaxis_mesh(mesh)
    return transformed_mesh


# Modify the generate_snapshots function to include the reaxis_gravity parameter
def generate_snapshots(
    file_path: str,
    output_dir: str = "../data/snapshots",
    resolution: List[int] = [512, 512],
    direction: str | Literal["common", "box", "omni"] = "common",
    preview: bool = False,
    mesh_color: Optional[List[int]] = None,  # Add a color parameter
    reaxis_gravity: bool = False,  # New parameter to control reaxis and recenter
    **kwargs,
) -> List[str]:
    """Generates snapshots or previews of a 3D mesh from different camera orientations and distances.

    Args:
        file_path (str): Path to the 3D file (OBJ, STEP, or STL).
        output_dir (str, optional): The output directory to save the snapshots. Defaults to "../data/snapshots".
        resolution (List[int], optional): The resolution of the snapshots. Defaults to [512, 512].
        direction (str | Literal["common", "box", "omni"], optional): Direction or preset collection of directions: 'box', 'common', 'omni', or a comma-separated list of directions. Defaults to "common".
        preview (bool, optional): Whether to preview the scene interactively. Defaults to False.
        mesh_color (Optional[List[int]], optional): The color to apply to the mesh in RGB format (e.g., [255, 0, 0] for red). Defaults to None.
        reaxis_gravity (bool, optional): Whether to reaxis and recenter the mesh before capturing snapshots. Defaults to False.

    Returns:
        List[str]: A list of paths to the saved snapshot images.
    """
    if not file_path:
        raise ValueError("A file path must be provided.")
    # create output path if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

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

    # Reaxis and recenter the mesh if requested
    if reaxis_gravity:
        mesh = recenter_and_reaxis_mesh_in_scene(mesh)
        logger.info("Mesh reoriented and recentered with gravity.")

    # Set the mesh color if provided
    if mesh_color is not None:
        mesh.visual.vertex_colors = mesh_color  # Set vertex colors
        logger.info(f"Mesh color set to {mesh_color}")

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
        camera_distance = get_adaptive_camera_distance(mesh, scale_factor=1, fov=30)
        preview_scene_interactive(mesh, camera_pose, camera_distance)
        return []  # Return an empty list if previewing

    else:
        camera_poses = [get_camera_pose(direction) for direction in directions]
        camera_distances = [
            get_adaptive_camera_distance(mesh, scale_factor=1, fov=30)
        ] * len(camera_poses)
        names = [f"snapshot_{direction}" for direction in directions]

        if contrast_factor := kwargs.get("contrast_factor", 1.2):
            logger.info(f"Using contrast factor: {contrast_factor}")
        if font_size := kwargs.get("font_size", 0.05 * resolution[0]):
            logger.info(f"Using font size: {font_size}")
        # Capture snapshots and return the list of image paths
        return capture_snapshots(
            mesh,
            camera_poses,
            camera_distances,
            pic_path,
            names,
            resolution,
            contrast_factor=contrast_factor,
            font_size=font_size,
        )


# Update the main function to include the reaxis_gravity argument
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate snapshots or previews of a 3D mesh from different camera orientations and distances."
    )

    # Mutually exclusive group for file input
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--obj_file", type=str, help="Path to the OBJ file.")
    group.add_argument("--step_file", type=str, help="Path to the STEP file.")
    group.add_argument("--stl_file", type=str, help="Path to the STL file.")

    # Optional arguments
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        default="../data/snapshots",
        help="Output directory to save the snapshots.",
    )
    parser.add_argument(
        "-r",
        "--resolution",
        type=int,
        nargs=2,
        default=[512, 512],
        help="Resolution of the snapshots (width, height).",
    )
    parser.add_argument(
        "-d",
        "--direction",
        type=str,
        default="common",
        help="Direction or preset collection of directions: 'box', 'common', 'omni', or a comma-separated list of directions.",
    )
    parser.add_argument(
        "-p",
        "--preview",
        action="store_true",
        default=False,
        help="Preview the scene interactively.",
    )
    parser.add_argument(
        "--reaxis_gravity",
        action="store_true",
        default=False,
        help="Reaxis and recenter the mesh with gravity before capturing snapshots.",
    )

    args = parser.parse_args()

    # Determine which file path to use
    if args.obj_file:
        file_path = args.obj_file
    elif args.step_file:
        file_path = args.step_file
    elif args.stl_file:
        file_path = args.stl_file
    else:
        raise ValueError("No file path provided.")

    try:
        # Generate snapshots or preview
        snapshot_paths = generate_snapshots(
            file_path=file_path,
            output_dir=args.output_dir,
            resolution=args.resolution,
            direction=args.direction,
            preview=args.preview,
            mesh_color=(0, 102, 204),
            reaxis_gravity=args.reaxis_gravity,  # Pass the reaxis_gravity argument
        )

        if not args.preview:
            print(f"Snapshots saved to: {args.output_dir}")
            for path in snapshot_paths:
                print(f" - {path}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)
