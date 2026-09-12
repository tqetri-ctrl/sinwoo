import math
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor, QPen, QFont, QBrush
from PyQt6.QtCore import Qt, QRectF
from services.zone_map_service import _download_and_draw_tiles, FONT_FAMILY

app = QApplication(sys.argv)

def lat_lon_to_screen(lat, lon, center_x, center_y, zoom, width, height):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    px = (lon + 180.0) / 360.0 * n * 256
    py = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n * 256
    sx = (width / 2.0) + (px - center_x * 256)
    sy = (height / 2.0) + (py - center_y * 256)
    return sx, sy

# 한남3구역 실제 좌표 및 BBox
# Center: lat 37.5310, lon 127.0015 (한남동 재개발 구역)
# BBox: min_lat 37.5260, min_lon 126.9960, max_lat 37.5360, max_lon 127.0070
lat, lon = 37.5310, 127.0015
bbox = (37.5260, 126.9960, 37.5360, 127.0070)
width, height = 620, 400
zoom = 15

lat_rad = math.radians(lat)
n = 2.0 ** zoom
center_x = (lon + 180.0) / 360.0 * n
center_y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

img = QImage(width, height, QImage.Format.Format_ARGB32)
img.fill(QColor("#F1F5F9"))

p = QPainter(img)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

_download_and_draw_tiles(p, center_x, center_y, zoom, width, height)

x1, y1 = lat_lon_to_screen(bbox[2], bbox[1], center_x, center_y, zoom, width, height)
x2, y2 = lat_lon_to_screen(bbox[0], bbox[3], center_x, center_y, zoom, width, height)

zone_rect = QRectF(x1, y1, x2 - x1, y2 - y1)
p.setPen(QPen(QColor(239, 68, 68, 240), 3.0, Qt.PenStyle.DashLine))
p.setBrush(QColor(239, 68, 68, 42))
p.drawRoundedRect(zone_rect, 10, 10)

cx, cy = width // 2, height // 2
p.setBrush(QColor(239, 68, 68, 70))
p.setPen(Qt.PenStyle.NoPen)
p.drawEllipse(cx - 18, cy - 18, 36, 36)

p.setBrush(QColor(220, 38, 38))
p.setPen(QPen(QColor(255, 255, 255), 2.5))
p.drawEllipse(cx - 8, cy - 8, 16, 16)

display_title = "한남3구역 재정비촉진지구 (디에이치 한남)"
badge_w = 320
badge_h = 32
badge_rect = QRectF(cx - badge_w // 2, cy - 48, badge_w, badge_h)
p.setBrush(QColor(15, 23, 42, 245))
p.setPen(QPen(QColor(255, 255, 255, 200), 1.2))
p.drawRoundedRect(badge_rect, 6, 6)

p.setPen(QColor(255, 255, 255))
p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"📍 {display_title}")

p.setBrush(QColor(15, 23, 42, 245))
p.setPen(Qt.PenStyle.NoPen)
p.drawRect(0, 0, width, 38)
p.setPen(QColor(255, 255, 255))
p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
p.drawText(QRectF(14, 0, width - 28, 38), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"🗺️ 정비구역 위치도 & 토지이용계획 참조 | {display_title}")

p.setBrush(QColor(15, 23, 42, 235))
p.drawRect(0, height - 30, width, 30)
p.setPen(QColor(148, 163, 184))
p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Normal))
p.drawText(QRectF(14, height - 30, 360, 30), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "■ 빨간점선: 재개발 정비구역 예정지  ■ 용도: 제2종/제3종일반주거")
p.drawText(QRectF(width - 240, height - 30, 226, 30), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "🏢 신우 공인중개사사무소")

p.end()
img.save("scratch/test_hannam_map.png")
print("Saved scratch/test_hannam_map.png")
