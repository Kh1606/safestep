from transformers import AutoImageProcessor, ZoeDepthForDepthEstimation
from PIL import Image
import torch
import numpy as np
import matplotlib.pyplot as plt

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# 1. Load processor + model
processor = AutoImageProcessor.from_pretrained("Intel/zoedepth-nyu-kitti")
model = ZoeDepthForDepthEstimation.from_pretrained("Intel/zoedepth-nyu-kitti").to(device)
model.eval()

# 2. Load image
image_path = "stairs3.jpg"
image = Image.open(image_path).convert("RGB")

# 3. Preprocess
inputs = processor(images=image, return_tensors="pt").to(device)

# 4. Predict depth
with torch.no_grad():
    outputs = model(**inputs)
    predicted_depth = outputs.predicted_depth  # shape: (1, H, W)

depth = predicted_depth[0].cpu().numpy()

# 5. Normalize for visualization
depth_min = depth.min()
depth_max = depth.max()
depth_norm = (depth - depth_min) / (depth_max - depth_min + 1e-6)

# 6. Plot
plt.figure(figsize=(10, 4))

plt.subplot(1, 2, 1)
plt.title("Original")
plt.axis("off")
plt.imshow(image)

plt.subplot(1, 2, 2)
plt.title("ZoeDepth depth")
plt.axis("off")
plt.imshow(depth_norm, cmap="plasma")

plt.tight_layout()
out_path = "stairs_zoe_depth_result.png"
plt.savefig(out_path, dpi=200)
plt.show()

print("Saved ZoeDepth visualization to", out_path)
