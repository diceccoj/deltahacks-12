import socket
import threading
import cv2
import numpy as np
import mediapipe as mp
import math
import signal
import sys
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import queue

# Global state for each camera
camera_states = {
    0: {'latest_result': None, 'lock': threading.Lock(), 'latest_frame': None},
    1: {'latest_result': None, 'lock': threading.Lock(), 'latest_frame': None}
}
running = True

screen_width = 730
screen_height = 410

SERVER_IP = "127.0.0.1"
PORTS = {0: 4242, 1: 4243}
sockets = {
    0: socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
    1: socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
}

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
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26),
    (25, 27), (26, 28)
]

def signal_handler(sig, frame):
    global running
    print("\n\nExiting gracefully...")
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def detect_pose(landmarks):
    l = {}
    for name, idx in IDXS.items():
        if idx < len(landmarks):
            l[name] = landmarks[idx]
        else:
            l[name] = None

    if not l["left_hip"] or not l["right_hip"] or not l["left_shoulder"] or not l["right_shoulder"]:
        return "none"

    hip_height = (l["left_hip"].y + l["right_hip"].y) / 2
    hip_x = (l["left_hip"].x + l["right_hip"].x) / 2
    shoulder_height = (l["left_shoulder"].y + l["right_shoulder"].y) / 2
    shoulder_x = (l["left_shoulder"].x + l["right_shoulder"].x) / 2
    torso_height = math.sqrt((shoulder_height - hip_height) ** 2 + (shoulder_x - hip_x) ** 2)

    if l["left_wrist"] and l["left_shoulder"] and l["right_wrist"] and l["right_shoulder"]:
        torso_width = abs(l["left_shoulder"].x - l["right_shoulder"].x)
        if torso_width > torso_height * 0.3:
            if l["left_wrist"].x < l["left_shoulder"].x and l["right_wrist"].x < l["right_shoulder"].x - torso_height * 0.4:
                return "place_left"
            if l["left_wrist"].x > l["left_shoulder"].x + torso_height * 0.4 and l["right_wrist"].x > l["right_shoulder"].x:
                return "place_right"

    if l["left_knee"] and l["left_hip"] and l["right_knee"] and l["right_hip"]:
        left_squat_diff = l["left_knee"].y - l["left_hip"].y
        right_squat_diff = l["right_knee"].y - l["right_hip"].y
        if abs(shoulder_height - hip_height) > torso_height * 0.75:
            if left_squat_diff < 0.1 and right_squat_diff < 0.1:
                return "squat"

    if l["left_wrist"] and l["right_wrist"] and l["left_ankle"] and l["right_ankle"] and \
       l["right_shoulder"] and l["left_shoulder"] and l["left_hip"] and l["right_hip"]:
        elbow_distance = abs(l["left_elbow"].x - l["right_elbow"].x)
        wrist_distance = abs(l["left_wrist"].x - l["right_wrist"].x)
        ankle_distance = abs(l["left_ankle"].x - l["right_ankle"].x)
        knee_distance = abs(l["left_knee"].x - l["right_knee"].x)
        right_wrist_height = l["right_wrist"].y
        left_wrist_height = l["left_wrist"].y

        # Checks if elbows are wide and knees are wide
        if elbow_distance > torso_height * 0.8 and knee_distance > torso_height * 0.35:
            if wrist_distance < elbow_distance and left_wrist_height < shoulder_height and right_wrist_height < shoulder_height:
                if left_wrist_height < l["left_ankle"].y and right_wrist_height < l["right_ankle"].y:
                    return "jumping_jacks_open"

        if left_wrist_height > hip_height - torso_height * 0.2 and right_wrist_height > hip_height - torso_height * 0.2:
            if left_wrist_height < l["left_ankle"].y and right_wrist_height < l["right_ankle"].y:
                if wrist_distance < torso_height and ankle_distance < torso_height * 0.5:
                    return "jumping_jacks_closed"

    if l["left_knee"] and l["left_hip"] and l["left_ankle"] and l["right_knee"] and l["right_hip"] and l["right_ankle"]:
        ankle_to_knee_left = abs(l["left_ankle"].y - l["left_knee"].y)
        ankle_to_knee_right = abs(l["right_ankle"].y - l["right_knee"].y)
        ankle_to_ankle_distance = abs(l["left_ankle"].x - l["right_ankle"].x)
        torso_width = abs(l["left_shoulder"].x - l["right_shoulder"].x) + abs(l["left_hip"].x - l["right_hip"].x) / 2

        if ankle_to_knee_right > torso_height * 0.1:
            if ankle_to_ankle_distance > torso_height:
                if torso_width < torso_height * 0.3:
                    return "right lunge"
        
        if ankle_to_knee_left > torso_height * 0.1:
            if ankle_to_ankle_distance > torso_height:
                if torso_width < torso_height * 0.3:
                    return "left lunge"

    if l["left_wrist"] and l["right_wrist"] and l["left_shoulder"] and l["right_shoulder"] and \
       l["left_hip"] and l["right_hip"] and l["left_hip"] and l["right_hip"]:
        ankle_height = (l["left_ankle"].y + l["right_ankle"].y) / 2
        shoulder_height = (l["left_shoulder"].y + l["right_shoulder"].y) / 2
        hip_height = (l["left_hip"].y + l["right_hip"].y) / 2
        wrist_height = (l["left_wrist"].y + l["right_wrist"].y) / 2

        if abs(shoulder_height - hip_height) < 0.1 and abs(hip_height - ankle_height) < 0.1:
            if abs(wrist_height - shoulder_height) < 0.2:
                return "push_up_down"

        if shoulder_height < hip_height and abs(shoulder_height - hip_height) < 0.2 and abs(hip_height - ankle_height) < 0.2:
            if wrist_height - shoulder_height > 0.1:
                return "push_up"

    if l["left_ankle"] and l["right_ankle"]:
        ankle_distance = abs(l["left_ankle"].x - l["right_ankle"].x)
        ankle_height = (l["left_ankle"].y + l["right_ankle"].y) / 2
        if ankle_distance < torso_height * 0.5:
            if abs(hip_height - ankle_height) > torso_height * 1.1:
                return "standing"

    return "none"

