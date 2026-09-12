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

def _draw_fitted_metric_value(p: QPainter, rect: QRectF, val: str, color: QColor = QColor("#0F172A")):
    p.setPen(color)
    clean_val = val.strip()
    
    fitted_font = None
    for size in [12, 11, 10]:
        font = QFont(FONT_FAMILY, size, QFont.Weight.Bold)
        fm = QFontMetrics(font)
        if fm.horizontalAdvance(clean_val) <= rect.width():
            fitted_font = font
            break
            
    if fitted_font:
        p.setFont(fitted_font)
        p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clean_val)
    else:
        p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap, clean_val)

width, height = 620, 400
img = QImage(width, height, QImage.Format.Format_ARGB32)
img.fill(QColor("#FFFFFF"))
p = QPainter(img)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

card_rect = QRectF(2, 2, width - 4, height - 4)
p.setBrush(QColor("#F8FAFC"))
p.setPen(QPen(QColor("#CBD5E1"), 1.2))
p.drawRoundedRect(card_rect, 12, 12)

banner_rect = QRectF(12, 12, width - 24, 68)
p.setBrush(QColor("#1E3A8A"))
p.setPen(Qt.PenStyle.NoPen)
p.drawRoundedRect(banner_rect, 8, 8)

p.setPen(QColor("#93C5FD"))
p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
p.drawText(QRectF(24, 20, width - 48, 18), Qt.AlignmentFlag.AlignLeft, "📊 정비사업 자동 수집 분석 대시보드 | 도마변동5구역")

title = "[대전 재개발] 도마변동5구역 최신 진행 현황과 사업시행인가 분석"
_draw_fitted_title(p, QRectF(24, 38, width - 48, 36), title)

step_y = 88
p.setPen(QColor("#334155"))
p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
p.drawText(QRectF(14, step_y, width - 28, 18), Qt.AlignmentFlag.AlignLeft, "🚀 사업 추진 단계 로드맵")

bar_y = step_y + 22
bar_rect = QRectF(14, bar_y, width - 28, 24)
p.setBrush(QColor("#E2E8F0"))
p.setPen(Qt.PenStyle.NoPen)
p.drawRoundedRect(bar_rect, 12, 12)

progress_val = 70
stage_text = "사업시행인가 완료 (관리처분 준비)"
fill_w = max(90.0, (width - 28) * (progress_val / 100.0))
fill_rect = QRectF(14, bar_y, fill_w, 24)
fill_grad = QLinearGradient(14, bar_y, 14 + fill_w, bar_y)
fill_grad.setColorAt(0.0, QColor("#2563EB"))
fill_grad.setColorAt(1.0, QColor("#059669"))
p.setBrush(QBrush(fill_grad))
p.drawRoundedRect(fill_rect, 12, 12)

p.setPen(QColor("#FFFFFF"))
p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
p.drawText(fill_rect, Qt.AlignmentFlag.AlignCenter, f"현재 공정률: {progress_val}% ({stage_text})")

grid_y = 144
box_w = (width - 36) / 2
box_h = 94

metrics = [
    ("🏢 총 세대수", "약 2,870세대 (대단지)", "#1D4ED8", "#EFF6FF", "#BFDBFE"),
    ("🏗️ 시공 브랜드", "현대건설 & GS건설 (힐스테이트·자이)", "#047857", "#ECFDF5", "#A7F3D0"),
    ("📌 추진 현황", "사업시행인가 완료 (관리처분 준비)", "#7C3AED", "#F5F3FF", "#DDD6FE"),
    ("📍 건축 규모", "지하 2층 ~ 지상 38층, 20여 개동", "#B45309", "#FFFBEB", "#FDE68A"),
]

for idx, (label, val, text_color, bg_color, border_color) in enumerate(metrics):
    r = idx // 2
    c = idx % 2
    bx = 14 + c * (box_w + 8)
    by = grid_y + r * (box_h + 8)
    b_rect = QRectF(bx, by, box_w, box_h)

    p.setBrush(QColor(bg_color))
    p.setPen(QPen(QColor(border_color), 1.2))
    p.drawRoundedRect(b_rect, 8, 8)

    p.setPen(QColor(text_color))
    p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
    p.drawText(QRectF(bx + 10, by + 8, box_w - 20, 20), Qt.AlignmentFlag.AlignLeft, label)

    _draw_fitted_metric_value(p, QRectF(bx + 10, by + 30, box_w - 20, 54), val)

footer_rect = QRectF(14, height - 30, width - 28, 20)
p.setPen(QColor("#64748B"))
p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Normal))
p.drawText(footer_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, "🏢 신우 공인중개사사무소 | 네이버 블로그 공식 포스팅 요약 차트")

p.end()
img.save("scratch/test_full_doma_card.png")
print("Saved scratch/test_full_doma_card.png")
