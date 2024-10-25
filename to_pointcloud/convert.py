import os
import numpy as np
import trimesh
from plyfile import PlyElement, PlyData

# TODO: should be adaptive to the size of the mesh
POINTCLOUD_N_POINTS = 8096 * 3


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

    outfile = os.path.join(
        out_path, os.path.basename(step_path).replace(".step", ".obj")
    )
    m.export(outfile, file_type="obj")


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
