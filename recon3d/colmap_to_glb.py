import os
import trimesh
from trimesh import points

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DENSE_DIR = os.path.join(BASE_DIR, "colmap_work", "dense")

candidate_files = [
    os.path.join(DENSE_DIR, "mesh_poisson.ply"),
    os.path.join(DENSE_DIR, "mesh_delaunay.ply"),
    os.path.join(DENSE_DIR, "fused.ply"),
]

usable_mesh = None
used_source = None

for path in candidate_files:
    if not os.path.exists(path):
        continue

    print(f"Trying: {path}")
    obj = trimesh.load(path)

    print("  Loaded type:", type(obj))

    mesh = None

    # Case 1: already a mesh
    if isinstance(obj, trimesh.Trimesh):
        if len(obj.vertices) > 0:
            mesh = obj

    # Case 2: point cloud -> make convex hull mesh
    elif isinstance(obj, points.PointCloud):
        if len(obj.vertices) > 0:
            print("  Detected point cloud, building convex hull mesh...")
            hull = obj.convex_hull
            if hull is not None and len(hull.vertices) > 0:
                mesh = hull

    # Case 3: scene -> merge geometries
    elif isinstance(obj, trimesh.Scene):
        if obj.geometry:
            print("  Scene geometries:", list(obj.geometry.keys()))
            merged = trimesh.util.concatenate(
                [g for g in obj.geometry.values() if len(g.vertices) > 0]
            )
            if merged is not None and len(merged.vertices) > 0:
                mesh = merged

    if mesh is not None and len(mesh.vertices) > 0:
        usable_mesh = mesh
        used_source = path
        break

if usable_mesh is None:
    raise ValueError("No usable mesh found: all PLY files are empty or invalid.")

print(f"Using mesh from: {used_source}")
output_glb = os.path.join(BASE_DIR, "colmap_work", "colmap_room.glb")
usable_mesh.export(output_glb)
print(f"Saved GLB to: {output_glb}")
