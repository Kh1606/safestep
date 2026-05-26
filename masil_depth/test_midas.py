import torch
import cv2
import numpy as np
import matplotlib.pyplot as plt

# Choose device (GPU if available, else CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# 1. Load MiDaS_small model and transforms from torch.hub
midas = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
midas.to(device)
midas.eval()

midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
transform = midas_transforms.small_transform  # IMPORTANT: use small_transform for MiDaS_small

# 2. Load your test image (BGR -> RGB)
image_path = "stairs3.jpg"  # change if your file name is different
img_bgr = cv2.imread(image_path)
if img_bgr is None:
    raise FileNotFoundError(f"Could not read image: {image_path}")

img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

# 3. Preprocess image
input_batch = transform(img_rgb).to(device)

# 4. Run model (no gradient needed)
with torch.no_grad():
    prediction = midas(input_batch)

# 5. Resize depth map back to original image size
prediction = torch.nn.functional.interpolate(
    prediction.unsqueeze(1),
    size=img_rgb.shape[:2],
    mode="bicubic",
    align_corners=False,
).squeeze()

depth = prediction.cpu().numpy()

# 6. Normalize for visualization (0..1)
depth_min = depth.min()
depth_max = depth.max()
depth_norm = (depth - depth_min) / (depth_max - depth_min + 1e-6)

# 7. Show original + depth map side by side
plt.figure(figsize=(10, 4))

plt.subplot(1, 2, 1)
plt.title("Original")
plt.axis("off")
plt.imshow(img_rgb)

plt.subplot(1, 2, 2)
plt.title("MiDaS_small depth")
plt.axis("off")
plt.imshow(depth_norm, cmap="plasma")

plt.tight_layout()
out_path = "stairs_depth_result.png"
plt.savefig(out_path, dpi=200)
plt.show()

print("Saved depth visualization to", out_path)
