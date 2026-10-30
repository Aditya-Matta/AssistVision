"""
detector.py — MobileNet-SSD object detection wrapper
"""

import cv2
import numpy as np
from config import (
    MODEL_WEIGHTS, MODEL_CONFIG, CONFIDENCE_THRESHOLD,
    INPUT_SIZE, COCO_CLASSES, BBOX_COLOR_HIGH, BBOX_COLOR_NORMAL,
    HIGH_PRIORITY_OBJECTS, LABEL_FONT_SCALE, LABEL_THICKNESS
)


class ObjectDetector:
    """
    Wraps OpenCV's DNN module with MobileNet-SSD.
    Returns detected objects with labels, confidence, bounding boxes,
    direction, and priority classification.
    """

    def __init__(self):
        print("[Detector] Loading MobileNet-SSD model…")
        self.net = cv2.dnn.readNetFromTensorflow(MODEL_WEIGHTS, MODEL_CONFIG)
        print("[Detector] Model loaded successfully.")
        self._history = {}        # label -> count of consecutive frames seen
        self._STABLE_FRAMES = 3   # must appear in this many frames to show
        self._last_detections = []

    def detect(self, frame):
        h, w = frame.shape[:2]
        frame = cv2.flip(frame, 1)
        blob = cv2.dnn.blobFromImage(
            frame, 
            scalefactor=1.0 / 127.5,      # Scale down 
            size=INPUT_SIZE, 
            mean=(127.5, 127.5, 127.5),   # Shift the center to 0
            swapRB=True, 
            crop=False
        )

        self.net.setInput(blob)
        output = self.net.forward()

        # Group detections by label, keep only highest confidence per label
        best = {}
        for detection in output[0, 0]:
            score = float(detection[2])
            if score < CONFIDENCE_THRESHOLD:
                continue
            class_id = int(detection[1])
            if class_id >= len(COCO_CLASSES):
                continue
            label = COCO_CLASSES[class_id]
            if label == "__background__":
                continue
            if label not in best or score > best[label][0]:
                best[label] = (score, detection)

        detections = []
        for label, (score, detection) in best.items():
            x1 = max(0, int(detection[3] * w))
            y1 = max(0, int(detection[4] * h))
            x2 = min(w, int(detection[5] * w))
            y2 = min(h, int(detection[6] * h))
            direction = self._get_direction(x1, x2, w)
            priority  = "high" if label in HIGH_PRIORITY_OBJECTS else "normal"
            detections.append({
                "label":      label,
                "confidence": score,
                "box":        (x1, y1, x2, y2),
                "direction":  direction,
                "priority":   priority,
            })

        # Temporal smoothing — only keep detections seen in recent frames
        self._update_history(detections)
        stable = self._get_stable_detections()

        annotated = self._draw(frame.copy(), stable)
        return stable, annotated

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_direction(self, x1, x2, frame_width):
        """Classify horizontal position of bbox centre as left/center/right."""
        centre = (x1 + x2) / 2
        third  = frame_width / 3
        if centre < third:
            return "left"
        elif centre < 2 * third:
            return "center"
        else:
            return "right"

    def _draw(self, frame, detections):
        """Draw bounding boxes and labels on frame."""
        for d in detections:
            x1, y1, x2, y2 = d["box"]
            color = BBOX_COLOR_HIGH if d["priority"] == "high" else BBOX_COLOR_NORMAL
            thickness = 3 if d["priority"] == "high" else 2

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

            label_text = f"{d['label']} ({d['confidence']:.0%}) · {d['direction']}"
            (tw, th), _ = cv2.getTextSize(
                label_text, cv2.FONT_HERSHEY_SIMPLEX, LABEL_FONT_SCALE, LABEL_THICKNESS
            )
            # Background pill for readability
            cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
            cv2.putText(
                frame, label_text,
                (x1 + 3, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                LABEL_FONT_SCALE,
                (255, 255, 255),
                LABEL_THICKNESS,
                cv2.LINE_AA,
            )

        return frame
    def _update_history(self, detections):
        self._last_detections = detections
        seen_now = {d["label"] for d in detections}
        for label in seen_now:
            self._history[label] = min(self._history.get(label, 0) + 1, 10)
        for label in list(self._history):
            if label not in seen_now:
                self._history[label] -= 2
                if self._history[label] <= 0:
                    del self._history[label]

    def _get_stable_detections(self):
        # Only return detections that have been consistently seen
        # We store the full detection dict in history too
        return [d for d in self._last_detections
                if self._history.get(d["label"], 0) >= self._STABLE_FRAMES]