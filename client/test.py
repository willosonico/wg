import cv2

pipeline = "v4l2src device=/dev/video10 \
              ! videoconvert ! videorate \
              ! video/x-raw,format=BGR,framerate=30/1"

print (pipeline)

cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

while True:
    ret, frame = cap.read()
    print(ret)