def draw_landmarks(rgb_image, detection_result):
    pose_landmarks_list = detection_result.pose_landmarks
    annotated_image = np.copy(rgb_image)
    for pose_landmarks in pose_landmarks_list:
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
        for i, landmark in enumerate(pose_landmarks):
            if not i in LANDMARK_NAMES.keys():
                continue
            cx = int(landmark.x * annotated_image.shape[1])
            cy = int(landmark.y * annotated_image.shape[0])
            cv2.circle(annotated_image, (cx, cy), 4, (0, 0, 255), -1)
    return annotated_image

def create_result_callback(camera_id):
    """Factory function to create callback for specific camera"""
    def result_cb(result, output_image: mp.Image, timestamp_ms: int):
        with camera_states[camera_id]['lock']:
            camera_states[camera_id]['latest_result'] = result
    return result_cb

def process_camera(camera_id):
    """Process a single camera in a separate thread (NO cv2.imshow here)"""
    global running
    
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_id}")
        return
    
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path="pose_landmarker_heavy.task"),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=create_result_callback(camera_id))
    
    try:
        with PoseLandmarker.create_from_options(options) as landmarker:
            print(f"Camera {camera_id} processing started")
            counter = 0
            
            while running:
                counter += 33
                ret, frame = cap.read()
                
                if not ret:
                    print(f"Error: Camera {camera_id} failed to capture")
                    break
                
                frame = cv2.resize(frame, (1200, 900))
                frame = cv2.flip(frame, 1)
                
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                landmarker.detect_async(mp_image, counter)
                
                annotated_frame = frame.copy()
                pose_str = "?"
                
                with camera_states[camera_id]['lock']:
                    if camera_states[camera_id]['latest_result'] and \
                       camera_states[camera_id]['latest_result'].pose_landmarks:
                        annotated_frame = draw_landmarks(
                            annotated_frame, 
                            camera_states[camera_id]['latest_result']
                        )
                        landmarks = camera_states[camera_id]['latest_result'].pose_landmarks
                        for pose in landmarks:
                            pose_str = detect_pose(pose)
                
                # Add camera ID and pose to display - smaller, nicer font
                cv2.putText(annotated_frame, f"Camera {camera_id}: {pose_str}",
                           (5, 50), cv2.FONT_HERSHEY_DUPLEX, 1.5, (255, 100, 0), 3)
                cv2.putText(annotated_frame, "Press 'q' or ESC to exit",
                           (5, annotated_frame.shape[0] - 15),
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (100, 200, 255), 2)
                
                # Store the processed frame (don't display here!)
                with camera_states[camera_id]['lock']:
                    camera_states[camera_id]['latest_frame'] = cv2.resize(annotated_frame, (screen_width, screen_height))
                
                # Send to different port for each camera
                if len(pose_str) <= 65507:
                    sockets[camera_id].sendto(
                        pose_str.encode('utf-8'), 
                        (SERVER_IP, PORTS[camera_id])
                    )
                    
    finally:
        cap.release()
        sockets[camera_id].close()
        print(f"Camera {camera_id} processing stopped")

