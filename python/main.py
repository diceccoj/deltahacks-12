import socket
import threading
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

latest_result = None
result_lock = threading.Lock()

SERVER_IP = "127.0.0.1"
SERVER_PORT = 4242
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

cap = cv2.VideoCapture(0)

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
PoseLandmarkerResult = mp.tasks.vision.PoseLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

def draw_landmarks(rgb_image, detection_result):
    POSE_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
        (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
        (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
        (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
        (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)
    ]
    pose_landmarks_list = detection_result.pose_landmarks
    annotated_image = np.copy(rgb_image)
    for pose_landmarks in pose_landmarks_list:
        # Draw connections
        for connection in POSE_CONNECTIONS:
            start_idx, end_idx = connection
            if start_idx < len(pose_landmarks) and end_idx < len(pose_landmarks):
                start = pose_landmarks[start_idx]
                end = pose_landmarks[end_idx]
                start_point = (int(start.x * annotated_image.shape[1]), 
                             int(start.y * annotated_image.shape[0]))
                end_point = (int(end.x * annotated_image.shape[1]), 
                           int(end.y * annotated_image.shape[0]))
                cv2.line(annotated_image, start_point, end_point, (0, 255, 0), 2)
        # Draw landmark points
        for landmark in pose_landmarks:
            cx = int(landmark.x * annotated_image.shape[1])
            cy = int(landmark.y * annotated_image.shape[0])
            cv2.circle(annotated_image, (cx, cy), 4, (0, 0, 255), -1)
    return annotated_image


def result_cb(result, output_image: mp.Image, timestamp_ms: int):
    global latest_result
    with result_lock:
        latest_result = result

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="./pose_landmarker_lite.task"),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=result_cb)

print("done initializing options!")

with PoseLandmarker.create_from_options(options) as landmarker:
    print(f"Landmarker: {landmarker}")
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: failed to capture image")
            break

        frame = cv2.resize(frame, (400, 300))
        frame = cv2.flip(frame, 1)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        landmarker.detect_async(mp_image, int(cap.get(cv2.CAP_PROP_POS_MSEC)))

        annotated_frame = frame.copy()
        with result_lock:
            if latest_result and latest_result.pose_landmarks:
                annotated_frame = draw_landmarks(annotated_frame, latest_result)

        cv2.putText(
            frame,
            f"OpenCV version: {cv2.__version__}",
            (5, 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        image = cv2.resize(annotated_frame, (400, 300))

        _, encoded_image = cv2.imencode(".jpg", image)

        if len(encoded_image) <= 65507:
            client_socket.sendto(encoded_image, (SERVER_IP, SERVER_PORT))
        else:
            print("Frame too large, skipping")

        cv2.imshow("Image", image)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        

cv2.destroyAllWindows()

cap.release()
