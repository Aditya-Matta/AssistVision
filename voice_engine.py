# """
# voice_engine.py — Priority-aware voice alert system
# Uses pyttsx3 in a background thread to prevent GUI blocking.
# """

# import time
# import threading
# import queue
# import pyttsx3
# from config import (
#     VOICE_RATE, VOICE_VOLUME,
#     COOLDOWN_SECONDS, HIGH_PRIORITY_COOLDOWN,
#     HIGH_PRIORITY_OBJECTS
# )


# class VoiceEngine:
#     """
#     Manages all text-to-speech output.

#     Design decisions:
#     - Runs in a dedicated daemon thread (non-blocking for GUI/detection loop)
#     - High-priority objects bypass cooldown and jump the queue
#     - Normal-priority objects respect per-label cooldown timers
#     - A small speech queue (maxsize=3) prevents announcement pile-ups
#     """

#     def __init__(self):
#         self._queue    = queue.PriorityQueue(maxsize=6)
#         self._cooldown = {}        # label → last_spoken timestamp
#         self._lock     = threading.Lock()
#         self._running  = True

#         # Start speech worker thread
#         self._thread = threading.Thread(target=self._worker, daemon=True)
#         self._thread.start()
#         print("[Voice] Engine started.")

#     # ── Public API ────────────────────────────────────────────────────────────

#     def announce(self, label: str, direction: str, priority: str):
#         """
#         Decide whether to speak and what to say.

#         High-priority  → "Warning — <label> on the <direction>."
#         Normal         → "<label> on the <direction>."
#         """
#         now = time.time()

#         with self._lock:
#             last = self._cooldown.get(label, 0)
#             gap  = HIGH_PRIORITY_COOLDOWN if priority == "high" else COOLDOWN_SECONDS

#             if now - last < gap:
#                 return   # Still in cooldown; skip

#             self._cooldown[label] = now

#         text       = self._build_text(label, direction, priority)
#         importance = 0 if priority == "high" else 1   # Lower = higher PQ priority

#         try:
#             self._queue.put_nowait((importance, text))
#         except queue.Full:
#             pass   # Drop the alert rather than block the detection loop

#     def speak_sos(self):
#         """Immediately announce SOS — bypasses everything."""
#         try:
#             self._queue.put_nowait((-1, "SOS alert sent. Help is on the way."))
#         except queue.Full:
#             pass

#     def shutdown(self):
#         self._running = False

#     # ── Internals ─────────────────────────────────────────────────────────────

#     def _build_text(self, label: str, direction: str, priority: str) -> str:
#         if direction == "center":
#             location = "ahead"
#         elif direction == "left":
#             location = "on your left"
#         else:
#             location = "on your right"

#         if priority == "high":
#             return f"Warning — {label} {location}."
#         else:
#             return f"{label.capitalize()} {location}."

#     def _worker(self):
#         """Dedicated thread: pulls from queue and speaks."""
        
#         # 1. Initialize the engine ONCE per thread, before the loop starts
#         try:
#             engine = pyttsx3.init()
#             engine.setProperty("rate",   VOICE_RATE)
#             engine.setProperty("volume", VOICE_VOLUME)
#         except Exception as e:
#             print(f"[Voice] Failed to initialize pyttsx3: {e}")
#             return

#         while self._running:
#             try:
#                 # Wait for a message
#                 _, text = self._queue.get(timeout = 5)
                
#                 # 2. Simply say the text and wait for it to finish
#                 engine.say(text)
#                 engine.runAndWait()
                
#                 # 3. DO NOT call engine.stop() here!
                
#             except queue.Empty:
#                 continue
#             except Exception as e:
#                 print(f"[Voice] Error during speech: {e}")
                
#         # 4. Only stop the engine when the thread is completely shutting down
#         try:
#             engine.stop()
#         except:
#             pass

"""
voice_engine.py — Priority-aware voice alert system
Uses a "One-Shot Process" to completely avoid pyttsx3 deadlocks.
"""

import time
import multiprocessing
import pyttsx3
from config import (
    VOICE_RATE, VOICE_VOLUME,
    COOLDOWN_SECONDS, HIGH_PRIORITY_COOLDOWN
)

def _speak_single(text):
    """
    This function runs in a temporary, disposable process.
    It initializes the engine, speaks, and then immediately dies.
    This guarantees pyttsx3 will NEVER freeze or deadlock.
    """
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", VOICE_RATE)
        engine.setProperty("volume", VOICE_VOLUME)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[Voice] Error: {e}")


class VoiceEngine:
    """
    Manages all text-to-speech output using disposable processes.
    """

    def __init__(self):
        self._cooldown = {}        # label → last_spoken timestamp
        self._active_process = None
        print("[Voice] One-Shot Engine started.")

    # ── Public API ────────────────────────────────────────────────────────────

    def announce(self, label: str, direction: str, priority: str):
        now = time.time()

        # 1. Cooldown Check
        last = self._cooldown.get(label, 0)
        gap  = HIGH_PRIORITY_COOLDOWN if priority == "high" else COOLDOWN_SECONDS

        if now - last < gap:
            return   # Still in cooldown; skip

        # 2. Check if the engine is ALREADY speaking
        # We don't want voices overlapping and talking over each other
        if self._active_process is not None and self._active_process.is_alive():
            return   # Drop this alert so the current sentence can finish

        self._cooldown[label] = now
        text = self._build_text(label, direction, priority)

        # 3. Fire and forget the one-shot process
        self._active_process = multiprocessing.Process(
            target=_speak_single, 
            args=(text,), 
            daemon=True
        )
        self._active_process.start()

    def speak_sos(self):
        """SOS is critical. It kills the current speech to shout the SOS."""
        if self._active_process is not None and self._active_process.is_alive():
            self._active_process.terminate()  # forcefully stop current speech
            
        self._active_process = multiprocessing.Process(
            target=_speak_single, 
            args=("SOS alert sent. Help is on the way.",), 
            daemon=True
        )
        self._active_process.start()

    def shutdown(self):
        if self._active_process is not None and self._active_process.is_alive():
            self._active_process.terminate()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _build_text(self, label: str, direction: str, priority: str) -> str:
        if direction == "center":
            location = "ahead"
        elif direction == "left":
            location = "on your left"
        else:
            location = "on your right"

        if priority == "high":
            return f"Warning — {label} {location}."
        else:
            return f"{label.capitalize()} {location}."