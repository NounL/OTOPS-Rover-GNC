import cv2
import numpy as np
import matplotlib.pyplot as plt

# Define the dictionary we want to use - marker ids from 0-99
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)

# Size in pixels
marker_size = 400  

# Creating subplots, 10 rows, 10 cols for a grid of all 100 markers (or 1 row 3 markers)
# Each subplot is width by height in inches
fig, axes = plt.subplots(1, 3, figsize=(17, 8))
# count = 0

# for i in range(2):
#     for j in range(10):
#         marker_id = count
#         marker_image = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)
#         axes[i][j].imshow(marker_image, cmap='gray', interpolation='nearest')
#         axes[i][j].axis('off')
#         axes[i][j].set_title(f'Marker {marker_id}')
#         count += 1

for i in range(3):
    marker_image = cv2.aruco.generateImageMarker(aruco_dict, i, marker_size)
    axes[i].imshow(marker_image, cmap='gray', interpolation='nearest')
    axes[i].axis('off')
    axes[i].set_title(f'Marker {i}')

plt.tight_layout()
plt.show()