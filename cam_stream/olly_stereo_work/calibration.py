# Stereo Camera Calibration Script
# Olly Love
# https://www.youtube.com/watch?v=3h7wgR5fYik&list=PLCpB2LmtGbuel31gdKHSV_HBaZa2guc6Y&index=4

# This not completely accurate watched wrong video

import numpy as np
import cv2 as cv
import glob

# Overall the idea is to build an array to represent the coordinates of a checkerboard
# Each row is one corner, each row storing x,y,z coord, z coord is always zero as 2D checkerboard
# Will have something like this
# [[ 0.  0.  0.]
#  [ 1.  0.  0.]
#  [ 2.  0.  0.]
#  ...
#  [21. 16.  0.]
#  [22. 16.  0.]
#  [23. 16.  0.]]

# Width by height, 24 by 17 corners
# This depends on the checkerboard size I use
chessboardSize = (24,17)
# change this based on camera - dont know that ours is 1440 by 1080
frameSize = (1440,1080)

# Default termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Becomes np.zeroes(408,3), 408 rows by 3 columns
# looks like 
# [[0. 0. 0.]
#  [0. 0. 0.]
#  [0. 0. 0.]
#  [0. 0. 0.]] ... til 408 rows
objp = np.zeros((chessboardSize[0] * chessboardSize[1], 3), np.float32)

# All rows, first 2 columns
# np.mgrid[0:24, 0:17] - 24 column (x values) by 17 row (y values) grid
# reshaping to have each row repping one corner x,y,z coords (though z coords left null as 2D)
objp[:,:2] = np.mgrid[0:chessboardSize[0], 0:chessboardSize[1]].T.reshape(-1,2)

# Store object points and img points from all images
# 3D - real world plane
objPoints = []
# 2D - image plane
imgPoints = []

# gets all png files in current folder as list of filenames - images of our checkerboard for calibrating
images = glob.glob('*.png')

for image in images:
    print(image)
    img = cv.imread(image)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    # Find chessboard corners
    ret, corners = cv.findChessboardCorners(gray, chessboardSize, None)

    # if found add object points, image points
    if ret == True:
        objPoints.append(objp)
        # refining locations of corners to subpixel accuracy, 11 by 11 and -1 by -1 being
        # default for the subpixel window used
        corners2 = cv.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
        imgPoints.append(corners)

        # Draw and display the corners
        cv.drawChessboardCorners(img, chessboardSize, corners2, ret)
        cv.imshow('img', img)
        # wait 1 second til next
        cv.waitKey(1000)

cv.destroyAllWindows()

# Calibration part - above we get object points, now use this data to calibrate
ret, cameraMatrix, dist, rvecs, tvecs = cv.calibrateCamera(objPoints, imgPoints, frameSize, None, None)

print("Camera Calibrated: ", ret)
print("\nCamera Matrix:\n", cameraMatrix)
print("n\Distortion Parameters:\n", dist)
print("\nRotation Vectors:\n", rvecs)
print("\nTranslation Vectors:\n", tvecs)

# Undistortion
img = cv.imread('cali5.png')
h, w = img.shape[:2]
newCameraMatrix, roi = cv.getOptimalNewCameraMatrix(cameraMatrix, dist, (w,h), 1, (w,h))

# Undistort
dst = cv.undistort(img, cameraMatrix, dist, None, newCameraMatrix)
# crop the image
x, y, w, h = roi
dst = dst[y:y+h, x:x+w]
cv.imwrite('caliResult1.png', dst)

# Undistort with Remapping
mapx, mapy = cv.initUndistortRectifyMap(cameraMatrix, dist, None, newCameraMatrix, (w,h), 5)
dst = cv.remap(img, mapx, mapy, cv.INTER_LINEAR)
# Crop the image
x, y, w, h = roi
dst = dst[y:y+h, x:x+w]
cv.imwrite('caliResult2.png', dst)

# reprojection error
mean_error = 0

for i in range(len(objPoints)):
    imgPoints2, _ = cv.projectPoints(objPoints[i], rvecs[i], tvecs[i], cameraMatrix, dist)
    error = cv.norm(imgPoints[i], imgPoints2, cv.NORM_L2)/len(imgPoints2)
    mean_error += error

print("\ntotal error: {}".format(mean_error/len(objPoints)))
print("\n\n\n")
