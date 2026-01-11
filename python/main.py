import socket
import threading
import cv2
import numpy as np
import mediapipe as mp
import math
import signal
import sys
from mediapipe.tasks import python
from mediapipe.tasks.python.vision.core.image import Image as MPImage
from mediapipe.tasks.python import vision
import queue
import struct

def list_available_cameras(max_test=10):
    """Detect all available cameras"""
    available_cameras = []
    
    # Determine the correct backend based on OS
    import platform
    system = platform.system()
    
    for i in range(max_test):
        # Use appropriate backend for each OS
        if system == "Windows":
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        elif system == "Darwin":  # macOS
            cap = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
        else:  # Linux
            cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
        
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"Camera {i}: {int(width)}x{int(height)} @ {fps} FPS")
                available_cameras.append(i)
            cap.release()
    
    print(f"Found {len(available_cameras)} camera(s): {available_cameras}")
    return available_cameras

# Detect available cameras
available_cameras = list_available_cameras()

if len(available_cameras) == 0:
    print("\nERROR: No cameras found!")
    print("Please connect at least one camera and try again.")
    sys.exit(1)

# Use the first two available cameras (or just one if only one is available)
camera_ids = available_cameras[:2]
print(f"\nUsing cameras: {camera_ids}")

# Global state - dynamically create based on available cameras
camera_states = {}
running = True

screen_width = 1920
screen_height = 1080

SERVER_IP = "127.0.0.1"
# Dynamically assign ports based on camera IDs
PORTS = {}
sockets = {}

