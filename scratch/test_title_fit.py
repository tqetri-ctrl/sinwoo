import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QFontMetrics, QPen, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, QRectF

app = QApplication(sys.argv)

FONT_FAMILY = "Malgun Gothic"

def _draw_fitted_title(p: QPainter, rect: QRectF, title: str, max_size: int = 13, min_size: int = 9, color: QColor = QColor("#FFFFFF")):
    p.setPen(color)
    clean_title = title.strip()
    fitted_font = None
    for size in range(max_size, min_size - 1, -1):
        font = QFont(FONT_FAMILY, size, QFont.Weight.Bold)
        fm = QFontMetrics(font)
        if fm.horizontalAdvance(clean_title) <= rect.width():
            fitted_font = font
            break
            
    if fitted_font:
        p.setFont(fitted_font)
        p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clean_title)
    else:
        font = QFont(FONT_FAMILY, min_size, QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap, clean_title)

# Let's test with the exact title from user's screenshot:
# "[대전 재개발] 도마변동5구역 최신 진행 현황과 사업시행인가 분석"
title = "[대전 재개발] 도마변동5구역 최신 진행 현황과 사업시행인가 분석"

width, height = 620, 400
img = QImage(width, height, QImage.Format.Format_ARGB32)
img.fill(QColor("#FFFFFF"))
p = QPainter(img)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

banner_rect = QRectF(12, 12, width - 24, 68)
p.setBrush(QColor("#1E3A8A"))
p.setPen(Qt.PenStyle.NoPen)
p.drawRoundedRect(banner_rect, 8, 8)

p.setPen(QColor("#93C5FD"))
p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
p.drawText(QRectF(24, 18, width - 48, 18), Qt.AlignmentFlag.AlignLeft, "📊 정비사업 자동 수집 분석 대시보드 | 도마변동5구역")

title_rect = QRectF(24, 38, width - 48, 36)
_draw_fitted_title(p, title_rect, title, max_size=13, min_size=9)

p.end()
img.save("scratch/test_title_rendered.png")
print("Saved scratch/test_title_rendered.png")
