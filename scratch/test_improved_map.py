import sys
import math
import urllib.request
sys.path.insert(0, ".")
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QPen
from PyQt6.QtCore import Qt, QRectF
from services.zone_map_service import resolve_coordinates, _download_and_draw_tiles

app = QApplication(sys.argv)

def generate_improved_zone_map(zone_or_addr: str, office_name: str = "신우 공인중개사사무소") -> QImage:
    width = 680
    height = 430
    zoom = 17  # 17: 가로등, 골목길, 학교, 아파트 단지명, 번지수까지 선명하게 식별되는 2배 확대 뷰

    lat, lon, display_title, _ = resolve_coordinates(zone_or_addr)

    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    center_x = (lon + 180.0) / 360.0 * n
    center_y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor("#F1F5F9"))

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # 1. 타일 다운로드 및 지도 렌더링
    _download_and_draw_tiles(p, center_x, center_y, zoom, width, height)

    # 2. 정비구역 붉은색 점선 경계 폴리곤 (화면 중심에 큼직하고 명확하게 배치)
    p.setPen(QPen(QColor(239, 68, 68, 240), 3.5, Qt.PenStyle.DashLine))
    p.setBrush(QColor(239, 68, 68, 42))
    zone_rect = QRectF(width // 2 - 180, height // 2 - 110, 360, 220)
    p.drawRoundedRect(zone_rect, 16, 16)

    # 3. 중심 핀 & 펄스 애니메이션 느낌의 원
    p.setBrush(QColor(239, 68, 68, 80))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(width // 2 - 22, height // 2 - 22, 44, 44)

    p.setBrush(QColor(220, 38, 38))
    p.setPen(QPen(QColor(255, 255, 255), 2.5))
    p.drawEllipse(width // 2 - 10, height // 2 - 10, 20, 20)

    # 4. 중심 핀 명칭 라벨 뱃지 (고대비 다크 네이비)
    badge_w = 320
    badge_h = 38
    badge_rect = QRectF(width // 2 - badge_w // 2, height // 2 - 66, badge_w, badge_h)
    p.setBrush(QColor(15, 23, 42, 245))
    p.setPen(QPen(QColor(255, 255, 255, 200), 1.2))
    p.drawRoundedRect(badge_rect, 8, 8)

    p.setPen(QColor(255, 255, 255))
    p.setFont(QFont("Malgun Gothic", 12, QFont.Weight.Bold))
    label_text = display_title if len(display_title) <= 20 else display_title[:19] + "..."
    p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"📍 {label_text}")

    # 5. 상단 헤더 배너 (국토교통부 토지이용계획 연동 가이드)
    p.setBrush(QColor(15, 23, 42, 245))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(0, 0, width, 44)

    p.setPen(QColor(255, 255, 255))
    p.setFont(QFont("Malgun Gothic", 12, QFont.Weight.Bold))
    p.drawText(QRectF(16, 0, width - 32, 44), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"🗺️ 정비구역 위치도 & 토지이용계획 참조 | {display_title}")

    # 6. 하단 푸터 범례
    p.setBrush(QColor(15, 23, 42, 235))
    p.drawRect(0, height - 34, width, 34)

    p.setPen(QColor(148, 163, 184))
    p.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Normal))
    p.drawText(QRectF(16, height - 34, 380, 34), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "■ 빨간점선: 재개발 정비구역 예정지  ■ 용도: 제2종일반주거지역")
    p.drawText(QRectF(width - 340, height - 34, 324, 34), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"🏢 {office_name}")

    p.end()
    return img

m = generate_improved_zone_map("도마변동5구역")
m.save("scratch/test_map_zoom17.png")
print("Saved scratch/test_map_zoom17.png")
