# Generating images for calibration
# Just opening the cameras as video capture, and taking images of calibration sheet
# periodically through that video capture, and storing them
# You run this file for images, then the calibration script to calibrate
# Olly Love
# https://www.youtube.com/watch?v=yKypaVl6qQo&list=PLCpB2LmtGbuel31gdKHSV_HBaZa2guc6Y&index=5 

import cv2 as cv
import time

# Each lens of stereo cam should be 1920 by 1080 (width by height)
# If each lens is side by side thats 1920 * 2 by 1080 (3840 by 1080)
# camera seems to only be 1280 by 720 each at the highest

cap = cv.VideoCapture(1, cv.CAP_DSHOW)
cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*"MJPG"))
cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
# Debugging lines
print(cap.get(cv.CAP_PROP_FRAME_WIDTH))
print(cap.get(cv.CAP_PROP_FRAME_HEIGHT))

# To allow for multiple images so they don't overwrite
# in filename
num = 0

save_interval = 3
prev_time = time.time()

while cap.isOpened():

    success, img = cap.read()
    h, w, _ = img.shape
    mid = w // 2

    left = img[:, mid:]
    right  = img[:, :mid]

    cv.imshow("Left", left)
    cv.imshow("Right", right)

    # Wait for keyboard press
    key = cv.waitKey(5)

    # Every 3 seconds take picture
    current_time = time.time()
    if current_time - prev_time >= save_interval:
        # Must have same amount of images for left and right, taken in pairs
        cv.imwrite('olly_stereo_work/images/stereoLeft/imageL' + str(num) + '.png', left)
        cv.imwrite('olly_stereo_work/images/stereoRight/imageR' + str(num) + '.png', right)
        print("images saved!")
        num += 1
        prev_time = current_time

    # Exit on escape key
    if key == 27:
        break

# Release and destroy windows before termination
cap.release()
cv.destroyAllWindows()