# Olly Love
# StereoBM depth map
# Not as good as sgbm but still fine

import numpy as np
import cv2 as cv
from matplotlib import pyplot as plt

# Loading in calibration data
cv_file = cv.FileStorage()
cv_file.open('olly_stereo_work/stereoMap.xml', cv.FileStorage_READ)
stereoMapL_x = cv_file.getNode('stereoMapL_x').mat()
stereoMapL_y = cv_file.getNode('stereoMapL_y').mat()
stereoMapR_x = cv_file.getNode('stereoMapR_x').mat()
stereoMapR_y = cv_file.getNode('stereoMapR_y').mat()
Q = cv_file.getNode('Q').mat()

# Stereo Camera Settings
cap = cv.VideoCapture(1, cv.CAP_DSHOW)
cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*"MJPG"))
cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

# resolution per lens
frameSize = (640,480)

# numDisparities must be multiple of 16, default is 0, blockSize must be odd number
# larger block size gives smoother map but decreased accuracy
# copilot saying try 128
#stereo = cv.StereoBM_create(numDisparities=16, blockSize=21)
'''
Trying resize + settings from video
'''
# Dividing width and height of frame by factor of 2 because stereobm performs better this way
resize_vals = (320, 240)

stereo = cv.StereoBM_create(
    numDisparities=48,
    blockSize=21
)

stereo.setPreFilterType(1)
stereo.setMinDisparity(0)
stereo.setNumDisparities(48)
stereo.setTextureThreshold(0)
stereo.setUniquenessRatio(1)
stereo.setSpeckleRange(2)
stereo.setSpeckleWindowSize(2)

while (cap.isOpened()):
    success, img = cap.read()
    h, w, _ = img.shape
    mid = w // 2

    # need to test this then fix for correct orientation
    left = img[:, mid:]
    right  = img[:, :mid]

    # Undistort and rectify images
    frame_left = cv.remap(left, stereoMapL_x, stereoMapL_y, cv.INTER_LANCZOS4, cv.BORDER_CONSTANT, 0)
    frame_right = cv.remap(right, stereoMapR_x, stereoMapR_y, cv.INTER_LANCZOS4, cv.BORDER_CONSTANT, 0)
    
    grayL = cv.cvtColor(frame_left, cv.COLOR_BGR2GRAY)
    grayR = cv.cvtColor(frame_right, cv.COLOR_BGR2GRAY)

    # resize 
    final_left = cv.resize(grayL, resize_vals)
    final_right = cv.resize(grayR, resize_vals)
    
    #depth = stereo.compute(grayL, grayR)
    disparity = stereo.compute(final_left, final_right)
    disparity = cv.dilate(disparity, None, iterations=1)
    disparity = cv.resize(disparity, frameSize)

    disparity_normal = cv.normalize(disparity, None, 0, 255, cv.NORM_MINMAX)
    image = np.array(disparity_normal, dtype = np.uint8)
    # disparity_color = cv.applyColorMap(image, cv.COLORMAP_BONE)
    disparity_color = cv.applyColorMap(image, cv.COLORMAP_HOT)

    # this chunk right here from video I found
    # Show depth map
    # if self.show_rgb:
    #     cv2.imshow("Depth map", np.hstack((disparity_color, left_frame)))
    # else:
    #     cv2.imshow("Depth map", disparity_color)

    # This stuff only used for distance calculation
    # Dimensions for the center point
    # disp_h, disp_w = depth.shape
    # cx, cy = disp_w // 2, disp_h // 2

    # copilot says normalize?
    #depth_vis = cv.normalize(depth, None, 0, 255, cv.NORM_MINMAX).astype(np.uint8)
    #disparity_color = cv.applyColorMap(depth_vis, cv.COLORMAP_HOT)

    # Will delete these later to only see the depth map - use for debugging
    cv.imshow("Left", grayL)
    cv.imshow("Right", grayR)

    cv.imshow("DEPTH", disparity_color)

    # Exit on escape key
    if cv.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv.destroyAllWindows()
    