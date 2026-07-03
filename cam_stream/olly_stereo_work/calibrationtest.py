# Used for debugging calibration errors

import numpy as np
import cv2 as cv

# chessboardSize = (9,6)

# # Latest pic registered in python works
# img = cv.imread("olly_stereo_work/chessboard.jpg")

# gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

# cv.imshow("gray", gray)

# ret, corners = cv.findChessboardCorners(gray, chessboardSize, None)

# print(ret)
# print(corners)

# cv.waitKey(0)
# cv.destroyAllWindows()

cap = cv.VideoCapture(1, cv.CAP_DSHOW)

# Tests ports for camera
# for i in range(10):
#     cap = cv.VideoCapture(i, cv.CAP_ANY)
#     if cap.isOpened():
#         print("Camera at index", i)
#         cap.release()

cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*"MJPG"))
cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
# Debugging lines
print(cap.get(cv.CAP_PROP_FRAME_WIDTH))
print(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

while cap.isOpened():

    success, img = cap.read()
    h, w, _ = img.shape
    mid = w // 2
    
    # Test orientation then recalibrate
    left = img[:, mid:]
    right  = img[:, :mid]
    
    cv.imshow("Left", left)
    cv.imshow("Right", right)

    # Wait for keyboard press
    key = cv.waitKey(5)

    # Exit on escape key
    if key == 27:
        break