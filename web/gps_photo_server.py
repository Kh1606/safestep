import os
import json
from datetime import datetime
from flask import Flask, request, send_from_directory

app = Flask(__name__)

# Folder where photos + metadata will be saved
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route("/")
def index():
    # Simple HTML page with GPS + camera upload
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MASIL GPS Photo Collector</title>
  <style>
    body { font-family: sans-serif; padding: 1rem; }
    label { display: block; margin-top: 1rem; }
    #status { margin-top: 0.5rem; color: #333; }
  </style>
</head>
<body>
  <h1>MASIL GPS Photo</h1>

  <p>
    1) Allow location when browser asks<br>
    2) Wait until coordinates appear<br>
    3) (Optional) Set floor (B2, 1F, 2F, etc.)<br>
    4) Take a photo and press "Upload"
  </p>

  <div id="status">Getting location...</div>

  <form id="uploadForm" action="/upload" method="POST" enctype="multipart/form-data">
    <input type="hidden" name="lat" id="lat">
    <input type="hidden" name="lon" id="lon">
    <input type="hidden" name="accuracy" id="accuracy">
    <input type="hidden" name="altitude" id="altitude">
    <input type="hidden" name="alt_accuracy" id="alt_accuracy">

    <label>
      Floor (optional, e.g. B2, 1F, 2F):
      <input type="text" name="floor" id="floor" placeholder="1F">
    </label>

    <label>
      Photo:
      <input type="file" name="photo" accept="image/*" capture="environment" required>
    </label>

    <button type="submit">Upload</button>
  </form>

  <script>
    const statusDiv = document.getElementById("status");
    const latInput = document.getElementById("lat");
    const lonInput = document.getElementById("lon");
    const accInput = document.getElementById("accuracy");
    const altInput = document.getElementById("altitude");
    const altAccInput = document.getElementById("alt_accuracy");

    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const c = pos.coords;
          latInput.value = c.latitude;
          lonInput.value = c.longitude;
          accInput.value = c.accuracy;

          // altitude may be null
          if (c.altitude !== null) {
            altInput.value = c.altitude;
          }
          if (c.altitudeAccuracy !== null) {
            altAccInput.value = c.altitudeAccuracy;
          }

          let text =
            "Location OK: " +
            c.latitude.toFixed(6) + ", " +
            c.longitude.toFixed(6) +
            " (±" + Math.round(c.accuracy) + " m)";

          if (c.altitude !== null) {
            text += "<br>Altitude: " + c.altitude.toFixed(1) + " m";
            if (c.altitudeAccuracy !== null) {
              text += " (±" + Math.round(c.altitudeAccuracy) + " m)";
            }
          } else {
            text += "<br>Altitude: not available";
          }

          statusDiv.innerHTML = text;
        },
        (err) => {
          console.error(err);
          statusDiv.textContent = "Could not get location: " + err.message;
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 5000
        }
      );
    } else {
      statusDiv.textContent = "Geolocation not supported on this device.";
    }
  </script>
</body>
</html>
    """


@app.route("/upload", methods=["POST"])
def upload():
    # Get file + GPS fields from form
    photo = request.files.get("photo")
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    acc = request.form.get("accuracy")
    alt = request.form.get("altitude")
    alt_acc = request.form.get("alt_accuracy")
    floor = request.form.get("floor")  # optional manual floor

    if not photo:
        return "No photo uploaded", 400

    # Timestamp-based filename
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    ext = os.path.splitext(photo.filename)[1].lower() or ".jpg"
    img_filename = f"{ts}{ext}"
    img_path = os.path.join(UPLOAD_DIR, img_filename)

    # Save image
    photo.save(img_path)

    def to_float_or_none(x):
        try:
            return float(x) if x not in (None, "", "null") else None
        except ValueError:
            return None

    meta = {
      "filename": img_filename,
      "lat": to_float_or_none(lat),
      "lon": to_float_or_none(lon),
      "accuracy_m": to_float_or_none(acc),
      "altitude_m": to_float_or_none(alt),
      "altitude_accuracy_m": to_float_or_none(alt_acc),
      "floor": floor or None,
      "timestamp_utc": ts
    }

    meta_filename = f"{ts}.json"
    meta_path = os.path.join(UPLOAD_DIR, meta_filename)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return (
        f"Saved photo as {img_filename}<br>"
        f"GPS: {meta['lat']}, {meta['lon']}<br>"
        f"Altitude: {meta['altitude_m']} (±{meta['altitude_accuracy_m']} m)<br>"
        f"Floor: {meta['floor']}<br>"
        f"<a href='/'>Back</a>"
    )


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
