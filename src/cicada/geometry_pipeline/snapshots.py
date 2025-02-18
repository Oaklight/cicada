import io
import logging
import os
import sys
from typing import List, Literal, Optional

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from tqdm import tqdm
from trimesh.viewer import SceneViewer

from cicada.geometry_pipeline import angles, convert


logger = logging.getLogger(__name__)


def get_adaptive_camera_distance(
    mesh: trimesh.Trimesh,
    scale_factor: float = 1,
    fov: float = 30,
) -> float:
    """Calculate a suitable camera distance based on the mesh's bounding box.

    :param mesh: The mesh for which to calculate the camera distance.
    :type mesh: trimesh.Trimesh
    :param scale_factor: Scaling factor for the camera distance, defaults to 1.
    :type scale_factor: float, optional
    :param fov: Field of view in degrees, defaults to 30.
    :type fov: float, optional
    :return: The calculated camera distance.
    :rtype: float
    """
    bounding_box = mesh.bounding_box.extents
    logger.debug(f"Bounding box: {bounding_box}")

    diagonal_length = np.linalg.norm(bounding_box)
    logger.debug(f"Diagonal length: {diagonal_length}")

    required_distance = (diagonal_length / 2) / np.tan(np.radians(fov / 2)) * 1.2
    camera_distance = scale_factor * required_distance

    logger.debug(f"Adaptive camera distance: {camera_distance}")
    return camera_distance


def get_camera_pose(
    looking_from_direction: str = "near",
) -> np.ndarray:
    """Retrieve the camera pose (Euler angles) for a given direction.

    :param looking_from_direction: The direction from which the camera is looking, defaults to "near".
    :type looking_from_direction: str, optional
    :return: The Euler angles representing the camera pose.
    :rtype: np.ndarray
    """
    euler_angles = angles.looking_from.get(looking_from_direction.lower())
    return euler_angles


def preview_scene_interactive(
    mesh: trimesh.Trimesh, camera_orientation: np.ndarray, camera_distance: float
) -> SceneViewer:
    """Create an interactive scene preview using trimesh.SceneViewer.

    :param mesh: The mesh to be displayed in the scene.
    :type mesh: trimesh.Trimesh
    :param camera_orientation: The Euler angles for the camera orientation.
    :type camera_orientation: np.ndarray
    :param camera_distance: The distance of the camera from the mesh.
    :type camera_distance: float
    :return: The SceneViewer object.
    :rtype: SceneViewer
    """
    scene = trimesh.Scene()
    scene.add_geometry(mesh)

    light = trimesh.scene.lighting.autolight(scene)
    scene.add_geometry(light)

    scene.set_camera(
        angles=camera_orientation,
        distance=camera_distance,
        center=mesh.centroid,
        fov=(30, 30),
    )
    scene.camera.orthographic = True

    logger.debug(f"Camera position: \n{scene.camera_transform}")
    logger.debug(f"Camera K: \n{scene.camera.K}")
    logger.debug(f"centroid: \n{mesh.centroid}")

    viewer = scene.show()

    return viewer


def rgba_to_rgb(rgba_image: Image.Image) -> Image.Image:
    """Convert an RGBA image to RGB.

    :param rgba_image: The RGBA image to convert.
    :type rgba_image: Image.Image
    :return: The converted RGB image.
    :rtype: Image.Image
    """
    return rgba_image.convert("RGB")


