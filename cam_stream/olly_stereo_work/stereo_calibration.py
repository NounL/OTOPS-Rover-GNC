# Camera Calibrator
# When you have calibration images generated and stored, run this to calibrate
# https://www.youtube.com/watch?v=yKypaVl6qQo&list=PLCpB2LmtGbuel31gdKHSV_HBaZa2guc6Y&index=5 
# https://github.com/niconielsen32/ComputerVision/blob/master/stereoVisionCalibration/stereovision_calibration.py

import numpy as np
import cv2 as cv
import glob

# 9 inner corners (width) by 6 inner corners (height)
# same as 5 black squares by 4 black squares
# This depends on the calibration sheet being used
chessboardSize = (9,6)
# Per lens resolution
frameSize = (640,480)

# Default termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
# Becomes np.zeroes(54,3), 54 rows by 3 columns
# looks like 
# [[0. 0. 0.]
#  [0. 0. 0.]
#  [0. 0. 0.]
#  [0. 0. 0.]] ... til 54 rows
objp = np.zeros((chessboardSize[0] * chessboardSize[1], 3), np.float32)
# All rows, first 2 columns
# np.mgrid[0:9, 0:6] - 9 columns (x values) by 6 row (y values) grid
# reshaping to have each row repping one corner x,y,z coords (though z coords left null as 2D)
objp[:,:2] = np.mgrid[0:chessboardSize[0], 0:chessboardSize[1]].T.reshape(-1,2)

# Each square on calibration sheet 21 mm long measured w ruler, scaling 
# for real world
objp = objp * 22
print(objp)

# Store object points and img points from all images
# 3D - real world plane
objpoints = []
# 2D - image plane
imgpointsL = []
imgpointsR = []

# gets all png files in folder as list of filenames - images of our checkerboard for calibrating
imagesLeft = sorted(glob.glob('olly_stereo_work/images/stereoLeft/*.png'))
imagesRight = sorted(glob.glob('olly_stereo_work/images/stereoRight/*.png'))

# going through 2 lists at once, pairing elements together
for imgLeft, imgRight in zip(imagesLeft, imagesRight):

    imgL = cv.imread(imgLeft)
    imgR = cv.imread(imgRight)
    grayL = cv.cvtColor(imgL, cv.COLOR_BGR2GRAY)
    grayR = cv.cvtColor(imgR, cv.COLOR_BGR2GRAY)

    # Troubles with chessboard corners not being recognized
    retL, cornersL = cv.findChessboardCorners(grayL, chessboardSize, None)
    retR, cornersR = cv.findChessboardCorners(grayR, chessboardSize, None)

    if retL and retR:
        objpoints.append(objp)

        # refining locations of corners to subpixel accuracy, 11 by 11 and -1 by -1 being
        # default for the subpixel window used
        cornersL = cv.cornerSubPix(grayL, cornersL, (11,11), (-1,-1), criteria)
        imgpointsL.append(cornersL)
        cornersR = cv.cornerSubPix(grayR, cornersR, (11,11), (-1,-1), criteria)
        imgpointsR.append(cornersR)

        # Draw and display the corners
        cv.drawChessboardCorners(imgL, chessboardSize, cornersL, retL)
        cv.imshow('img left', imgL)
        cv.drawChessboardCorners(imgR, chessboardSize, cornersR, retR)
        cv.imshow('img right', imgR)
        # wait 1 second til next
        cv.waitKey(1000)

cv.destroyAllWindows()

# Calibration part - above we get object points, now use this data to calibrate
retL, cameraMatrixL, distL, rvecsL, tvecsL = cv.calibrateCamera(objpoints, imgpointsL, frameSize, None, None)
heightL, widthL, channelsL = imgL.shape
newCameraMatrixL, roi_L = cv.getOptimalNewCameraMatrix(cameraMatrixL, distL, (widthL, heightL), 1, (widthL, heightL))

retR, cameraMatrixR, distR, rvecsR, tvecsR = cv.calibrateCamera(objpoints, imgpointsR, frameSize, None, None)
heightR, widthR, channelsR = imgR.shape
newCameraMatrixR, roi_R = cv.getOptimalNewCameraMatrix(cameraMatrixR, distR, (widthR, heightR), 1, (widthR, heightR))

# Stereo Vision Calibration
flags = 0
flags |= cv.CALIB_FIX_INTRINSIC
# fixing intrinsic parameters to be the same,
# intrinsic parameters = inside the camera, focal length, sensor size...

criteria_stereo = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# This step is performed to transformation between the two cameras and calculate Essential and Fundamenatl matrix
retStereo, newCameraMatrixL, distL, newCameraMatrixR, distR, rot, trans, essentialMatrix, fundamentalMatrix = cv.stereoCalibrate(objpoints, imgpointsL, imgpointsR, newCameraMatrixL, distL, newCameraMatrixR, distR, grayL.shape[::-1], criteria_stereo, flags)

########## Stereo Rectification #################################################
# copilot said rectifyScale = 0 better?
rectifyScale = 1
rectL, rectR, projMatrixL, projMatrixR, Q, roi_L, roi_R= cv.stereoRectify(newCameraMatrixL, distL, newCameraMatrixR, distR, grayL.shape[::-1], rot, trans, rectifyScale,(0,0))

stereoMapL = cv.initUndistortRectifyMap(newCameraMatrixL, distL, rectL, projMatrixL, grayL.shape[::-1], cv.CV_16SC2)
stereoMapR = cv.initUndistortRectifyMap(newCameraMatrixR, distR, rectR, projMatrixR, grayR.shape[::-1], cv.CV_16SC2)

print("Saving parameters!")
cv_file = cv.FileStorage('olly_stereo_work/stereoMap.xml', cv.FILE_STORAGE_WRITE)

cv_file.write('stereoMapL_x',stereoMapL[0])
cv_file.write('stereoMapL_y',stereoMapL[1])
cv_file.write('stereoMapR_x',stereoMapR[0])
cv_file.write('stereoMapR_y',stereoMapR[1])
cv_file.write('Q', Q)

cv_file.release()

print("projMatrixL\n")
print(projMatrixL)

print("---------\n")

print("projMatrixR\n")
print(projMatrixR)

print("---------\n")

print("Q\n")
print(Q)