#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import cv2
import numpy as np

class ArucoDetectorNode(Node):
    def __init__(self):
        super().__init__('aruco_detector_node')
        
        self.bridge = CvBridge()
        self.get_logger().info(f"Using OpenCV version: {cv2.__version__}")
        
        self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        self.aruco_params = cv2.aruco.DetectorParameters_create()
        
        self.camera_topic = '/a300_00000/sensors/camera_0/color/image'
        self.image_sub = self.create_subscription(
            Image,
            self.camera_topic,
            self.image_callback,
            10
        )
        
        self.annotated_pub = self.create_publisher(
            Image, 
            '/cpr_a200_0000/camera_0/image_annotated', 
            10
        )
        
        self.get_logger().info(f"ArUco Detector Active. Listening to {self.camera_topic}...")

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge Error: {e}")
            return

        if cv_image is None or cv_image.size == 0:
            return

        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray, 
            self.aruco_dict, 
            parameters=self.aruco_params
        )

        if ids is not None:
            self.get_logger().info(f"Detected {len(ids)} proxy fruit(s)!")
            
            cv2.aruco.drawDetectedMarkers(cv_image, corners, ids)
            
            for i in range(len(ids)):
                c = corners[i][0]
                center_x = int((c[0][0] + c[1][0] + c[2][0] + c[3][0]) / 4)
                center_y = int((c[0][1] + c[1][1] + c[2][1] + c[3][1]) / 4)
                self.get_logger().info(f"Fruit ID {ids[i][0]} found at Pixel (X: {center_x}, Y: {center_y})")

        try:
            annotated_msg = self.bridge.cv2_to_imgmsg(cv_image, encoding="bgr8")
            self.annotated_pub.publish(annotated_msg)
        except CvBridgeError as e:
            self.get_logger().error(f"CvBridge Publish Error: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = ArucoDetectorNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down Aruco Detector...")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
