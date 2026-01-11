import socket
import threading
import cv2
import numpy as np
import mediapipe as mp
import math
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

latest_result = None
result_lock = threading.Lock()

screen_width = 1920
screen_height = 1080

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

    # Check for essential landmarks
    if not l["left_hip"] or not l["right_hip"] or not l["left_shoulder"] or not l["right_shoulder"]:
        return "none"

    # Calculate torso height
    hip_height = (l["left_hip"].y + l["right_hip"].y) / 2
    hip_x = (l["left_hip"].x + l["right_hip"].x) / 2

    shoulder_height = (l["left_shoulder"].y + l["right_shoulder"].y) / 2
    shoulder_x = (l["left_shoulder"].x + l["right_shoulder"].x) / 2

    torso_height = math.sqrt((shoulder_height - hip_height) ** 2 + (shoulder_x - hip_x) ** 2)

    # Place Left / Right
    if l["left_wrist"] and l["left_shoulder"] and l["right_wrist"] and l["right_shoulder"]:

        torso_width = abs(l["left_shoulder"].x - l["right_shoulder"].x)

        if torso_width > torso_height * 0.3:
            # Place Left
            if l["left_wrist"].x < l["left_shoulder"].x and l["right_wrist"].x < l["right_shoulder"].x - torso_height * 0.4:
                return "place_left"
            # Place Right
            if l["left_wrist"].x > l["left_shoulder"].x + torso_height * 0.4 and l["right_wrist"].x > l["right_shoulder"].x:
                return "place_right"

    # Squat
    if l["left_knee"] and l["left_hip"] and l["right_knee"] and l["right_hip"]:
        left_squat_diff = l["left_knee"].y - l["left_hip"].y
        right_squat_diff = l["right_knee"].y - l["right_hip"].y

        # Checks if chest is upright
        if abs(shoulder_height - hip_height) > torso_height * 0.75:
            if left_squat_diff < 0.1 and right_squat_diff < 0.1:
                return "squat"

    # Jumping Jacks
    if l["left_wrist"] and l["right_wrist"] and l["left_ankle"] and l["right_ankle"] and \
       l["right_shoulder"] and l["left_shoulder"] and l["left_hip"] and l["right_hip"]:

        elbow_distance = abs(l["left_elbow"].x - l["right_elbow"].x)
        wrist_distance = abs(l["left_wrist"].x - l["right_wrist"].x)
        ankle_distance = abs(l["left_ankle"].x - l["right_ankle"].x)
        right_wrist_height = l["right_wrist"].y
        left_wrist_height = l["left_wrist"].y

        # print(f"wrist_distance={wrist_distance:.4f}, ankle_distance={ankle_distance:.4f}, torso_height={torso_height:.4f}")
        # sys.stdout.flush()

        # checks if elbows are out and ankles are apart
        if elbow_distance > torso_height * 0.8 and ankle_distance > torso_height * 0.65:
            # checks if wrists are closer than elbows and above nose height
            if wrist_distance < elbow_distance and left_wrist_height < shoulder_height and right_wrist_height < shoulder_height:
                # check if wrists are above ankles
                if left_wrist_height < l["left_ankle"].y and right_wrist_height < l["right_ankle"].y:
                    return "jumping_jacks_open"

        # checks if wrists are below hips
        if left_wrist_height > hip_height - torso_height * 0.2 and right_wrist_height > hip_height - torso_height * 0.2:
            # checks if wrists are above ankles
            if left_wrist_height < l["left_ankle"].y and right_wrist_height < l["right_ankle"].y:
                # checks if wrists and ankles are close together
                if wrist_distance < torso_height and ankle_distance < torso_height * 0.5:
                    return "jumping_jacks_closed"
                
    # Lunges
    if l["left_knee"] and l["left_hip"] and l["left_ankle"] and l["right_knee"] and l["right_hip"] and l["right_ankle"]:

        ankle_to_knee_left = abs(l["left_ankle"].y - l["left_knee"].y)
        ankle_to_knee_right = abs(l["right_ankle"].y - l["right_knee"].y)

        ankle_to_ankle_distance = abs(l["left_ankle"].x - l["right_ankle"].x)

        torso_width = abs(l["left_shoulder"].x - l["right_shoulder"].x) + abs(l["left_hip"].x - l["right_hip"].x) / 2

        # Right Lunge
        if ankle_to_knee_right > torso_height * 0.1:
            if ankle_to_ankle_distance > torso_height:
                if torso_width < torso_height * 0.3:
                    return "right lunge"
            
        # Left Lunge
        if ankle_to_knee_left > torso_height * 0.1:
            if ankle_to_ankle_distance > torso_height:
                if torso_width < torso_height * 0.3:
                    return "left lunge"
            
        
    # Push-up
    if l["left_wrist"] and l["right_wrist"] and l["left_shoulder"] and l["right_shoulder"] and \
       l["left_hip"] and l["right_hip"] and l["left_hip"] and l["right_hip"]:
        
        ankle_height = (l["left_ankle"].y + l["right_ankle"].y) / 2
        shoulder_height = (l["left_shoulder"].y + l["right_shoulder"].y) / 2
        hip_height = (l["left_hip"].y + l["right_hip"].y) / 2
        wrist_height = (l["left_wrist"].y + l["right_wrist"].y) / 2


        #  Check if body is horizontal
        if abs(shoulder_height - hip_height) < 0.1 and abs(hip_height - ankle_height) < 0.1:
            # Check if wrists are close to shoulders height
            if abs(wrist_height - shoulder_height) < 0.2:
                return "push_up_down"

        # Check if body is on a slight slant
        if shoulder_height < hip_height and abs(shoulder_height - hip_height) < 0.2 and abs(hip_height - ankle_height) < 0.2:
            # Check if wrists are below shoulders height
            if wrist_height - shoulder_height > 0.1:
                return "push_up"
            
    # Standing
    if l["left_ankle"] and l["right_ankle"]:

        ankle_distance = abs(l["left_ankle"].x - l["right_ankle"].x)
        ankle_height = (l["left_ankle"].y + l["right_ankle"].y) / 2
            
        # checks if wrists and ankles are close together
        if ankle_distance < torso_height * 0.5:
            if abs(hip_height - ankle_height) > torso_height * 1.1:
                return "standing"


    # No recognized pose
    return "none"

