# Simple detecting of ArUco markers from picture or video
# Resources: https://www.youtube.com/watch?v=AQXLC2Btag4
# https://www.geeksforgeeks.org/computer-vision/detecting-aruco-markers-with-opencv-and-python-1/ 
# Windows version as can actually access webcam here for testing

import cv2
import cv2.aruco as aruco

videoCap = True
cap = cv2.VideoCapture(0)

def findAruco(img, draw=True):
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_100)
    parameters = aruco.DetectorParameters()
    detector = aruco.ArucoDetector(aruco_dict, parameters)
    corners, ids, rejected = detector.detectMarkers(gray)
    
    if draw:
        aruco.drawDetectedMarkers(img, corners)

    return corners, ids

# While loop needed for video camera
while True:
    if videoCap: 
        _,img=cap.read()
    else:
        img = cv2.imread("marker_7.png")
        img = cv2.resize(img, (600, 400))
    
    corners, ids = findAruco(img)

    print(ids)

    # This saying if user presses q key (ascii) stop 
    if cv2.waitKey(1) == 113:
        break

    cv2.imshow("img",img)