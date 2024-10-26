import logging
from multiprocessing import parent_process
import os, sys


import numpy as np
import pyrender
import trimesh

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from to_pointcloud import angles

LOG_LEVEL = "DEBUG"

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.addHandler(logging.StreamHandler())


def get_adaptive_camera_distance(
    mesh: trimesh.Trimesh,
    scale_factor=200,
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

    # Convert the camera orientation to Euler angles
    # r = scipy.spatial.transform.Rotation.from_matrix(camera_orientation)
    # euler_angles = r.as_euler("xyz", degrees=False)

    # Set the camera parameters using set_camera
    scene.set_camera(
        angles=camera_orientation,
        distance=camera_distance,
        center=mesh.centroid,
        fov=(60, 45),  # Field of view in degrees (horizontal, vertical)
    )

    logger.debug(f"Camera pose: \n{camera_pose}")
    logger.debug(f"Camera position: \n{scene.camera_transform}")
    logger.debug(f"Camera K: \n{scene.camera.K}")
    logger.debug(f"centroid: \n{mesh.centroid}")

    # Show the interactive viewer
    viewer = scene.show()



# Usage Example

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--step_file", type=str, default="../data/knife.step")
    parser.add_argument("-d", "--direction", type=str, default="front")
    args = parser.parse_args()

    obj_path = os.path.dirname(args.step_file)
    obj_file = os.path.join(
        obj_path, os.path.basename(args.step_file).replace(".step", ".obj")
    )

    mesh = trimesh.load_mesh(obj_file)
    pic_path = os.path.join(obj_path, "snapshots")

    camera_pose = get_camera_pose(args.direction)
    camera_distance = get_adaptive_camera_distance(mesh, 2)
    preview_scene_interactive(mesh, camera_pose, camera_distance)