for idx, cam_id in enumerate(camera_ids):
    camera_states[cam_id] = {
        'latest_result': None, 
        'lock': threading.Lock(), 
        'latest_frame': None,
        'seg_mask': None
    }
    PORTS[cam_id] = 4242 + idx  # First camera: 4242, second: 4243
    sockets[cam_id] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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

    # normalize falsy / missing landmarks to False; invalidate landmarks with out-of-range coords
    for name, val in list(l.items()):
        if not val:
            l[name] = False
            continue
        try:
            x = float(val.x)
            y = float(val.y)
        except Exception:
            l[name] = False
            continue
        
         # valid if both x and y are between 0 and 1, with some margin
        off_screen_margin = 0.15  # allow some margin for off-screen detection
        if not (-off_screen_margin < x < 1 + off_screen_margin and -off_screen_margin < y < 1 + off_screen_margin):
            l[name] = False
    
    if not l["left_hip"] or not l["right_hip"] or not l["left_shoulder"] or not l["right_shoulder"] or \
       not l["left_knee"] or not l["right_knee"] or not l["left_ankle"] or not l["right_ankle"] or \
       not l["left_wrist"] or not l["right_wrist"]:
        return "none"

    hip_height = (l["left_hip"].y + l["right_hip"].y) / 2
    hip_x = (l["left_hip"].x + l["right_hip"].x) / 2
    shoulder_height = (l["left_shoulder"].y + l["right_shoulder"].y) / 2
    shoulder_x = (l["left_shoulder"].x + l["right_shoulder"].x) / 2
    torso_height = math.sqrt((shoulder_height - hip_height) ** 2 + (shoulder_x - hip_x) ** 2)

    torso_width = abs(l["left_shoulder"].x - l["right_shoulder"].x)

    # Checks if player is standing upright
    if abs(shoulder_height - hip_height) > torso_height * 0.85:

        # Detect all moves that require standing upright

        # Detect side arm raises
        if torso_width > torso_height * 0.3:
            if l["left_wrist"].x < l["left_shoulder"].x and l["right_wrist"].x < l["right_shoulder"].x - torso_height * 0.4:
                return "place_left"
            if l["left_wrist"].x > l["left_shoulder"].x + torso_height * 0.4 and l["right_wrist"].x > l["right_shoulder"].x:
                return "place_right"

        # Detect squats
        left_squat_diff = l["left_knee"].y - l["left_hip"].y
        right_squat_diff = l["right_knee"].y - l["right_hip"].y
        if abs(shoulder_height - hip_height) > torso_height * 0.75:
            if left_squat_diff < 0.1 and right_squat_diff < 0.1:
                return "squat"

        # Detect jumping jacks
        elbow_distance = abs(l["left_elbow"].x - l["right_elbow"].x)
        wrist_distance = abs(l["left_wrist"].x - l["right_wrist"].x)
        ankle_distance = abs(l["left_ankle"].x - l["right_ankle"].x)
        knee_distance = abs(l["left_knee"].x - l["right_knee"].x)
        right_wrist_height = l["right_wrist"].y
        left_wrist_height = l["left_wrist"].y

        if elbow_distance > torso_height * 0.8 and knee_distance > torso_height * 0.35:
            if wrist_distance < elbow_distance and left_wrist_height < shoulder_height and right_wrist_height < shoulder_height:
                if left_wrist_height < l["left_ankle"].y and right_wrist_height < l["right_ankle"].y:
                    return "jumping_jacks_open"

        if left_wrist_height > hip_height - torso_height * 0.2 and right_wrist_height > hip_height - torso_height * 0.2:
            if left_wrist_height < l["left_ankle"].y and right_wrist_height < l["right_ankle"].y:
                if wrist_distance < torso_height and ankle_distance < torso_height * 0.5:
                    return "jumping_jacks_closed"

        # Detect lunges
        ankle_to_knee_left = abs(l["left_ankle"].x - l["left_knee"].x)
        ankle_to_knee_right = abs(l["right_ankle"].x - l["right_knee"].x)
        ankle_to_ankle_distance = abs(l["left_ankle"].x - l["right_ankle"].x)
        torso_width = abs(l["left_shoulder"].x - l["right_shoulder"].x) + abs(l["left_hip"].x - l["right_hip"].x) / 2

        if ankle_to_knee_right > torso_height * 0.2:
            if ankle_to_ankle_distance > torso_height:
                if torso_width < torso_height * 0.3:
                    return "right lunge"
        
        if ankle_to_knee_left > torso_height * 0.1:
            if ankle_to_ankle_distance > torso_height:
                if torso_width < torso_height * 0.3:
                    return "left lunge"
                    
        # Knee ups detection (new)
        dist = l["left_knee"].y - l["left_hip"].y
        if dist < torso_height * 0.1:
            return "knee_up_l"

        dist = l["right_knee"].y - l["right_hip"].y
        if dist < torso_height * 0.1:
            return "knee_up_r"

        ankle_distance = abs(l["left_ankle"].x - l["right_ankle"].x)
        ankle_height = (l["left_ankle"].y + l["right_ankle"].y) / 2
        if ankle_distance < torso_height * 0.5:
            if abs(hip_height - ankle_height) > torso_height * 1.1:
                return "standing"

    else:
        # Detect push-ups
            ankle_height = (l["left_ankle"].y + l["right_ankle"].y) / 2
            wrist_height = (l["left_wrist"].y + l["right_wrist"].y) / 2

            ankle_x = (l["left_ankle"].x + l["right_ankle"].x) / 2
            wrist_x = (l["left_wrist"].x + l["right_wrist"].x) / 2

            wrist_to_ankle = abs(wrist_x - ankle_x)

            if wrist_to_ankle > torso_height * 1.5:

                if abs(shoulder_height - hip_height) < 0.1 and abs(hip_height - ankle_height) < 0.1:
                    if abs(wrist_height - shoulder_height) < 0.2:
                        return "push_up_down"

                if shoulder_height < hip_height and abs(shoulder_height - hip_height) < 0.2 and abs(hip_height - ankle_height) < 0.2:
                    if wrist_height - shoulder_height > 0.1:
                        return "push_up"

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

def encode_seg_mask(seg_masks):
    if seg_masks == None:
        black_mask = np.zeros((120, 160), dtype=np.uint8)
        return cv2.imencode('.jpg', black_mask, [cv2.IMWRITE_JPEG_QUALITY, 75])
    mask_array = seg_masks[0].numpy_view()
    binary_mask = (mask_array > 0.5).astype(np.uint8) * 255
    small_mask = cv2.resize(binary_mask, (160, 120))
    return cv2.imencode('.jpg', small_mask, [cv2.IMWRITE_JPEG_QUALITY, 75])

