import math
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor, QPen, QFont, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QRectF, QPointF

app = QApplication(sys.argv)

def lat_lon_to_screen(lat, lon, center_x, center_y, zoom, width, height):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    px = (lon + 180.0) / 360.0 * n * 256
    py = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n * 256
    sx = (width / 2.0) + (px - center_x * 256)
    sy = (height / 2.0) + (py - center_y * 256)
    return sx, sy

# For 도마변동5구역:
# Real boundary of 도마변동5구역:
# min_lat: 36.3140, max_lat: 36.3195
# min_lon: 127.3745, max_lon: 127.3825
# center: lat 36.3168, lon 127.3785
lat, lon = 36.3168, 127.3785
bbox = (36.3140, 127.3745, 36.3195, 127.3825)

width, height = 620, 400
zoom = 16

lat_rad = math.radians(lat)
n = 2.0 ** zoom
center_x = (lon + 180.0) / 360.0 * n
center_y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

# Top-left of bbox on screen: (max_lat, min_lon)
# Bottom-right of bbox on screen: (min_lat, max_lon)
x1, y1 = lat_lon_to_screen(bbox[2], bbox[1], center_x, center_y, zoom, width, height)
x2, y2 = lat_lon_to_screen(bbox[0], bbox[3], center_x, center_y, zoom, width, height)

print(f"Zoom {zoom}: Box coords on screen: x1={x1:.1f}, y1={y1:.1f}, x2={x2:.1f}, y2={y2:.1f}, width={x2-x1:.1f}, height={y2-y1:.1f}")
