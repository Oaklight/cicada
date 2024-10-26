import logging
import os
from typing import Tuple

import numpy as np
import trimesh
from plyfile import PlyData, PlyElement

# TODO: should be adaptive to the size of the mesh
POINTCLOUD_N_POINTS = 8096 * 3
DEFAULT_RGB = (0, 191, 255)
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


def step2obj(step_path: str, out_path: str):

    m = step2mesh(step_path)

    # recenter and reaxis the mesh
    m, _ = recenter_and_reaxis_mesh(m)

    # save the mesh to obj file
    outfile = os.path.join(
        out_path, os.path.basename(step_path).replace(".step", ".obj")
    )
    m.export(outfile, file_type="obj")
    logger.info(f"[step2obj] mesh saved to {outfile}")


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


def obj2pc(obj_path: str, out_path: str):
    # obj_path, out_path
    m = trimesh.load_mesh(obj_path)
    logger.debug(
        f"[obj2pc] mesh loaded from {obj_path} with {m.vertices.shape[0]} vertices"
    )

    path = os.path.join(out_path, os.path.basename(obj_path).replace(".obj", ".ply"))
    pc = trimesh.PointCloud(m.sample(POINTCLOUD_N_POINTS))
    logger.debug(f"[obj2pc] convert to pointcloud, with {pc.vertices.shape[0]} points")

    pc = pc.vertices
    write_ply(pc, path)
    logger.info(f"[obj2pc] pointcloud saved to {path}")


if __name__ == "__main__":
    # Example usage
    import argparse

    parser = argparse.ArgumentParser()
    # either of these two is required, but exclusive
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--step_file", type=str)
    group.add_argument("--obj_file", type=str)
    args = parser.parse_args()

    if args.step_file:
        step_file = args.step_file
        out_path = os.path.dirname(step_file)
        obj_file = os.path.join(
            out_path, os.path.basename(step_file).replace(".step", ".obj")
        )

        step2obj(step_file, out_path)
        obj2pc(obj_file, out_path)
    elif args.obj_file:
        obj_file = args.obj_file
        out_path = os.path.dirname(obj_file)
        pc_file = os.path.join(
            out_path, os.path.basename(obj_file).replace(".obj", ".ply")
        )

        obj2pc(obj_file, out_path)
