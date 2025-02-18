import logging
import os
from typing import Tuple

import numpy as np
import trimesh
from plyfile import PlyData, PlyElement

# TODO: should be adaptive to the size of the mesh
POINTCLOUD_N_POINTS = 8096 * 3
DEFAULT_RGB = (88, 88, 88)


logger = logging.getLogger(__name__)


def recenter_and_reaxis_mesh(
    mesh: trimesh.Trimesh,
) -> Tuple[trimesh.Trimesh, np.ndarray]:
    """
    Recenter and reaxis the mesh using its principal inertia transform,
    ensuring that the mesh is oriented such that the gravity vector (negative Z-axis)
    aligns with the principal axis corresponding to the object's "up" direction.

    Args:
        mesh (trimesh.Trimesh): The input mesh.

    Returns:
        Tuple[trimesh.Trimesh, np.ndarray]: The transformed mesh and the transformation matrix.
    """
    # Get the principal inertia transform
    transformation_matrix = mesh.principal_inertia_transform
    logger.debug(f"[Transform] principal inertia transform: \n{transformation_matrix}")

    # Apply the transformation to the mesh
    transformed_mesh = mesh.copy()
    transformed_mesh.apply_transform(transformation_matrix)

    # Ensure that the mesh is oriented such that the gravity vector (negative Z-axis)
    # aligns with the principal axis corresponding to the object's "up" direction.
    # We assume that the principal axis corresponding to the smallest moment of inertia
    # is the "up" direction.
    moments_of_inertia = transformed_mesh.moment_inertia
    principal_axes = np.diag(moments_of_inertia)

    # Find the index of the smallest moment of inertia (assumed to be the "up" direction)
    up_axis_index = np.argmin(principal_axes)

    # Adjusted rotation logic to align the object's "up" direction with +Y (trimesh's upward direction)
    # 调整旋转逻辑，将物体的“上”方向对齐到+Y轴（trimesh的垂直正方向）
    if up_axis_index == 0:
        # X-axis -> Rotate 90° around Z to align X to Y
        rotation_matrix = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    elif up_axis_index == 2:
        # Z-axis -> Rotate -90° around X to align Z to Y
        rotation_matrix = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
    else:
        # Y-axis (no rotation needed)
        rotation_matrix = np.eye(3)

    # Convert the 3x3 rotation matrix to a 4x4 transformation matrix
    rotation_matrix_4x4 = np.eye(4)
    rotation_matrix_4x4[:3, :3] = rotation_matrix

    # Apply the rotation to the transformed mesh
    transformed_mesh.apply_transform(rotation_matrix_4x4)

    # Combine the original transformation matrix with the rotation matrix
    combined_transform = np.dot(rotation_matrix_4x4, transformation_matrix)
    transformation_matrix = combined_transform

    logger.debug(
        f"[Transform] mesh transformed with principal inertia transform and aligned with gravity"
    )
    return transformed_mesh, transformation_matrix


def step2mesh(step_path: str) -> trimesh.Trimesh:
    """
    Convert a STEP file to a mesh using GMSH.

    Args:
        step_path (str): Path to the STEP file.

    Returns:
        trimesh.Trimesh: The generated mesh.
    """
    mesh = trimesh.Trimesh(
        **trimesh.interfaces.gmsh.load_gmsh(
            file_name=step_path,
            gmsh_args=[
                ("Mesh.Algorithm", 5),
                ("Mesh.Algorithm3D", 1),
                ("Mesh.CharacteristicLengthFromCurvature", 50),
                ("General.NumThreads", 10),
                ("Mesh.MinimumCirclePoints", 32),
            ],
        )
    )
    logger.debug(
        f"[step2mesh] mesh loaded from {step_path}, {mesh.vertices.shape[0]} vertices"
    )
    return mesh


def step2obj(step_path: str, out_path: str) -> str:
    """
    Convert a STEP file to an OBJ file.

    Args:
        step_path (str): Path to the STEP file.
        out_path (str): Directory to save the OBJ file.

    Returns:
        str: Path to the saved OBJ file.
    """
    m = step2mesh(step_path)
    m, _ = recenter_and_reaxis_mesh(m)

    obj_path = os.path.join(
        out_path, os.path.basename(step_path).replace(".step", ".obj")
    )
    m.export(obj_path, file_type="obj")
    logger.info(f"[step2obj] mesh saved to {obj_path}")

    return obj_path


def step2stl(step_path: str, out_path: str) -> str:
    """
    Convert a STEP file to an STL file.

    Args:
        step_path (str): Path to the STEP file.
        out_path (str): Directory to save the STL file.

    Returns:
        str: Path to the saved STL file.
    """
    mesh = step2mesh(step_path)
    stl_path = os.path.join(
        out_path, os.path.basename(step_path).replace(".step", ".stl")
    )
    mesh.export(stl_path, file_type="stl")
    logger.info(f"STEP file converted to STL: {stl_path}")

    return stl_path


def stl2obj(stl_path: str, out_path: str) -> str:
    """
    Convert an STL file to an OBJ file.

    Args:
        stl_path (str): Path to the STL file.
        out_path (str): Directory to save the OBJ file.

    Returns:
        str: Path to the saved OBJ file.
    """
    mesh = trimesh.load_mesh(stl_path)
    obj_path = os.path.join(
        out_path, os.path.basename(stl_path).replace(".stl", ".obj")
    )
    mesh.export(obj_path, file_type="obj")
    logger.info(f"STL file converted to OBJ: {obj_path}")

    return obj_path


