import cv2

def capture_image():
    # OpenCV logic to capture image from the camera
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    return frame