def main():
    global running
    
    print("\n=== DUAL CAMERA POSE DETECTION ===")
    print("Camera 0 -> Port 4242")
    print("Camera 1 -> Port 4243")
    print("\nEXIT OPTIONS:")
    print("- Press 'q' to quit")
    print("- Press 'ESC' to quit")
    print("- Press Ctrl+C to quit")
    print("- Click X on any window to quit")
    print("===================================\n")
    
    # Create threads for each camera
    thread0 = threading.Thread(target=process_camera, args=(0,), daemon=True)
    thread1 = threading.Thread(target=process_camera, args=(1,), daemon=True)
    
    # Start both threads
    thread0.start()
    thread1.start()
    
    # Main thread handles display (cv2.imshow must be in main thread)
    window0 = "Camera 0"
    window1 = "Camera 1"
    
    # Create windows and position them side by side
    cv2.namedWindow(window0, cv2.WINDOW_NORMAL)
    cv2.namedWindow(window1, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window0, screen_width, screen_height)
    cv2.resizeWindow(window1, screen_width, screen_height)
    cv2.moveWindow(window0, 0, 0)  # Left window
    cv2.moveWindow(window1, screen_width + 10, 0)  # Right window, with small gap
    
    try:
        while running:
            # Get latest frames from both cameras
            frame0 = None
            frame1 = None
            
            with camera_states[0]['lock']:
                if camera_states[0]['latest_frame'] is not None:
                    frame0 = camera_states[0]['latest_frame'].copy()
            
            with camera_states[1]['lock']:
                if camera_states[1]['latest_frame'] is not None:
                    frame1 = camera_states[1]['latest_frame'].copy()
            
            # Display frames
            if frame0 is not None:
                cv2.imshow(window0, frame0)
            if frame1 is not None:
                cv2.imshow(window1, frame1)
            
            # Check for exit keys
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:  # q or ESC
                print("\nExiting...")
                running = False
                break
            
            # Check if windows were closed
            try:
                if cv2.getWindowProperty(window0, cv2.WND_PROP_VISIBLE) < 1 or \
                   cv2.getWindowProperty(window1, cv2.WND_PROP_VISIBLE) < 1:
                    print("\nWindow closed, exiting...")
                    running = False
                    break
            except:
                # Window might not exist yet
                pass
                
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt detected...")
        running = False
    finally:
        cv2.destroyAllWindows()
        # Give threads time to clean up
        thread0.join(timeout=2)
        thread1.join(timeout=2)
        print("All cameras shut down")

if __name__ == "__main__":
    main()