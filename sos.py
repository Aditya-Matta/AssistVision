"""
sos.py — Caretaker SOS email with optional camera snapshot
"""

import smtplib
import threading
import os
import cv2
from email.mime.text     import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image    import MIMEImage
import time

from config import (
    SOS_SENDER_EMAIL, SOS_SENDER_PASSWORD,
    SOS_RECEIVER_EMAIL, SOS_SUBJECT, SOS_BODY,
    ATTACH_SCREENSHOT
)


def send_sos(frame=None, on_success=None, on_failure=None):
    """
    Send an SOS email non-blocking.
    Optionally attaches `frame` (BGR numpy array) as a JPEG.
    Calls on_success() or on_failure(error_msg) on completion.
    """
    def _send():
        snapshot_path = f"sos_snapshot_{int(time.time())}.jpg"
        try:
            msg = MIMEMultipart()
            msg["From"]    = SOS_SENDER_EMAIL
            msg["To"]      = SOS_RECEIVER_EMAIL
            msg["Subject"] = SOS_SUBJECT
            msg.attach(MIMEText(SOS_BODY, "plain"))

            if ATTACH_SCREENSHOT and frame is not None:
                cv2.imwrite(snapshot_path, frame)
                with open(snapshot_path, "rb") as f:
                    img_data = f.read()
                image = MIMEImage(img_data, name="snapshot.jpg")
                msg.attach(image)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(SOS_SENDER_EMAIL, SOS_SENDER_PASSWORD)
                server.sendmail(SOS_SENDER_EMAIL, SOS_RECEIVER_EMAIL, msg.as_string())

            if on_success:
                on_success()

        except Exception as e:
            if on_failure:
                on_failure(str(e))

        finally:
            if os.path.exists(snapshot_path):
                os.remove(snapshot_path)

    threading.Thread(target=_send, daemon=True).start()
