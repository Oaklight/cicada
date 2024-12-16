import argparse
import logging
import os
from typing import Tuple

import numpy as np
import trimesh
from plyfile import PlyData, PlyElement

# TODO: should be adaptive to the size of the mesh
POINTCLOUD_N_POINTS = 8096 * 3
DEFAULT_RGB = (88, 88, 88)
LOG_LEVEL = "DEBUG"


logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.addHandler(logging.StreamHandler())


def recenter_and_reaxis_mesh(
    mesh: trimesh.Trimesh,
) -> Tuple[trimesh.Trimesh, np.ndarray]:
    # calculate the principal inertia transform
    transformation_matrix = mesh.principal_inertia_transform
    logger.debug(f"[Transform] principal inertia transform: \n{transformation_matrix}")

    # transform the mesh
    transformed_mesh = mesh.copy()
    transformed_mesh.apply_transform(transformation_matrix)
    logger.debug(f"[Transform] mesh transformed with principal inertia transform")

    return transformed_mesh, transformation_matrix


def step2mesh(step_path: str):
    """
    According to https://gmsh.info/doc/texinfo/gmsh.html#Mesh-options,
    for the fastest 2D meshing, use Algorithm 3 (Initial Mesh Only) or Algorithm 5 (Delaunay).
    for the fastest 3D meshing, use Algorithm 1 (Delaunay) or Algorithm 3 (Initial Mesh Only).
    """
    mesh = trimesh.Trimesh(
        **trimesh.interfaces.gmsh.load_gmsh(
            file_name=step_path,
            gmsh_args=[
                ("Mesh.Algorithm", 5),  # Different algorithm types, check them out
                ("Mesh.Algorithm3D", 1),  # Different algorithm types, check them out
                (
                    "Mesh.CharacteristicLengthFromCurvature",
                    50,
                ),  # Tuning the smoothness, + smoothness = + time
                ("General.NumThreads", 10),  # Multithreading capability
                ("Mesh.MinimumCirclePoints", 32),
            ],
        )
    )
    logger.debug(  # add function name in the beginning []
        # f"[{}] <mesh> from {step_path} with {mesh.vertices.shape[0]} vertices"
        f"[step2mesh] mesh loaded from {step_path}, {mesh.vertices.shape[0]} vertices"
    )

    return mesh


def step2obj(step_path: str, out_path: str) -> str:

    m = step2mesh(step_path)

    # recenter and reaxis the mesh
    m, _ = recenter_and_reaxis_mesh(m)

    # save the mesh to obj file
    obj_path = os.path.join(
        out_path, os.path.basename(step_path).replace(".step", ".obj")
    )
    m.export(obj_path, file_type="obj")
    logger.info(f"[step2obj] mesh saved to {obj_path}")

    return obj_path


def step2stl(step_path: str, out_path: str) -> str:
    """Convert STEP file to STL format."""
    mesh = step2mesh(step_path)
    stl_path = os.path.join(
        out_path, os.path.basename(step_path).replace(".step", ".stl")
    )
    mesh.export(stl_path, file_type="stl")
    logger.info(f"STEP file converted to STL: {stl_path}")
    return stl_path


def stl2obj(stl_path: str, out_path: str) -> str:
    """Convert STL file to OBJ format."""
    mesh = trimesh.load_mesh(stl_path)
    obj_path = os.path.join(
        out_path, os.path.basename(stl_path).replace(".stl", ".obj")
    )
    mesh.export(obj_path, file_type="obj")
    logger.info(f"STL file converted to OBJ: {obj_path}")
    return obj_path


def obj2stl(obj_path: str, out_path: str) -> str:
    """Convert OBJ file to STL format."""
    mesh = trimesh.load_mesh(obj_path)
    stl_path = os.path.join(
        out_path, os.path.basename(obj_path).replace(".obj", ".stl")
    )
    mesh.export(stl_path, file_type="stl")
    logger.info(f"OBJ file converted to STL: {stl_path}")
    return stl_path


def write_ply(points, filename, text=False, default_rgb=DEFAULT_RGB):
    """input: Nx3, write points to filename as PLY format."""
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
    # obj_path, out_path
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
    """Convert STL file to point cloud (PLY format)."""
    mesh = trimesh.load_mesh(stl_path)
    pc_path = os.path.join(out_path, os.path.basename(stl_path).replace(".stl", ".ply"))
    pc = trimesh.PointCloud(mesh.sample(POINTCLOUD_N_POINTS))
    write_ply(pc.vertices, pc_path)
    logger.info(f"STL file converted to point cloud: {pc_path}")
    return pc_path


if __name__ == "__main__":
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

    args = parser.parse_args()

    if args.obj_file:
        obj_file = args.obj_file
        out_path = os.path.dirname(obj_file)
        if args.convert_obj2pc:
            obj2pc(obj_file, out_path)
        elif args.convert_obj2stl:
            obj2stl(obj_file, out_path)
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
        else:
            logger.error("No valid action selected for STL file.")
