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

# Almost done but need to follow more tutorials (for image file help), 
# Need to edit subscriber node as well
# Want to switch this so subscriber doing the aruco work, publisher just sending the image

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os

class ImagePublisher(Node):

    def __init__(self):
        super().__init__('image_publisher')
        self.publisher_ = self.create_publisher(Image, 'camera_image', 10)
        # 0.033 = 30fps, 0.016 = 60fps
        timer_period = 0.016 # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.bridge = CvBridge()
        # Line for jetson: self.cap = cv2.VideoCapture(0)
        self.cap = cv2.VideoCapture()

        # My Windows IPv4 address + port from mpeg streamer - must have mpeg streamer open when testing
        # Comment this line out for jetson - only needed for ip camera stream with wsl
        self.cap.open("http://putiphere:8000")
        
        # For testing with image instead of camera feed - delete when not needed anymore
        # relative_image_path = str(os.getcwd()) + "/src/py_pubsub_aruco/py_pubsub_aruco/allArucoMarkersSmall.png"
        # self.cv_image = cv2.imread(relative_image_path)
        # if self.cv_image is None:
        #     # Shows current directory for debugging image issues
        #     self.get_logger().error(f"Image not found. Current working directory: {os.getcwd()}")
        #     exit(1)

    def timer_callback(self):
        ret, frame = self.cap.read()
        if ret:
            # Video used camera frame here instead of cv_image
            ros_image = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            self.publisher_.publish(ros_image)
            self.get_logger().info("Publishing Image!")
        else:
            self.get_logger().info("Error reading image.")

def main(args=None):
    rclpy.init(args=args)
    image_publisher = ImagePublisher()
    rclpy.spin(image_publisher)
    image_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
