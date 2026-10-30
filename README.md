# AssistVision 👁

### Real-Time Assistive Object Detection System

**IEEE Project** | Python · OpenCV · MobileNet-SSD · pyttsx3 · Tkinter

---

## What It Does

AssistVision is an accessibility-focused computer vision system that detects
objects in a live camera feed and announces them via voice. It includes a
priority safety layer that immediately warns users of potentially dangerous
objects (vehicles, people) using distinct alert language.

---

## Features

| Feature             | Description                                              |
| ------------------- | -------------------------------------------------------- |
| Object Detection    | MobileNet-SSD v3 on COCO (80 classes)                    |
| Direction Awareness | Left / Center / Right from bounding box position         |
| Priority Alerts     | Instant "Warning — car ahead" for hazardous objects     |
| Voice Cooldown      | Prevents announcement spam for normal objects            |
| SOS System          | Keyboard/button trigger → email caretaker with snapshot |
| Live GUI            | Camera feed, detection log, FPS counter                  |

---

## Project Structure

```
assistive_vision/
├── main.py             Entry point
├── gui.py              Tkinter interface
├── detector.py         MobileNet-SSD wrapper
├── voice_engine.py     Priority voice alert system
├── sos.py              SOS email module
├── config.py           All configuration in one place
├── download_model.py   One-time model downloader
├── requirements.txt    Dependencies
└── models/             (auto-created by download_model.py)
    ├── frozen_inference_graph.pb
    └── ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Download model files

```bash
python download_model.py
```

### 3. Configure SOS email (optional)

Edit `.env`:

```python
SOS_SENDER_EMAIL    = "your_gmail@gmail.com"
SOS_SENDER_PASSWORD = "your_16_char_app_password"   # Gmail App Password
SOS_RECEIVER_EMAIL  = "caretaker@example.com"
```

> Gmail → Security → 2-Step Verification → App Passwords → Generate

### 4. Run

```bash
python main.py
```

---

## Usage

- Click **▶ Start** to begin detection
- Objects are announced via voice with direction context
- **Hazardous objects** (car, bus, truck, motorcycle, bicycle, person)
  trigger instant "Warning — ___" alerts
- Press **S** or click **🆘 SOS** to email the caretaker with a live snapshot
- Click **⏹ Stop** to end the session

---

## Priority Object List

Configurable in `config.py → HIGH_PRIORITY_OBJECTS`:

```python
HIGH_PRIORITY_OBJECTS = {
    "car", "bus", "truck", "motorcycle", "bicycle", "person"
}
```

---

## System Architecture

```
Camera (OpenCV)
       ↓
MobileNet-SSD v3 Detection
       ↓
Direction Classification (left / center / right)
       ↓
Priority Intelligence Layer
   ├─ HIGH  → Instant "Warning — <object> <direction>"
   └─ NORMAL → Cooldown queue → "<object> on your <direction>"
                        ↓
               pyttsx3 Voice Engine (background thread)
```

---

## Viva / Demo Points

- "The system classifies detections into high and normal priority, ensuring
  potentially hazardous objects trigger immediate voice alerts while everyday
  objects follow a cooldown policy to prevent notification fatigue."
- "Since the system is assistive in nature, prioritizing hazardous objects
  ensures faster alerts and improves user safety."
- "Voice output is handled in a dedicated daemon thread, keeping the GUI
  and detection loop non-blocking."

---

## Dependencies

- `opencv-python` — Camera capture + DNN inference
- `pyttsx3` — Offline text-to-speech (no internet needed)
- `Pillow` — Converts OpenCV BGR frames for Tkinter display
- `smtplib` (stdlib) — SOS email delivery
