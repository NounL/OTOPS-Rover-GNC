# Copyright 2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Reads and gets aruco marker id from an image

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import math

class ImageSubscriber(Node):

    def __init__(self):
        super().__init__('image_subscriber')
        self.subscription = self.create_subscription(
            Image,
            'camera_image',
            self.listener_callback,
            10)
        self.subscription
        self.bridge = CvBridge()

        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
        self.parameters = cv2.aruco.DetectorParameters_create()

        # Video found marker_size when generating - how do i get size?
        # competition says this regarding size - "Each marker will be a minimum size of 2” x 2” or 5cm x 5cm."
        # 5cmx5cm = 100mm, my samples must be 100mm
        self.marker_size = 100

        # Copied and pasted from calibration data yaml file
        self.camera_matrix = np.array([
            [1103.81665, 0, 602.53781],
            [0, 1109.70027, 284.71209],
            [0, 0, 1]    
        ], dtype=np.float64)
        
        self.distortion_coeffs = np.array([0.014637, 0.025424, -0.017560, -0.008342, 0.000000], dtype=np.float64)

    """
    Code between these quotes from : https://learnopencv.com/rotation-matrix-to-euler-angles/
    """

    # Checks if a matrix is a valid rotation matrix.
    def isRotationMatrix(self,R):
        Rt = np.transpose(R)
        shouldBeIdentity = np.dot(Rt, R)
        I = np.identity(3, dtype = R.dtype)
        n = np.linalg.norm(I - shouldBeIdentity)
        return n < 1e-6
    
    # Calculates rotation matrix to euler angles
    # The result is the same as MATLAB except the order
    # of the euler angles ( x and z are swapped ).
    def rotationMatrixToEulerAngles(self,R) :
    
        assert(self.isRotationMatrix(R))
    
        sy = math.sqrt(R[0,0] * R[0,0] +  R[1,0] * R[1,0])
    
        singular = sy < 1e-6
    
        if  not singular :
            x = math.atan2(R[2,1] , R[2,2])
            y = math.atan2(-R[2,0], sy)
            z = math.atan2(R[1,0], R[0,0])
        else :
            x = math.atan2(-R[1,2], R[1,1])
            y = math.atan2(-R[2,0], sy)
            z = 0
    
        return np.array([x, y, z])
    
    """
    Above code from link
    """
        
    def find_aruco(self, img, draw=True):
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray, self.aruco_dict, self.camera_matrix, self.distortion_coeffs, parameters=self.parameters
        )
        
        if ids is not None and draw:
            cv2.aruco.drawDetectedMarkers(img, corners)

            # Pose detection for markers
            # rvec rotation vectors, tvecs = translation vectors
            rvecs, tvecs, _objPoints = cv2.aruco.estimatePoseSingleMarkers(corners, self.marker_size, self.camera_matrix, self.distortion_coeffs)

            # For handling multiple on screen markers
            for marker in range(len(ids)):
                cv2.aruco.drawAxis(img, self.camera_matrix, self.distortion_coeffs, rvecs[marker][0], tvecs[marker][0], self.marker_size)

                rvec_flipped = rvecs[marker][0] * -1
                tvec_flipped = tvecs[marker][0] * -1
                rotation_matrix, jacobian = cv2.Rodrigues(rvec_flipped)
                realworld_tvec = np.dot(rotation_matrix, tvec_flipped)

                pitch, roll, yaw = self.rotationMatrixToEulerAngles(rotation_matrix)

                # Puts marker ids in top left corner
                #cv2.putText(img, str(ids[marker][0]), (int(corners[marker][0][0][0])-30, int(corners[marker][0][0][1])), cv2.FONT_HERSHEY_PLAIN,3,(255,0,0),2,cv2.LINE_AA)
                
                # Displays realworld coordinates (I think) of camera relative to marker - Want to also publish this later
                tvec_str = f"x={realworld_tvec[0]:4.0f} y={realworld_tvec[1]:4.0f} direction={math.degrees(yaw):4.0f}"
                # For testing to see values - details overlap for multiple markers
                cv2.putText(img, tvec_str, (20,670), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2, cv2.LINE_AA)

        return corners, ids

    def listener_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        corners, ids = self.find_aruco(cv_image)
        cv2.imshow("Image", cv_image)
        cv2.waitKey(1)

        if ids is not None:
            self.marker_id = str(ids)
            self.get_logger().info(f"Image read! Marker ID's found: {self.marker_id}")
        else:
            self.get_logger().info(f"Error, no markers detected.")

def main(args=None):
    rclpy.init(args=args)
    image_subscriber = ImageSubscriber()
    rclpy.spin(image_subscriber)
    image_subscriber.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
