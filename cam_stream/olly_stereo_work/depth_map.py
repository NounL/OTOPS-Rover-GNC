# Olly Love
# StereoSGBM depth map
# Better Quality over bm?
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

# in pixels
f = Q[2,3]
B = -1 / Q[3,2]
cx = -Q[0,3]
cy = -Q[1,3]

cap = cv.VideoCapture(1, cv.CAP_DSHOW)
cap.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*"MJPG"))
cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

# resolution per lens
frameSize = (640,480)

# Dividing width and height of frame by factor of 2 because performs better this way
resize_vals = (320, 240)

# Old pranav + copilot/gpt settings
# stereo = cv.StereoSGBM.create(
#     minDisparity=0,
#     # 128 = good for 0.5–6m range
#     numDisparities=16,  
#     # Told if looks noisy try blocksize = 9, if blurry try 5 
#     blockSize=7,
#     P1 = 8 * 1 * 7 * 7,
#     P2 = 32 * 1 * 7 * 7,
#     disp12MaxDiff=1,
#     uniquenessRatio=10,
#     # could try 100 - chatgpt
#     speckleWindowSize=50,
#     speckleRange=2,
#     mode=cv.STEREO_SGBM_MODE_SGBM_3WAY
# )

# lower res images better with smaller window size, 3, 5, 7
# window_size = 3

# Diff settings found online:
# https://python.plainenglish.io/the-depth-ii-block-matching-d599e9372712 
# stereo = cv.StereoSGBM.create(
#     # code found had as -1
#     minDisparity=0,
#     # max_disp has to be dividable by 16 f. E. HH 192, 256
#     numDisparities=5*16,  
#     blockSize=window_size,
#     # 8 * channel * blocksize (best to use 1 channel, grayscale, code I found used 3 for rgb)
#     # 32 * channel * blocksize
#     # copilot saying should be window_size squared at the end instead of just window_size
#     P1=8 * 1 * window_size,
#     P2=32 * 1 * window_size,
#     disp12MaxDiff=12,
#     # suggested range 5-15
#     uniquenessRatio=10,
#     # 50-200 good range, for smoother image
#     speckleWindowSize=50,
#     speckleRange=32,
#     preFilterCap=63,
#     mode=cv.STEREO_SGBM_MODE_SGBM_3WAY
# )

# Other settings to try from video:
# block_size = 3
# min_disparity = 0
# num_disparities = 32
# p1_factor = 8
# p2_factor = 32
# disp_12_max_diff = 0
# pre_filter_cap = 0
# uniqueness_ratio = 1
# speckle_range = 1
# speckle_window = 10

'''
Trying this from video code
'''
# His settings
# block_size = 3
# min_disparity = 0
# num_disparities = 32
# p1_factor = 8
# p2_factor = 32
# disp_12_max_diff = 0
# pre_filter_cap = 0
# uniqueness_ratio = 1
# speckle_range = 1
# speckle_window = 10

#blockSize = 3

# Apply configuration settings
stereo = cv.StereoSGBM_create(
    0,
    32,
    3,
    8*3*3,
    32*3*3,
    0,
    0,
    1,
    1,
    10
)

