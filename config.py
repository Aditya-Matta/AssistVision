"""
config.py — Central configuration for AssistVision
Modify these values to tune system behaviour.
"""
import os

# ── Model ────────────────────────────────────────────────────────────────────
MODEL_WEIGHTS = "models/frozen_inference_graph.pb"
MODEL_CONFIG  = "models/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
CONFIDENCE_THRESHOLD = 0.55   # Ignore detections below this score
INPUT_SIZE = (320, 320)        # MobileNet-SSD input resolution

# ── Camera ───────────────────────────────────────────────────────────────────
CAMERA_INDEX  = 0              # 0 = default webcam
FRAME_WIDTH   = 640
FRAME_HEIGHT  = 480

# ── Priority Alert System ─────────────────────────────────────────────────────
# Objects in this set trigger INSTANT voice alerts, bypassing cooldown
HIGH_PRIORITY_OBJECTS = {
    "car", "bus", "truck", "motorcycle", "bicycle", "person"
}

# ── Voice Cooldown ────────────────────────────────────────────────────────────
COOLDOWN_SECONDS       = 4.0   # Minimum gap between normal-priority alerts
HIGH_PRIORITY_COOLDOWN = 1.5   # Shorter gap for high-priority re-alerts

# ── Voice Engine ─────────────────────────────────────────────────────────────
VOICE_RATE   = 160             # Words per minute (default ~200 is fast)
VOICE_VOLUME = 1.0             # 0.0 – 1.0

# ── SOS / Caretaker Email ─────────────────────────────────────────────────────
SOS_SENDER_EMAIL    = os.getenv("SOS_SENDER_EMAIL")    # Email address for sending SOS alerts
SOS_SENDER_PASSWORD = os.getenv("SOS_SENDER_PASSWORD") # App password for the sender
SOS_RECIPIENT_EMAIL = os.getenv("SOS_RECIPIENT_EMAIL") # Caretaker's email address
SOS_SUBJECT         = "⚠️ AssistVision SOS Alert"
SOS_BODY            = (
    "This is an automated SOS alert from AssistVision.\n"
    "The user has triggered an emergency signal.\n"
    "Please check on them immediately."
)
ATTACH_SCREENSHOT   = True     # Attach a camera frame to the SOS email

# ── GUI ───────────────────────────────────────────────────────────────────────
WINDOW_TITLE  = "AssistVision — Assistive Object Detection"
FEED_WIDTH    = 640
FEED_HEIGHT   = 480
BBOX_COLOR_HIGH   = (0, 0, 255)    # Red (BGR) for high-priority objects
BBOX_COLOR_NORMAL = (0, 200, 0)    # Green (BGR) for normal objects
LABEL_FONT_SCALE  = 0.6
LABEL_THICKNESS   = 2

# ── COCO Class Labels (91 classes) ────────────────────────────────────────────
# ── COCO Class Labels (91 classes padded for TF Object Detection API) ──────────
COCO_CLASSES = [
    "__background__", "person", "bicycle", "car", "motorcycle", "airplane", 
    "bus", "train", "truck", "boat", "traffic light", "fire hydrant", 
    "N/A", "stop sign", "parking meter", "bench", "bird", "cat", "dog", 
    "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "N/A", 
    "backpack", "umbrella", "N/A", "N/A", "handbag", "tie", "suitcase", 
    "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat", 
    "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", 
    "N/A", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", 
    "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", 
    "donut", "cake", "chair", "couch", "potted plant", "bed", "N/A", 
    "dining table", "N/A", "N/A", "toilet", "N/A", "tv", "laptop", "mouse", 
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", 
    "sink", "refrigerator", "N/A", "book", "clock", "vase", "scissors", 
    "teddy bear", "hair drier", "toothbrush"
]