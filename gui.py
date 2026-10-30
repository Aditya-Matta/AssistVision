"""
gui.py — Tkinter GUI for AssistVision
Fixed layout: all widgets render correctly on launch.
"""

import tkinter as tk
from tkinter import messagebox
import cv2
import threading
import time
from PIL import Image, ImageTk

from config import (
    WINDOW_TITLE, CAMERA_INDEX,
    FRAME_WIDTH, FRAME_HEIGHT,
)
from detector     import ObjectDetector
from voice_engine import VoiceEngine
from sos          import send_sos

from config import FEED_WIDTH as DISPLAY_W, FEED_HEIGHT as DISPLAY_H

BG_DARK  = "#0d0d1a"
BG_PANEL = "#16213e"
BG_FEED  = "#0a0a14"
RED      = "#e94560"
TEAL     = "#00d4aa"
AMBER    = "#f0a500"
MUTED    = "#a8a8b3"
WHITE    = "#e0e0e0"


class AssistVisionApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)

        self._running      = False
        self._capture      = None
        self._latest_frame = None
        self._frame_lock   = threading.Lock()

        self._build_ui()
        self.root.update()

        self._status_var.set("Loading model, please wait...")
        self.root.update()

        self.detector = ObjectDetector()
        self.voice    = VoiceEngine()

        self._status_var.set("Model ready. Press Start Detection.")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG_PANEL, pady=10)
        hdr.pack(side=tk.TOP, fill=tk.X)

        tk.Label(hdr, text="👁  AssistVision",
                 font=("Helvetica", 17, "bold"),
                 fg=RED, bg=BG_PANEL).pack(side=tk.LEFT, padx=16)
        tk.Label(hdr, text="Real-Time Assistive Object Detection",
                 font=("Helvetica", 10), fg=MUTED, bg=BG_PANEL).pack(side=tk.LEFT)

        # ── Body row ────────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=BG_DARK)
        body.pack(side=tk.TOP, fill=tk.BOTH, padx=12, pady=8)

        # Left: camera feed
        feed_wrap = tk.Frame(body, bg=RED, bd=2,
                     width=DISPLAY_W, height=DISPLAY_H)
        feed_wrap.pack_propagate(False)  # 🔥 important
        feed_wrap.pack(side=tk.LEFT)

        self.feed_label = tk.Label(feed_wrap, bg=BG_FEED)
        self.feed_label.pack(fill=tk.BOTH, expand=True)

        # Right: sidebar
        sidebar = tk.Frame(body, bg=BG_DARK, width=230)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))
        sidebar.pack_propagate(False)

        # Status card
        s_card = tk.Frame(sidebar, bg=BG_PANEL, padx=10, pady=8)
        s_card.pack(fill=tk.X, pady=(0, 8))

        tk.Label(s_card, text="STATUS", font=("Courier", 8, "bold"),
                 fg=MUTED, bg=BG_PANEL).pack(anchor=tk.W)

        self._status_var = tk.StringVar(value="Initialising...")
        tk.Label(s_card, textvariable=self._status_var,
                 font=("Courier", 9), fg=TEAL, bg=BG_PANEL,
                 wraplength=210, justify=tk.LEFT).pack(anchor=tk.W, pady=(2, 4))

        self._fps_var = tk.StringVar(value="FPS: —")
        tk.Label(s_card, textvariable=self._fps_var,
                 font=("Courier", 10), fg=TEAL, bg=BG_PANEL).pack(anchor=tk.W)

        self._obj_var = tk.StringVar(value="Objects: —")
        tk.Label(s_card, textvariable=self._obj_var,
                 font=("Courier", 10), fg=AMBER, bg=BG_PANEL).pack(anchor=tk.W)

        self._sos_var = tk.StringVar(value="")
        tk.Label(s_card, textvariable=self._sos_var,
                 font=("Courier", 10, "bold"), fg=RED, bg=BG_PANEL).pack(anchor=tk.W)

        # Controls card
        c_card = tk.Frame(sidebar, bg=BG_PANEL, padx=10, pady=8)
        c_card.pack(fill=tk.X, pady=(0, 8))

        tk.Label(c_card, text="CONTROLS", font=("Courier", 8, "bold"),
                 fg=MUTED, bg=BG_PANEL).pack(anchor=tk.W, pady=(0, 6))

        self.start_btn = tk.Button(
            c_card, text="▶  Start Detection",
            font=("Helvetica", 10, "bold"),
            bg=TEAL, fg=BG_DARK, relief=tk.FLAT,
            cursor="hand2", pady=6,
            command=self._start_detection
        )
        self.start_btn.pack(fill=tk.X, pady=(0, 4))

        self.stop_btn = tk.Button(
            c_card, text="⏹  Stop Detection",
            font=("Helvetica", 10, "bold"),
            bg="#3d3d5c", fg=MUTED, relief=tk.FLAT,
            cursor="hand2", pady=6,
            command=self._stop_detection, state=tk.DISABLED
        )
        self.stop_btn.pack(fill=tk.X, pady=(0, 4))

        tk.Button(
            c_card, text="🆘  SOS Alert",
            font=("Helvetica", 10, "bold"),
            bg=RED, fg=WHITE, relief=tk.FLAT,
            cursor="hand2", pady=6,
            command=self._trigger_sos
        ).pack(fill=tk.X)

        tk.Label(c_card, text="(or press  S  key)",
                 font=("Courier", 8), fg=MUTED, bg=BG_PANEL).pack(anchor=tk.W, pady=(4,0))

        # Log card
        l_card = tk.Frame(sidebar, bg=BG_PANEL, padx=10, pady=8)
        l_card.pack(fill=tk.BOTH, expand=True)

        tk.Label(l_card, text="DETECTION LOG", font=("Courier", 8, "bold"),
                 fg=MUTED, bg=BG_PANEL).pack(anchor=tk.W, pady=(0, 4))

        log_inner = tk.Frame(l_card, bg=BG_PANEL)
        log_inner.pack(fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(log_inner, bg=BG_PANEL, troughcolor=BG_DARK)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_box = tk.Text(
            log_inner, height=14, width=27,
            bg=BG_DARK, fg="#c0c0d0",
            font=("Courier", 8),
            state=tk.DISABLED, relief=tk.FLAT, bd=0,
            wrap=tk.WORD, yscrollcommand=sb.set
        )
        self.log_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self.log_box.yview)

        self.log_box.tag_config("high",   foreground="#ff4757")
        self.log_box.tag_config("normal", foreground="#2ed573")
        self.log_box.tag_config("sos",    foreground="#ffa502")
        self.log_box.tag_config("info",   foreground=MUTED)

        # Keyboard shortcuts
        self.root.bind("<s>", lambda e: self._trigger_sos())
        self.root.bind("<S>", lambda e: self._trigger_sos())

    # ─────────────────────────────────────────────────────────────────────────

    def _start_detection(self):
        self._capture = cv2.VideoCapture(CAMERA_INDEX)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        if not self._capture.isOpened():
            messagebox.showerror("Camera Error",
                                 "Could not open camera. Check webcam connection.")
            return

        self._running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL, bg=RED, fg=WHITE)
        self._status_var.set("Running…")
        self._log("Detection started.", "info")
        threading.Thread(target=self._detection_loop, daemon=True).start()

    def _stop_detection(self):
        self._running = False
        if self._capture:
            self._capture.release()
            self._capture = None
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED, bg="#3d3d5c", fg=MUTED)
        self.feed_label.config(image="", bg=BG_FEED)
        self.feed_label.image = None
        self._fps_var.set("FPS: —")
        self._obj_var.set("Objects: —")
        self._status_var.set("Stopped.")
        self._log("Detection stopped.", "info")

    def _detection_loop(self):
        prev = time.time()
        while self._running:
            ret, frame = self._capture.read()
            if not ret:
                self.root.after(0, self._stop_detection)
                break

            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            with self._frame_lock:
                self._latest_frame = frame.copy()

            detections, annotated = self.detector.detect(frame)
            for d in detections:
                self.voice.announce(d["label"], d["direction"], d["priority"])

            now = time.time()
            fps = 1.0 / max(now - prev, 1e-9)
            prev = now
            self.root.after(0, self._update_ui, annotated, detections, fps)

    def _update_ui(self, frame, detections, fps):
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img   = Image.fromarray(rgb).resize((DISPLAY_W, DISPLAY_H))
        photo = ImageTk.PhotoImage(image=img)
        self.feed_label.config(image=photo)
        self.feed_label.image = photo

        self._fps_var.set(f"FPS: {fps:.1f}")
        self._obj_var.set(f"Objects: {len(detections)}")

        for d in detections:
            tag    = "high" if d["priority"] == "high" else "normal"
            prefix = "⚠ "  if d["priority"] == "high" else "• "
            self._log(f"{prefix}{d['label']} [{d['direction']}] {d['confidence']:.0%}", tag)

    # ─────────────────────────────────────────────────────────────────────────

    def _trigger_sos(self):
        self.voice.speak_sos()
        self._sos_var.set("SOS SENDING…")
        self._log("SOS triggered.", "sos")

        with self._frame_lock:
            snap = self._latest_frame.copy() if self._latest_frame is not None else None

        send_sos(
            frame=snap,
            on_success=lambda: self.root.after(0, self._sos_ok),
            on_failure=lambda e: self.root.after(0, self._sos_fail, e),
        )

    def _sos_ok(self):
        self._sos_var.set("SOS SENT ✓")
        self._log("SOS email delivered.", "sos")
        self.root.after(4000, lambda: self._sos_var.set(""))

    def _sos_fail(self, err):
        self._sos_var.set("SOS FAILED ✗")
        self._log(f"SOS error: {err}", "sos")
        messagebox.showerror("SOS Error", f"Could not send SOS:\n{err}")

    def _log(self, msg: str, tag: str = "info"):
        self.log_box.config(state=tk.NORMAL)
        ts = time.strftime("%H:%M:%S")
        self.log_box.insert(tk.END, f"[{ts}] {msg}\n", tag)
        self.log_box.see(tk.END)
        lines = int(self.log_box.index("end-1c").split(".")[0])
        if lines > 300:
            self.log_box.delete("1.0", "50.0")
        self.log_box.config(state=tk.DISABLED)

    def _on_close(self):
        self._running = False
        if self._capture:
            self._capture.release()
        if hasattr(self, "voice"):
            self.voice.shutdown()
        self.root.destroy()
