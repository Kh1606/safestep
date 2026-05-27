import cv2
import os
from pathlib import Path

import torch
import numpy as np
from tqdm import tqdm

import open3d as o3d
import trimesh


# ---------- 1. FRAME EXTRACTION ----------

def extract_frames(video_path, out_dir, step=5):
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    i = 0
    saved = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if i % step == 0:
            out_path = os.path.join(out_dir, f"frame_{i:05d}.jpg")
            cv2.imwrite(out_path, frame)
            saved += 1
        i += 1

    cap.release()
    print(f"[Frames] Extracted {saved} frames to {out_dir}")


# ---------- 2. LOAD MiDaS DEPTH MODEL ----------

def load_midas(device="cuda"):
    model_type = "DPT_Large"  # you can switch to "DPT_Hybrid" (faster)
    midas = torch.hub.load("intel-isl/MiDaS", model_type)
    midas.to(device)
    midas.eval()

    transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
    if "DPT" in model_type:
        transform = transforms.dpt_transform
    else:
        transform = transforms.small_transform

    return midas, transform


def run_depth_on_frames(frames_dir, depth_dir, device="cuda"):
    os.makedirs(depth_dir, exist_ok=True)
    midas, transform = load_midas(device=device)

    frame_paths = sorted(Path(frames_dir).glob("*.jpg"))
    print(f"[Depth] Found {len(frame_paths)} frames")

    for p in tqdm(frame_paths, desc="Depth inference"):
        img = cv2.imread(str(p))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        input_batch = transform(img_rgb).to(device)

        with torch.no_grad():
            prediction = midas(input_batch)

            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img_rgb.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()

        depth = prediction.cpu().numpy()
        depth = depth - depth.min()
        depth = depth / (depth.max() + 1e-8)

        np.save(Path(depth_dir) / (p.stem + "_depth.npy"), depth)

    print(f"[Depth] Saved depth maps to {depth_dir}")


# ---------- 3. DEPTH -> POINT CLOUD ----------

def depth_to_point_cloud(rgb, depth, fx, fy, cx, cy, depth_scale=2.0):
    """
    Simple pinhole backprojection. depth is normalized [0,1].
    depth_scale controls "room thickness".
    """
    h, w = depth.shape
    depth_scaled = depth * depth_scale

    xs, ys = np.meshgrid(np.arange(w), np.arange(h))
    xs = xs.astype(np.float32)
    ys = ys.astype(np.float32)

    X = (xs - cx) / fx * depth_scaled
    Y = (ys - cy) / fy * depth_scaled
    Z = depth_scaled

    points = np.stack((X, -Y, -Z), axis=-1).reshape(-1, 3)   # flip axes a bit
    colors = rgb.reshape(-1, 3) / 255.0

    return points, colors


def build_point_cloud(frames_dir, depth_dir, out_ply):
    frame_paths = sorted(Path(frames_dir).glob("*.jpg"))
    if not frame_paths:
        print("[PointCloud] No frames found.")
        return

    # Take the middle frame only (best chance to see a clear view)
    mid_idx = len(frame_paths) // 2
    p = frame_paths[mid_idx]
    depth_path = Path(depth_dir) / (p.stem + "_depth.npy")

    if not depth_path.exists():
        print(f"[PointCloud] Depth file not found for {p.name}")
        return

    rgb = cv2.imread(str(p))
    rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
    depth = np.load(depth_path)

    h, w, _ = rgb.shape
    fx = fy = max(h, w)  # rough guess, ok for shape
    cx = w / 2.0
    cy = h / 2.0

    pts, cols = depth_to_point_cloud(rgb, depth, fx, fy, cx, cy)

    print(f"[PointCloud] Points from one frame: {pts.shape[0]}")

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts)
    pcd.colors = o3d.utility.Vector3dVector(cols)

    # Downsample a bit
    pcd = pcd.voxel_down_sample(voxel_size=0.02)

    o3d.io.write_point_cloud(out_ply, pcd)
    print(f"[PointCloud] Saved point cloud to {out_ply}")


# ---------- 4. POINT CLOUD -> MESH -> GLB ----------

def pointcloud_to_glb(ply_path, glb_path):
    pcd = o3d.io.read_point_cloud(ply_path)
    print("[Mesh] Estimating normals...")
    pcd.estimate_normals()

    print("[Mesh] Running Poisson reconstruction (this might take a bit)...")
    mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=8
    )

    # Crop to reasonable bounds (optional, for noisy clouds)
    bbox = pcd.get_axis_aligned_bounding_box()
    mesh = mesh.crop(bbox)

    # Convert to trimesh and export as GLB
    vertices = np.asarray(mesh.vertices)
    faces = np.asarray(mesh.triangles)

    tri_mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    scene = trimesh.Scene(tri_mesh)

    scene.export(glb_path)
    print(f"[Mesh] Exported GLB to {glb_path}")


# ---------- MAIN PIPELINE ----------

if __name__ == "__main__":
    video_path = "ex3.mp4"         # <-- put your video file here
    frames_dir = "frames"
    depth_dir = "depth"
    ply_path = "room.ply"
    glb_path = "room.glb"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[Info] Using device: {device}")

    extract_frames(video_path, frames_dir, step=5)
    run_depth_on_frames(frames_dir, depth_dir, device=device)
    build_point_cloud(frames_dir, depth_dir, ply_path)
    pointcloud_to_glb(ply_path, glb_path)
