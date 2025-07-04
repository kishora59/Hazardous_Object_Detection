import threading
import socket
import pickle
import time
from ultralytics import YOLO
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
import cv2


model = YOLO("best.pt")
model.verbose = False

swap_pairs = [("scissors", "cell phone"), ("cell phone", "scissors"), ("chair", "knife"), ("knife", "chair")]
swap_map = {}
for a, b in swap_pairs:
    id_a = [k for k, v in model.names.items() if v == a]
    id_b = [k for k, v in model.names.items() if v == b]
    if id_a and id_b:
        swap_map[id_a[0]] = id_b[0]
        swap_map[id_b[0]] = id_a[0]

grid_rows, grid_cols = 5, 5
center_zone = (2, 2)
confidence_threshold = 0.5

cap = cv2.VideoCapture(0)
instruction_history = []

server_ip = '0.0.0.0'
server_port = 12345
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_ip, server_port))
server_socket.listen(1)
client_socket, client_address = server_socket.accept()

harmful_objects = ["knife", "scissors"]
detected_harmful_object = None

last_detection_time = time.time()

def process_frame():
    global detected_harmful_object, last_detection_time
    ret, frame = cap.read()
    if not ret:
        root.after(10, process_frame)
        return

    frame_h, frame_w = frame.shape[:2]
    grid_w = frame_w / grid_cols
    grid_h = frame_h / grid_rows

    results = model(frame, conf=confidence_threshold)
    objects = results[0].boxes

    zones_covered = set()
    detected_classes = set()

    harmful_object_detected = False

    for box in objects:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        x1 = max(0, min(frame_w - 1, x1))
        y1 = max(0, min(frame_h - 1, y1))
        x2 = max(0, min(frame_w - 1, x2))
        y2 = max(0, min(frame_h - 1, y2))

        start_col = int(x1 // grid_w)
        end_col = int(x2 // grid_w)
        start_row = int(y1 // grid_h)
        end_row = int(y2 // grid_h)

        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                if 0 <= row < grid_rows and 0 <= col < grid_cols:
                    zones_covered.add((row, col))

        cls_id = int(box.cls[0])
        swapped_cls_id = swap_map[cls_id] if cls_id in swap_map else cls_id
        label = model.names[swapped_cls_id]
        detected_classes.add(label)

        if label in harmful_objects:
            harmful_object_detected = True
            detected_harmful_object = label

    if len(objects) > 0:
        last_detection_time = time.time()

    instruction = "Move forward"
    coverage_ratio = len(zones_covered) / (grid_rows * grid_cols)

    if harmful_object_detected:
        safety_status = "Unsafe"
        instruction = f"Harmful object detected: {detected_harmful_object} — please move back."
    else:
        safety_status = "Safe"
        if coverage_ratio >= 0.6:
            instruction = "Path is blocked. Please step back."
        elif all((gy, gx) in zones_covered for gy in range(grid_rows) for gx in [2]) and not any((gy, gx) in zones_covered for gy in range(grid_rows) for gx in [0, 1, 3, 4]):
            instruction = "Obstacle ahead — move left or right"
        elif zones_covered == {center_zone}:
            instruction = "Obstacle ahead — stop"
        elif any((2, x) in zones_covered for x in [0, 1]) and not any((2, x) in zones_covered for x in [3, 4]):
            instruction = "Obstacle on your left — move right"
        elif any((2, x) in zones_covered for x in [3, 4]) and not any((2, x) in zones_covered for x in [0, 1]):
            instruction = "Obstacle on your right — move left"
        elif any((2, x) in zones_covered for x in [0, 1]) and any((2, x) in zones_covered for x in [3, 4]):
            instruction = "Obstacle on both sides — look for alternate path"
        elif any((3, x) in zones_covered for x in range(grid_cols)):
            instruction = "Obstacle near feet — stop"
        elif any((4, x) in zones_covered for x in [0, 1]):
            instruction = "Low object on left — careful"
        elif any((4, x) in zones_covered for x in [3, 4]):
            instruction = "Low object on right — careful"
        elif (1, 2) in zones_covered or (0, 2) in zones_covered:
            instruction = "Top-center — heads-up"
        elif time.time() - last_detection_time > 5:
            instruction = "Move forward"

    instruction_history.append(instruction)
    if len(instruction_history) > 3:
        instruction_history.pop(0)

    if instruction_history.count(instruction) > 1 or instruction == "Move forward":
        serialized_instruction = pickle.dumps(instruction)
        client_socket.sendall(serialized_instruction)

    for row in range(grid_rows):
        for col in range(grid_cols):
            x1 = int(col * grid_w)
            y1 = int(row * grid_h)
            x2 = int((col + 1) * grid_w)
            y2 = int((row + 1) * grid_h)
            color = (0, 255, 0) if (row, col) in zones_covered else (200, 200, 200)
            thickness = 2 if (row, col) in zones_covered else 1
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

    annotated_frame = results[0].plot()
    combined = cv2.addWeighted(annotated_frame, 0.8, frame, 0.5, 0)
    img = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img)
    imgtk = ImageTk.PhotoImage(image=img_pil)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)
    instruction_label.config(text=instruction)
    coverage_label.config(text=f"Coverage: {coverage_ratio * 100:.2f}%")
    detected_label.config(text=f"Detected: {', '.join(detected_classes)}")
    safety_label.config(text=f"Safety Status: {safety_status}")
    root.after(10, process_frame)

def update_confidence(val):
    global confidence_threshold
    confidence_threshold = float(val)
    confidence_label.config(text=f"Confidence Threshold: {confidence_threshold}")

root = tk.Tk()
root.title("YOLOv8 Object Detection UI")

video_label = tk.Label(root)
video_label.pack(pady=10)

instruction_label = tk.Label(root, text="Move forward", font=("Helvetica", 24))
instruction_label.pack(pady=10)

coverage_label = tk.Label(root, text="Coverage: 0.00%", font=("Helvetica", 18))
coverage_label.pack(pady=5)

detected_label = tk.Label(root, text="Detected: None", font=("Helvetica", 18))
detected_label.pack(pady=5)

safety_label = tk.Label(root, text="Safety Status: Safe", font=("Helvetica", 18))
safety_label.pack(pady=5)

confidence_label = tk.Label(root, text=f"Confidence Threshold: {confidence_threshold}", font=("Helvetica", 18))
confidence_label.pack(pady=5)

confidence_slider = tk.Scale(root, from_=0, to=1, resolution=0.01, orient="horizontal", command=update_confidence)
confidence_slider.set(confidence_threshold)
confidence_slider.pack(pady=10)

button_frame = tk.Frame(root)
button_frame.pack(side="bottom", pady=20)

pause_button = tk.Button(button_frame, text="Pause", command=lambda: cap.release())
pause_button.pack(side="left", padx=20)

resume_button = tk.Button(button_frame, text="Resume", command=lambda: cap.open(0))
resume_button.pack(side="right", padx=20)

threading.Thread(target=process_frame, daemon=True).start()
root.mainloop()

cap.release()
client_socket.close()
server_socket.close()