def enhance_color_contrast(image: Image.Image, factor: float = 1.2) -> Image.Image:
    """Enhance the color contrast of the image.

    :param image: The image to enhance.
    :type image: Image.Image
    :param factor: The contrast enhancement factor, defaults to 1.2.
    :type factor: float, optional
    :return: The enhanced image.
    :rtype: Image.Image
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
    font_path: Optional[str] = None,
    font_size: int = 20,
) -> List[str]:
    """Capture snapshots of the mesh from different camera orientations and distances.

    :param mesh: The mesh to capture snapshots of.
    :type mesh: trimesh.Trimesh
    :param camera_orientations: List of camera orientations (Euler angles).
    :type camera_orientations: np.ndarray
    :param camera_distances: List of camera distances.
    :type camera_distances: List[float]
    :param output_dir: The output directory to save the snapshots.
    :type output_dir: str
    :param names: List of names for the snapshots, defaults to None.
    :type names: Optional[List[str]], optional
    :param resolution: The resolution of the snapshots, defaults to [512, 512].
    :type resolution: List[int], optional
    :param contrast_factor: Contrast factor for image enhancement, defaults to 1.2.
    :type contrast_factor: float, optional
    :param font_path: Path to a .ttf font file, defaults to None.
    :type font_path: Optional[str], optional
    :param font_size: Font size for the caption, defaults to 20.
    :type font_size: int, optional
    :return: A list of paths to the saved snapshot images.
    :rtype: List[str]
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    scene = trimesh.Scene()
    scene.add_geometry(mesh)

    light = trimesh.scene.lighting.autolight(scene)
    scene.add_geometry(light)

    snapshot_paths = []

    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        font = ImageFont.load_default()

    pbar = tqdm(total=len(camera_orientations))
    for i, cocd in enumerate(zip(camera_orientations, camera_distances)):
        co, cd = cocd
        scene.set_camera(
            angles=co,
            distance=cd,
            center=mesh.centroid,
            fov=(30, 30),
        )
        scene.camera.orthographic = True

        png = scene.save_image(resolution=resolution, visible=False)

        img = Image.open(io.BytesIO(png))
        img_rgb = rgba_to_rgb(img)

        img_enhanced = enhance_color_contrast(img_rgb, contrast_factor)

        draw = ImageDraw.Draw(img_enhanced)
        if names is not None:
            caption = f"{names[i]}"
        else:
            caption = f"Snapshot {i}"
        bbox = draw.textbbox((0, 0), caption, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        margin = 10
        position = (img_enhanced.width - text_width - margin, margin)
        draw.text(position, caption, font=font, fill="black")

        if names is not None:
            file_path = os.path.join(output_dir, f"{names[i]}.png")
        else:
            file_path = os.path.join(output_dir, f"snapshot_{i}.png")

        img_enhanced.save(file_path)
        snapshot_paths.append(file_path)

        pbar.update(1)

    return snapshot_paths


def preview_mesh_interactively(
    mesh: trimesh.Trimesh,
    direction: str = "front",
    reaxis_gravity: bool = False,
    mesh_color: Optional[List[int]] = None,
) -> SceneViewer:
    """Preview the mesh interactively using trimesh.SceneViewer.

    :param mesh: The mesh to preview.
    :type mesh: trimesh.Trimesh
    :param direction: The direction from which the camera is looking, defaults to "front".
    :type direction: str, optional
    :param reaxis_gravity: Whether to reaxis and recenter the mesh before previewing, defaults to False.
    :type reaxis_gravity: bool, optional
    :param mesh_color: The color to apply to the mesh in RGB format, defaults to None.
    :type mesh_color: Optional[List[int]], optional
    :return: The SceneViewer object.
    :rtype: SceneViewer
    """
    if reaxis_gravity:
        mesh, _ = convert.recenter_and_reaxis_mesh(mesh)
        logger.info("Mesh reoriented and recentered with gravity.")

    if mesh_color is not None:
        mesh.visual.vertex_colors = mesh_color
        logger.info(f"Mesh color set to {mesh_color}")

    camera_pose = get_camera_pose(direction)
    camera_distance = get_adaptive_camera_distance(mesh, scale_factor=1, fov=30)
    return preview_scene_interactive(mesh, camera_pose, camera_distance)


def generate_snapshots(
    file_path: str,
    output_dir: str = "../data/snapshots",
    resolution: List[int] = [512, 512],
    direction: str | Literal["common", "box", "omni"] = "common",
    preview: bool = False,
    mesh_color: List[int] = [0, 102, 204],
    reaxis_gravity: bool = False,
    **kwargs,
) -> List[str]:
    """Generate snapshots or previews of a 3D mesh from different camera orientations and distances.

    :param file_path: Path to the 3D file (OBJ, STEP, or STL).
    :type file_path: str
    :param output_dir: The output directory to save the snapshots, defaults to "../data/snapshots".
    :type output_dir: str, optional
    :param resolution: The resolution of the snapshots, defaults to [512, 512].
    :type resolution: List[int], optional
    :param direction: Direction or preset collection of directions: 'box', 'common', 'omni', or a comma-separated list of directions, defaults to "common".
    :type direction: str | Literal["common", "box", "omni"], optional
    :param preview: Whether to preview the scene interactively, defaults to False.
    :type preview: bool, optional
    :param mesh_color: The color to apply to the mesh in RGB format, defaults to None.
    :type mesh_color: Optional[List[int]], optional
    :param reaxis_gravity: Whether to reaxis and recenter the mesh before capturing snapshots, defaults to False.
    :type reaxis_gravity: bool, optional
    :return: A list of paths to the saved snapshot images.
    :rtype: List[str]
    """
    if not file_path:
        raise ValueError("A file path must be provided.")
    os.makedirs(output_dir, exist_ok=True)

    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".step":
        obj_path = os.path.dirname(file_path)
        obj_file = os.path.join(
            obj_path, os.path.basename(file_path).replace(".step", ".obj")
        )
        obj_file = convert.step2obj(file_path, obj_path)
    elif file_extension == ".obj":
        obj_file = file_path
    elif file_extension == ".stl":
        obj_file = file_path
    else:
        raise ValueError(
            "Unsupported file type. Only OBJ, STEP, and STL files are supported."
        )

    obj_name = os.path.splitext(os.path.basename(obj_file))[0]
    pic_path = os.path.join(output_dir, obj_name)

    mesh = trimesh.load_mesh(obj_file)
    logger.info(f"Loaded mesh from {obj_file}")

    if reaxis_gravity:
        mesh, _ = convert.recenter_and_reaxis_mesh(mesh)
        logger.info("Mesh reoriented and recentered with gravity.")

    if mesh_color is not None:
        mesh.visual.vertex_colors = mesh_color
        logger.info(f"Mesh color set to {mesh_color}")

    if direction == "box":
        directions = angles.box_views
    elif direction == "common":
        directions = angles.common_views
    elif direction == "omni":
        directions = angles.omni_views
    else:
        directions = [d.strip() for d in direction.split(",") if d.strip()]

    for direction in directions:
        if direction.lower() not in angles.looking_from:
            logger.error(f"Invalid direction: {direction}")
            sys.exit(1)

    logger.info(f"Using directions: {directions}")

    if preview:
        preview_mesh_interactively(mesh, direction, reaxis_gravity, mesh_color)
        return []
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


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Generate snapshots or previews of a 3D mesh from different camera orientations and distances."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--obj_file", type=str, help="Path to the OBJ file.")
    group.add_argument("--step_file", type=str, help="Path to the STEP file.")
    group.add_argument("--stl_file", type=str, help="Path to the STL file.")

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

    if args.obj_file:
        file_path = args.obj_file
    elif args.step_file:
        file_path = args.step_file
    elif args.stl_file:
        file_path = args.stl_file
    else:
        raise ValueError("No file path provided.")

    try:
        snapshot_paths = generate_snapshots(
            file_path=file_path,
            output_dir=args.output_dir,
            resolution=args.resolution,
            direction=args.direction,
            preview=args.preview,
            mesh_color=(0, 102, 204),  # blue
            reaxis_gravity=args.reaxis_gravity,
        )

        if not args.preview:
            print(f"Snapshots saved to: {args.output_dir}")
            for path in snapshot_paths:
                print(f" - {path}")

    except Exception as e:
        logger.error