while (cap.isOpened()):
    success, img = cap.read()
    h, w, _ = img.shape
    mid = w // 2

    # could be big issue here - test orientation and fix
    left = img[:, mid:]
    right  = img[:, :mid]

    # Undistort and rectify images
    # also try inter_linear for better cpu
    frame_left = cv.remap(left, stereoMapL_x, stereoMapL_y, cv.INTER_LANCZOS4, cv.BORDER_CONSTANT, 0)
    frame_right = cv.remap(right, stereoMapR_x, stereoMapR_y, cv.INTER_LANCZOS4, cv.BORDER_CONSTANT, 0)
    
    grayL = cv.cvtColor(frame_left, cv.COLOR_BGR2GRAY)
    grayR = cv.cvtColor(frame_right, cv.COLOR_BGR2GRAY)

    # resize 
    final_left = cv.resize(grayL, resize_vals)
    final_right = cv.resize(grayR, resize_vals)

    disparity = stereo.compute(final_left, final_right)
    disparity = cv.erode(disparity, None, iterations=1)
    disparity = cv.dilate(disparity, None, iterations=1)

    # Scaling for distance measurement
    scale_x = resize_vals[0] / frameSize[0]
    scale_y = resize_vals[1] / frameSize[1]
    f_scaled = f * scale_x
    cx = resize_vals[0] // 2
    cy = resize_vals[1] // 2
    
    # Need this before the resize for pixel accuracy 
    # Getting the pixel coord at center of disparity map
    # Might be noisy and can test with median thing 
    center_disp = disparity[cy, cx]

    if center_disp > 0:
        Z = (f_scaled * B) / center_disp
        Z_m = Z / 1000.0
    else:
        Z = 0

    disparity = cv.resize(disparity, frameSize)

    # divide here by 16?
    disparity_normal = cv.normalize(disparity, None, 0, 255, cv.NORM_MINMAX)
    image = np.array(disparity_normal, dtype = np.uint8)
    disparity_color = cv.applyColorMap(image, cv.COLORMAP_HOT)
    
    # center_roi = disparity[cy_scaled-10:cy_scaled+10, cx_scaled-10:cx_scaled+10]
    # avg_disp = np.mean(center_roi)

    # if avg_disp > 0.5:
    #     distance_mm = (f_scaled * B) / avg_disp
    #     distance_m = distance_mm / 1000.0
    # else:
    #     distance = 0 

    # Map cx and cy to display resolution
    cx_disp = frameSize[0] // 2
    cy_disp = frameSize[1] // 2

    # 6. Annotations
    cv.rectangle(disparity_color, (cx_disp-10, cy_disp-10), (cx_disp+10, cy_disp+10), (255, 255, 255), 2)
    cv.putText(disparity_color, f"Dist: {Z_m:.2f}m", (cx_disp-50, cy_disp-20), 
                cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Compute disparity 
    # disparity = stereo.compute(grayL, grayR).astype(np.float32) / 16.0

    # Dimensions for the center point - retry this later
    # disp_h, disp_w = disparity.shape
    # cx, cy = disp_w // 2, disp_h // 2

    # points_3d = cv.reprojectImageTo3D(disparity, Q)
    # #roi_3d = points_3d[cy-10:cy+10, cx-10:cx+10]
    # roi_3d = points_3d[
    #     max(0, cy-10):min(disp_h, cy+10),
    #     max(0, cx-10):min(disp_w, cx+10)
    # ]

    # z_values = roi_3d[:, :, 2]

    # valid = np.isfinite(z_values) & (z_values > 0)

    # if np.any(valid):
    #     distance = np.median(z_values[valid])
    # else:
    #     distance = 0

    # Optional - coords of center pixel
    # X, Y, Z = points_3d[cy, cx]

    # Sample the center for noise-resistant reading
    #center_roi = disparity[cy-10:cy+10, cx-10:cx+10]
    #avg_disparity = np.mean(center_roi)

    # f and b not used anymore with points_3d
    # Focal length in pixels from cam_data note from calibration
    # f = Q[2,3] - in cam_data Q reprojection matrix
    #f = 682.297453

    # -59.496311
    # 0.0594 m 5.94 cm baseline
    # Baseline B = 1 / f
    #B = 0.0594963
    
    # if avg_disparity > 0.5:
    #     distance = (f * B) / avg_disparity
    # else:
    #     distance = 0 

    # Chatgpt saying use this instead of avg_disparity = np.mean(center_roi)
    # Chatgpt saying > 1 better then > 0
    # Chatgpt saying use actual data from Q matrix instead of manually calculating with f and B
    # valid = center_roi[center_roi > 1]
    # if len(valid):
    #     avg_disparity = np.median(valid)

    #     # Depth in meters
    #     distance = (f * B) / avg_disparity
    # else:
    #     avg_disparity = 0
    #     distance = 0

    # disparity_vis = cv.normalize(disparity, None, 0, 255, cv.NORM_MINMAX).astype(np.uint8)
    # disparity_color = cv.applyColorMap(disparity_vis, cv.COLORMAP_JET)

    # Blend the depth map with the actual camera image
    # 0.6 weight on the camera, 0.4 on the heat map
    # Overlay allegedly only for debugging
    # overlay = cv.addWeighted(frame_left, 0.6, disparity_color, 0.4, 0)

    # # 6. Annotations this value completely wrong
    # cv.rectangle(disparity_color, (cx-10, cy-10), (cx+10, cy+10), (255, 255, 255), 2)
    # cv.putText(disparity_color, f"Dist: {distance:.2f}m", (cx-50, cy-20), 
    #             cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # cv.imshow("REAL WORLD + DEPTH", overlay)
    # cv.imshow("RAW DISPARITY", disparity_vis)
    cv.imshow("DEPTH", disparity_color)

    # Exit on escape key
    if cv.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv.destroyAllWindows()