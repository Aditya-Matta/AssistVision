import cv2
import time
import numpy as np
from config import MODEL_WEIGHTS, MODEL_CONFIG, CONFIDENCE_THRESHOLD, INPUT_SIZE, COCO_CLASSES

net = cv2.dnn.readNetFromTensorflow(MODEL_WEIGHTS, MODEL_CONFIG)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

latencies = []
frame_count = 0
total_start = time.time()

print("Measuring... press Q to stop (run for at least 100 frames)")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    blob = cv2.dnn.blobFromImage(frame, size=INPUT_SIZE, swapRB=True, crop=False)
    net.setInput(blob)

    t_start = time.time()
    output = net.forward()
    t_end = time.time()

    latencies.append((t_end - t_start) * 1000)
    frame_count += 1

    elapsed = time.time() - total_start
    fps = frame_count / elapsed
    cv2.putText(frame, f"FPS: {fps:.1f}  Latency: {latencies[-1]:.1f}ms",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
    cv2.imshow("Measuring", frame)

    if cv2.waitKey(1) & 0xFF == ord('q') or frame_count >= 10000:
        break

cap.release()
cv2.destroyAllWindows()

total_time = time.time() - total_start
avg_fps = frame_count / total_time
avg_lat = np.mean(latencies)
std_lat = np.std(latencies)
min_lat = np.min(latencies)
max_lat = np.max(latencies)

print(f"\n========= RESULTS ({frame_count} frames) =========")
print(f"Average FPS        : {avg_fps:.2f}")
print(f"Avg Inference Latency : {avg_lat:.2f} ms")
print(f"Std Dev Latency    : {std_lat:.2f} ms")
print(f"Min Latency        : {min_lat:.2f} ms")
print(f"Max Latency        : {max_lat:.2f} ms")
print(f"Total time         : {total_time:.2f} s")
print(f"\nNote your CPU model from Task Manager / System Info for the paper")