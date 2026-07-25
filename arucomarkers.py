#!/usr/bin/env python3

import cv2
import numpy as np

print(f"Detected OpenCV Version: {cv2.__version__}")

major_ver, minor_ver, _ = cv2.__version__.split('.')

try:
    if int(major_ver) == 4 and int(minor_ver) >= 7:
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        
        if hasattr(cv2.aruco, 'generateImageMarker'):
            marker_image = cv2.aruco.generateImageMarker(dictionary, 0, 200)
        else:
            marker_image = cv2.aruco.drawMarker(dictionary, 0, 200)

    else:
        dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        marker_image = cv2.aruco.drawMarker(dictionary, 0, 200)

    cv2.imwrite("aruco_marker_0.png", marker_image)
    print("Marker generated successfully.")

except Exception as e:
    print(f"Failed to generate marker. Error: {e}")
    print("Ensure you have the contrib modules installed: pip install opencv-contrib-python")