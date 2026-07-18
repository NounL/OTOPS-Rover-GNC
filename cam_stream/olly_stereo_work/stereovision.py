# This applies results from calibration, undistort and rectification visualizing this
# this not important but applying some of the code in here to a depth map is

import numpy as np
import cv2 as cv

# Camera parameters to undistort and rectify images
cv_file = cv.FileStorage()
cv_file.open('olly_stereo_work/stereoMap.xml', cv.FileStorage_READ)

stereoMapL_x = cv_file.getNode('stereoMapL_x').mat()
stereoMapL_y = cv_file.getNode('stereoMapL_y').mat()
stereoMapR_x = cv_file.getNode('stereoMapR_x').mat()
stereoMapR_y = cv_file.getNode('stereoMapR_y').mat()

cap = cv.VideoCapture(1, cv.CAP_DSHOW)
cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*"MJPG"))
cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

while(cap.isOpened()):

    success, img = cap.read()
    h, w, _ = img.shape
    mid = w // 2

    left = img[:, mid:]
    right  = img[:, :mid]

    # Undistort and rectify images
    frame_right = cv.remap(right, stereoMapR_x, stereoMapR_y, cv.INTER_LANCZOS4, cv.BORDER_CONSTANT, 0)
    frame_left = cv.remap(left, stereoMapL_x, stereoMapL_y, cv.INTER_LANCZOS4, cv.BORDER_CONSTANT, 0)
                     
    # Show the frames
    cv.imshow("frame right", frame_right) 
    cv.imshow("frame left", frame_left)

    # Hit "q" to close the window
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

print("Left map size:", stereoMapL_x.shape)
print("Right map size:", stereoMapR_x.shape)
print("Live left size:", left.shape)
print("Live right size:", right.shape)

# Release and destroy all windows before termination
cap.release()

cv.destroyAllWindows()