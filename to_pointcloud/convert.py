import os
from typing import Tuple

import numpy as np
import trimesh
from plyfile import PlyData, PlyElement

# TODO: should be adaptive to the size of the mesh
POINTCLOUD_N_POINTS = 8096 * 3


def calculate_centroid(mesh: trimesh.Trimesh) -> np.ndarray:
    # calculate the centroid of the mesh (regardless of actual mass)
    centroid = np.mean(mesh.vertices, axis=0)
    return centroid


def calculate_principal_axes(mesh) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate the principal axes of the mesh and
    return the descending ordered axes and eigenvalues in
    """
    # calculate the inertia tensor of the mesh
    inertia_tensor = mesh.moment_inertia

    # calculate the principal axes of the mesh
    eigenvalues, eigenvectors = np.linalg.eig(inertia_tensor)
    principal_axes = eigenvectors.T

    # reorder the principal axes based on the eigenvalues
    principal_axes = principal_axes[np.argsort(eigenvalues)[::-1]]
    eigenvalues = eigenvalues[np.argsort(eigenvalues)[::-1]]

    return (principal_axes, eigenvalues)


def recenter_and_reaxis_mesh(
    mesh: trimesh.Trimesh,
) -> Tuple[trimesh.Trimesh, np.ndarray]:
    # calculate the centroid and principal axes of the mesh
    centroid = calculate_centroid(mesh)
    principal_axes, _ = calculate_principal_axes(mesh)

    # calculate translation matrix
    translation_matrix = np.eye(4)
    translation_matrix[:3, 3] = -centroid

    # calculate rotation matrix
    rotation_matrix = np.eye(4)
    rotation_matrix[:3, :3] = principal_axes.T

    # merge translation and rotation matrix
    transformation_matrix = np.dot(rotation_matrix, translation_matrix)

    # transform the mesh
    transformed_mesh = mesh.copy()
    transformed_mesh.apply_transform(transformation_matrix)

    return transformed_mesh, transformation_matrix


def create_mesh_from_step(step_path: str):
    mesh = trimesh.Trimesh(
        **trimesh.interfaces.gmsh.load_gmsh(
            file_name=step_path,
            gmsh_args=[
                ("Mesh.Algorithm", 1),  # Different algorithm types, check them out
                (
                    "Mesh.CharacteristicLengthFromCurvature",
                    50,
                ),  # Tuning the smoothness, + smoothness = + time
                ("General.NumThreads", 10),  # Multithreading capability
                ("Mesh.MinimumCirclePoints", 32),
            ],
        )
    )

    return mesh


def step2obj(step_path: str, out_path: str):

    m = create_mesh_from_step(step_path)

    # recenter and reaxis the mesh
    m2, _ = recenter_and_reaxis_mesh(m)

    # save the mesh to obj file
    outfile = os.path.join(
        out_path, os.path.basename(step_path).replace(".step", ".obj")
    )
    m.export(outfile, file_type="obj")
    outfile2 = os.path.join(
        out_path, os.path.basename(step_path).replace(".step", "_recentered.obj")
    )
    m2.export(outfile2, file_type="obj")


def write_ply(points, filename, text=False):
    """input: Nx3, write points to filename as PLY format."""
    points = [
        (
            points[i, 0],
            points[i, 1],
            points[i, 2],
            254,
            254,
            254,
        )  # give default white color (254, 254, 254) to all points
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


def obj2pc(obj_path: str, out_path: str):
    # obj_path, out_path
    m = trimesh.load_mesh(obj_path)
    path = os.path.join(out_path, os.path.basename(obj_path).replace(".obj", ".ply"))
    pc = trimesh.PointCloud(m.sample(POINTCLOUD_N_POINTS))
    pc.vertices[:, [2, 1]] = pc.vertices[:, [1, 2]]
    pc = pc.vertices
    # swap y and z axis
    write_ply(pc, path)


if __name__ == "__main__":
    # Example usage
    step_file = "../data/00106_index_1.step"  # Replace with your STEP file path
    obj_path = os.path.dirname(step_file)
    obj_file = os.path.join(
        obj_path, os.path.basename(step_file).replace(".step", ".obj")
    )

    step2obj(step_file, obj_path)
    obj2pc(obj_file, obj_path)