def process_camera(camera_id):
    """Process a single camera in a separate thread (NO cv2.imshow here)"""
    global running
    
    # Determine the correct backend based on OS
    import platform
    system = platform.system()
    
    if system == "Windows":
        cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
    elif system == "Darwin":  # macOS
        cap = cv2.VideoCapture(camera_id, cv2.CAP_AVFOUNDATION)
    else:  # Linux
        cap = cv2.VideoCapture(camera_id, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_id}")
        return
    
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path="pose_landmarker_full.task"),
        running_mode=VisionRunningMode.LIVE_STREAM,
        output_segmentation_masks=True,
        result_callback=create_result_callback(camera_id))
    
    try:
        with PoseLandmarker.create_from_options(options) as landmarker:
            print(f"Camera {camera_id} processing started (Port: {PORTS[camera_id]})")
            counter = 0
            
            while running:
                counter += 33
                ret, frame = cap.read()
                
                if not ret:
                    print(f"Error: Camera {camera_id} failed to capture")
                    break
                
                frame = cv2.resize(frame, (1200//2, 900//2))
                frame = cv2.flip(frame, 1)
                
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                landmarker.detect_async(mp_image, counter)
                
                seg_masks = None
                annotated_frame = frame.copy()
                pose_str = "?"
                
                with camera_states[camera_id]['lock']:
                    if camera_states[camera_id]['latest_result'] and \
                       camera_states[camera_id]['latest_result'].pose_landmarks:
                        seg_masks = camera_states[camera_id]['latest_result'].segmentation_masks
                        annotated_frame = draw_landmarks(
                            annotated_frame, 
                            camera_states[camera_id]['latest_result']
                        )
                        landmarks = camera_states[camera_id]['latest_result'].pose_landmarks
                        for pose in landmarks:
                            pose_str = detect_pose(pose)
    
                # Add camera ID and pose to display
                cv2.putText(annotated_frame, f"Camera {camera_id}: {pose_str}",
                           (5, 50), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 100, 0), 3)
                cv2.putText(annotated_frame, "Press 'q' or ESC to exit",
                           (5, annotated_frame.shape[0] - 15),
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (100, 200, 255), 2)

                # Store the processed frame
                with camera_states[camera_id]['lock']:
                    camera_states[camera_id]['latest_frame'] = cv2.resize(annotated_frame, (screen_width, screen_height))
                    camera_states[camera_id]['seg_mask'] = seg_masks

                # Send segmentation mask
                seg_success, seg_encoded = encode_seg_mask(seg_masks)
                if seg_success:
                    mask_bytes = seg_encoded.tobytes()
                    header = b'MASK' + struct.pack('I', len(mask_bytes))
                    mask_port = PORTS[camera_id] + 100  # e.g., 4342, 4343
                    sockets[camera_id].sendto(header + mask_bytes, (SERVER_IP, mask_port))

                # Send pose data
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
    
    print("\n=== POSE DETECTION ===")
    for cam_id in camera_ids:
        print(f"Camera {cam_id} -> Port {PORTS[cam_id]} (Mask: {PORTS[cam_id] + 100})")
    print("\nEXIT OPTIONS:")
    print("- Press 'q' to quit")
    print("- Press 'ESC' to quit")
    print("- Press Ctrl+C to quit")
    print("- Click X on any window to quit")
    print("======================\n")
    
    # Create threads for each available camera
    threads = []
    for cam_id in camera_ids:
        thread = threading.Thread(target=process_camera, args=(cam_id,), daemon=True)
        thread.start()
        threads.append(thread)
    
    # Create windows for display
    windows = {}
    for idx, cam_id in enumerate(camera_ids):
        window_name = f"Camera {cam_id}"
        windows[cam_id] = window_name
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, screen_width, screen_height)
        # Position windows side by side
        cv2.moveWindow(window_name, idx * (screen_width + 10), 0)
    
    try:
        while running:
            # Display all camera feeds
            for cam_id in camera_ids:
                with camera_states[cam_id]['lock']:
                    if camera_states[cam_id]['latest_frame'] is not None:
                        frame = camera_states[cam_id]['latest_frame'].copy()
                        cv2.imshow(windows[cam_id], frame)
            
            # Close windows for cameras that aren't being used
            # This handles the case where we have fewer cameras than expected
            all_possible_cameras = list(range(10))
            for cam_id in all_possible_cameras:
                if cam_id not in camera_ids:
                    window_name = f"Camera {cam_id}"
                    try:
                        # Try to destroy the window if it exists
                        cv2.destroyWindow(window_name)
                    except:
                        pass
            
            # Check for exit keys
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                print("\nExiting...")
                running = False
                break
            
            # Check if any window was closed
            try:
                for window_name in windows.values():
                    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                        print("\nWindow closed, exiting...")
                        running = False
                        break
            except:
                pass
                
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt detected...")
        running = False
    finally:
        cv2.destroyAllWindows()
        # Wait for all threads to finish
        for thread in threads:
            thread.join(timeout=2)
        print("All cameras shut down")

if __name__ == "__main__":
    main()