def get_slope(x1, y1, x2, y2):
    """
    Return slope (dy/dx) between points (x1, y1) and (x2, y2).
    Returns math.inf for a vertical line.
    """
    if x2 == x1:
        return math.inf
    return (y2 - y1) / (x2 - x1)

def get_midpoint(x1, y1, x2, y2):
    """
    Return midpoint between points (x1, y1) and (x2, y2).
    """
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    return mx, my

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
            
            # # Draw coordinates above and to the left
            # coord_text = f"({landmark.x:.2f},{landmark.y:.2f},{landmark.z:.2f})"
            # cv2.putText(annotated_image, coord_text, (cx - 10, cy - 10),
            #            cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5)
    return annotated_image


def result_cb(result, output_image: mp.Image, timestamp_ms: int):
    global latest_result
    with result_lock:
        latest_result = result

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="pose_landmarker_heavy.task"),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=result_cb)

print("done initializing options!")

with PoseLandmarker.create_from_options(options) as landmarker:
    print(f"Landmarker: {landmarker}")
    counter = 0
    while True:
        counter += 33
        ret, frame = cap.read()

        if not ret:
            print("Error: failed to capture image")
            break

        frame = cv2.resize(frame, (1200, 900))
        frame = cv2.flip(frame, 1)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        landmarker.detect_async(mp_image, counter)

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
                    # print(pose_str)

        cv2.putText(
            annotated_frame,
            pose_str,
            (5, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            4,
            (255, 0, 0),
            10,
        )

        image = cv2.resize(annotated_frame, (screen_width, screen_height))

        _, encoded_image = cv2.imencode(".jpg", cv2.resize(annotated_frame, (screen_width, screen_height)))



        if len(pose_str) <= 65507:
            client_socket.sendto(pose_str.encode('utf-8'), (SERVER_IP, SERVER_PORT))
        else:
            print("Frame too large, skipping")

        cv2.imshow("Image", image)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        

cv2.destroyAllWindows()

cap.release()


