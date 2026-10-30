"""
download_model.py — Downloads MobileNet-SSD v3 model files.
Run this once before launching the main app:
    python download_model.py
"""

import os
import urllib.request

MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

FILES = {
    "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt": (
        "https://gist.githubusercontent.com/dkurt/"
        "54a8e8b51beb3bd3f770b79e56927bd7/raw/"
        "2a20064a9d33b893dd95d2567da126d0ecd03e85/"
        "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
    ),
}

# The .pb weights file must be extracted from the tar.gz archive
TAR_URL = (
    "https://storage.googleapis.com/download.tensorflow.org/"
    "models/object_detection/ssd_mobilenet_v3_large_coco_2020_01_14.tar.gz"
)

for filename, url in FILES.items():
    dest = os.path.join(MODEL_DIR, filename)
    if os.path.exists(dest):
        print(f"[✓] {filename} already exists.")
        continue
    print(f"[↓] Downloading {filename}…")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"[✓] Saved → {dest}")
    except Exception as e:
        print(f"[✗] Failed: {e}")

# Download and extract the .pb weights file from tar.gz
pb_dest = os.path.join(MODEL_DIR, "frozen_inference_graph.pb")
if os.path.exists(pb_dest):
    print(f"[✓] frozen_inference_graph.pb already exists.")
else:
    import tarfile, io
    print("[↓] Downloading model weights (.tar.gz) from TensorFlow Model Zoo…")
    print("    (This is ~19MB, please wait…)")
    try:
        tar_path = os.path.join(MODEL_DIR, "_temp_model.tar.gz")
        urllib.request.urlretrieve(TAR_URL, tar_path)
        with tarfile.open(tar_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("frozen_inference_graph.pb"):
                    member.name = os.path.basename(member.name)
                    tar.extract(member, MODEL_DIR)
                    print(f"[✓] Extracted → {pb_dest}")
                    break
        os.remove(tar_path)
    except Exception as e:
        print(f"[✗] Failed to download weights: {e}")
        print(f"\n    Download manually from:\n    {TAR_URL}")
        print(f"    Extract and copy frozen_inference_graph.pb → models/")

print("\nAll done. Run:  python main.py")
