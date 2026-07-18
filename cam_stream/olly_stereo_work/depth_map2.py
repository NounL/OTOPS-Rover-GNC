# Probably not gonna use this
# code modified from this: https://python.plainenglish.io/the-depth-ii-block-matching-d599e9372712 
import cv2 as cv
import numpy as np

# Loading in calibration data
cv_file = cv.FileStorage()
cv_file.open('olly_stereo_work/stereoMap.xml', cv.FileStorage_READ)

stereoMapL_x = cv_file.getNode('stereoMapL_x').mat()
stereoMapL_y = cv_file.getNode('stereoMapL_y').mat()
stereoMapR_x = cv_file.getNode('stereoMapR_x').mat()
stereoMapR_y = cv_file.getNode('stereoMapR_y').mat()

Q = cv_file.getNode('Q').mat()

cap = cv.VideoCapture(1, cv.CAP_DSHOW)
cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*"MJPG"))
cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

# lower res images better with smaller window size, 3, 5, 7
window_size = 3

left_matcher = cv.StereoSGBM.create(
    # code found used -1, can try that to
    minDisparity=0,
    # max_disp has to be dividable by 16 f. E. HH 192, 256
    # can try 96 or 128 as well
    numDisparities=5*16,  
    blockSize=window_size,
    # 8 * channel * blocksize (best to use 1 channel, grayscale, code I found used 3 for rgb)
    # 32 * channel * blocksize
    # copilot saying should be window_size squared at the end instead of just window_size
    P1 = 8 * 1 * window_size,
    P2 = 32 * 1 * window_size,
    disp12MaxDiff=12,
    # suggested range 5-15
    uniquenessRatio=10,
    # 50-200 good range, for smoother image
    speckleWindowSize=50,
    speckleRange=32,
    preFilterCap=63,
    mode=cv.STEREO_SGBM_MODE_SGBM_3WAY
)

right_matcher = cv.ximgproc.createRightMatcher(left_matcher)
# FILTER Parameters
lmbda = 80000
sigma = 1.3
visual_multiplier = 6

wls_filter = cv.ximgproc.createDisparityWLSFilter(matcher_left=left_matcher)
wls_filter.setLambda(lmbda)

wls_filter.setSigmaColor(sigma)


while (cap.isOpened()):
    success, img = cap.read()
    h, w, _ = img.shape
    mid = w // 2

    # this might be causing me big issue
    left = img[:, mid:]
    right  = img[:, :mid]

    # Undistort and rectify images
    # copilot said INTER_LINEAR better then previous one
    frame_left = cv.remap(left, stereoMapL_x, stereoMapL_y, cv.INTER_LINEAR, cv.BORDER_CONSTANT, 0)
    frame_right = cv.remap(right, stereoMapR_x, stereoMapR_y, cv.INTER_LINEAR, cv.BORDER_CONSTANT, 0)
    
    grayL = cv.cvtColor(frame_left, cv.COLOR_BGR2GRAY)
    grayR = cv.cvtColor(frame_right, cv.COLOR_BGR2GRAY)

    displ = left_matcher.compute(grayL, grayR)
    dispr = right_matcher.compute(grayR, grayL)
    displ = np.int16(displ)
    dispr = np.int16(dispr)
    filteredImg = wls_filter.filter(displ, grayL, None, dispr) 

    # copilot says this line not safe, something about buffer
    #filteredImg = cv.normalize(src=filteredImg, dst=filteredImg, beta=0, alpha=255, norm_type=cv.NORM_MINMAX)
    filteredImg = cv.normalize(filteredImg, None, 0, 255, cv.NORM_MINMAX)
    filteredImg = np.uint8(filteredImg)

    cv.imshow("DEPTH", filteredImg)

    # will worry about distance after code for depth map

    # Exit on escape key
    if cv.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv.destroyAllWindows()