def obj2stl(obj_path: str, out_path: str) -> str:
    """
    Convert an OBJ file to an STL file.

    Args:
        obj_path (str): Path to the OBJ file.
        out_path (str): Directory to save the STL file.

    Returns:
        str: Path to the saved STL file.
    """
    mesh = trimesh.load_mesh(obj_path)
    stl_path = os.path.join(
        out_path, os.path.basename(obj_path).replace(".obj", ".stl")
    )
    mesh.export(stl_path, file_type="stl")
    logger.info(f"OBJ file converted to STL: {stl_path}")

    return stl_path


def write_ply(
    points: np.ndarray,
    filename: str,
    text: bool = False,
    default_rgb: Tuple[int, int, int] = DEFAULT_RGB,
) -> None:
    """
    Write points to a PLY file.

    Args:
        points (np.ndarray): Nx3 array of points.
        filename (str): Path to save the PLY file.
        text (bool): Whether to save the PLY file in text format.
        default_rgb (Tuple[int, int, int]): Default RGB color for the points.
    """
    points = [
        (
            points[i, 0],
            points[i, 1],
            points[i, 2],
            default_rgb[0],
            default_rgb[1],
            default_rgb[2],
        )
        for i in range(points.shape[0])
    ]
    vertex = np.array(
        points,
        dtype=[
            ("x", "f4"),
            ("y", "f4"),
            ("z", "f4"),
            ("red", "u1"),
            ("green", "u1"),
            ("blue", "u1"),
        ],
    )
    el = PlyElement.describe(vertex, "vertex", comments=["vertices"])
    with open(filename, mode="wb") as f:
        PlyData([el], text=text).write(f)
    logger.debug(f"[write_ply] saved to {filename}, with default rgb is {default_rgb}")


def obj2pc(obj_path: str, out_path: str) -> str:
    """
    Convert an OBJ file to a point cloud (PLY format).

    Args:
        obj_path (str): Path to the OBJ file.
        out_path (str): Directory to save the PLY file.

    Returns:
        str: Path to the saved PLY file.
    """
    m = trimesh.load_mesh(obj_path)
    logger.debug(
        f"[obj2pc] mesh loaded from {obj_path} with {m.vertices.shape[0]} vertices"
    )
    pc_path = os.path.join(out_path, os.path.basename(obj_path).replace(".obj", ".ply"))
    pc = trimesh.PointCloud(m.sample(POINTCLOUD_N_POINTS))
    logger.debug(f"[obj2pc] convert to pointcloud, with {pc.vertices.shape[0]} points")

    pc = pc.vertices
    write_ply(pc, pc_path)
    logger.info(f"[obj2pc] pointcloud saved to {pc_path}")

    return pc_path


def stl2pc(stl_path: str, out_path: str) -> str:
    """
    Convert an STL file to a point cloud (PLY format).

    Args:
        stl_path (str): Path to the STL file.
        out_path (str): Directory to save the PLY file.

    Returns:
        str: Path to the saved PLY file.
    """
    mesh = trimesh.load_mesh(stl_path)
    pc_path = os.path.join(out_path, os.path.basename(stl_path).replace(".stl", ".ply"))
    pc = trimesh.PointCloud(mesh.sample(POINTCLOUD_N_POINTS))
    write_ply(pc.vertices, pc_path)
    logger.info(f"STL file converted to point cloud: {pc_path}")

    return pc_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--obj_file", type=str)
    group.add_argument("--step_file", type=str)
    group.add_argument("--stl_file", type=str)

    group_action = parser.add_mutually_exclusive_group(required=True)
    group_action.add_argument("--convert_step2obj", action="store_true")
    group_action.add_argument("--convert_obj2pc", action="store_true")
    group_action.add_argument("--convert_step2stl", action="store_true")
    group_action.add_argument("--convert_obj2stl", action="store_true")
    group_action.add_argument("--convert_stl2obj", action="store_true")
    group_action.add_argument("--convert_stl2pc", action="store_true")
    group_action.add_argument(
        "--reaxis_gravity",
        action="store_true",
        help="Recenter and reaxis the mesh to align with gravity.",
    )

    args = parser.parse_args()

    if args.obj_file:
        obj_file = args.obj_file
        out_path = os.path.dirname(obj_file)
        if args.convert_obj2pc:
            obj2pc(obj_file, out_path)
        elif args.convert_obj2stl:
            obj2stl(obj_file, out_path)
        elif args.reaxis_gravity:
            mesh = trimesh.load_mesh(obj_file)
            transformed_mesh, _ = recenter_and_reaxis_mesh(mesh)
            transformed_mesh.export(obj_file, file_type="obj")
            logger.info(f"Mesh reoriented with gravity and saved to {obj_file}")
        else:
            logger.error("No valid action selected for OBJ file.")
    elif args.step_file:
        step_file = args.step_file
        out_path = os.path.dirname(step_file)
        if args.convert_step2obj:
            step2obj(step_file, out_path)
        elif args.convert_step2stl:
            step2stl(step_file, out_path)
        else:
            logger.error("No valid action selected for STEP file.")
    elif args.stl_file:
        stl_file = args.stl_file
        out_path = os.path.dirname(stl_file)
        if args.convert_stl2obj:
            stl2obj(stl_file, out_path)
        elif args.convert_stl2pc:
            stl2pc(stl_file, out_path)
        elif args.reaxis_gravity:
            mesh = trimesh.load_mesh(stl_file)
            transformed_mesh, _ = recenter_and_reaxis_mesh(mesh)
            transformed_mesh.export(stl_file, file_type="stl")
            logger.info(f"Mesh reoriented with gravity and saved to {stl_file}")
        else:
            logger.error("No valid action selected for STL file.")
