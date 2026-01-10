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

LANDMARK_NAMES = {
    0: "nose",
    11: "left_shoulder",
    12: "right_shoulder",
    13: "left_elbow",
    14: "right_elbow",
    15: "left_wrist",
    16: "right_wrist",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle"
}

IDXS = {
    "nose": 0,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28
}

POSE_CONNECTIONS = [
    (11, 12),  # left_shoulder to right_shoulder
    (11, 13),  # left_shoulder to left_elbow
    (13, 15),  # left_elbow to left_wrist
    (12, 14),  # right_shoulder to right_elbow
    (14, 16),  # right_elbow to right_wrist
    (11, 23),  # left_shoulder to left_hip
    (12, 24),  # right_shoulder to right_hip
    (23, 24),  # left_hip to right_hip
    (23, 25),  # left_hip to left_knee
    (24, 26),  # right_hip to right_knee
    (25, 27),  # left_knee to left_ankle
    (26, 28)   # right_knee to right_ankle
]

def detect_pose(landmarks):
    l = {}
    for name, idx in IDXS.items():
        if idx < len(landmarks):
            l[name] = landmarks[idx]
        else:
            l[name] = None

    # Squat
    if l["left_knee"] and l["left_hip"] and l["right_knee"] and l["right_hip"]:
        left_squat_diff = l["left_knee"].y - l["left_hip"].y
        right_squat_diff = l["right_knee"].y - l["right_hip"].y
        if left_squat_diff < 0.1 and right_squat_diff < 0.1:
            return "squat"

    # Jumping Jacks

    #if l["left_wrist"]


    # 


    return "none"

def draw_landmarks(rgb_image, detection_result):

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
        # Draw landmark points with coordinates
        for i, landmark in enumerate(pose_landmarks):
            if not i in LANDMARK_NAMES.keys():
                continue
            cx = int(landmark.x * annotated_image.shape[1])
            cy = int(landmark.y * annotated_image.shape[0])
            cv2.circle(annotated_image, (cx, cy), 4, (0, 0, 255), -1)
            
            # Draw coordinates above and to the left
            coord_text = f"({landmark.x:.2f},{landmark.y:.2f},{landmark.z:.2f})"
            cv2.putText(annotated_image, coord_text, (cx - 10, cy - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5)
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

        frame = cv2.resize(frame, (1200, 900))
        frame = cv2.flip(frame, 1)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        landmarker.detect_async(mp_image, int(cap.get(cv2.CAP_PROP_POS_MSEC)))

        annotated_frame = frame.copy()
        pose_str = "?"
        with result_lock:
            if latest_result and latest_result.pose_landmarks:
                annotated_frame = draw_landmarks(annotated_frame, latest_result)
        
                landmarks = latest_result.pose_landmarks
                for pose_idx, pose in enumerate(landmarks):
                #     print(f"\n--- Pose {pose_idx} ---")
                    
                #     for idx, landmark in enumerate(pose):
                #         if idx in LANDMARK_NAMES.keys():
                #             name = LANDMARK_NAMES[idx] if idx < len(LANDMARK_NAMES) else f"landmark_{idx}"
                #             print(f"{name:25} ({landmark.x:6.2f}, {landmark.y:6.2f}, {landmark.z:6.2f})")
                
                    pose_str = detect_pose(pose)
                    print(pose_str)

        cv2.putText(
            annotated_frame,
            pose_str,
            (5, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            4,
            (255, 0, 0),
            10,
        )

        image = cv2.resize(annotated_frame, (800, 600))

        _, encoded_image = cv2.imencode(".jpg", cv2.resize(annotated_frame, (400, 300)))



        if len(encoded_image) <= 65507:
            client_socket.sendto(encoded_image, (SERVER_IP, SERVER_PORT))
        else:
            print("Frame too large, skipping")

        cv2.imshow("Image", image)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        

cv2.destroyAllWindows()

cap.release()


