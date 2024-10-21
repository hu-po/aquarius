import cv2
import os

OUTPUT_DIR = "/tmp"
FPS = 30
FRAME_BUFFERSIZE = 2
# RESOLUTION = (3840, 2160)
RESOLUTION = (1920, 1080)
# RESOLUTION = (640, 480)

def list_devices():
    # This function attempts to open video capture devices in a range
    # and lists them if they are available.
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if not cap.read()[0]:
            cap.release()
            break
        else:
            print(f"Found video device: /dev/video{index}")
            arr.append(index)
        cap.release()
        index += 1
    return arr

def save_frame(device_index, filename):
    # This function saves a single frame from the specified device.
    cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
    if not cap.isOpened():
        print(f"Failed to open device /dev/video{device_index}")
        return False
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(filename, frame)
        print(f"Saved frame to {filename}")
    else:
        print("Failed to capture frame")
    cap.release()
    return ret

def record_video(device_index, filename, duration=5):
    cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
    cap.set(cv2.CAP_PROP_BUFFERSIZE, FRAME_BUFFERSIZE)
    if not cap.isOpened():
        print(f"Failed to open device /dev/video{device_index}")
        return False
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(filename, fourcc, FPS, RESOLUTION)
    frames_to_record = int(cap.get(cv2.CAP_PROP_FPS) * duration)
    print(f"Recording {frames_to_record} frames to {filename}")
    for _ in range(frames_to_record):
        ret, frame = cap.read()
        if ret:
            out.write(frame)
        else:
            break
    cap.release()
    out.release()
    print("Recording finished")
    return True

if __name__ == "__main__":
    devices = list_devices()
    if devices:
        for device in devices:
            try:
                save_frame(device, os.path.join(OUTPUT_DIR, f"device_{device}.png"))
                record_video(device, os.path.join(OUTPUT_DIR, f"device_{device}.mp4"), 5)
            except Exception as e:
                print(f"Failed to process device {device}: {str(e)}")
    else:
        print("No video devices found")