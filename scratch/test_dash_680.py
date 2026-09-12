import sys
sys.path.insert(0, ".")
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, QRectF

app = QApplication(sys.argv)

def create_dashboard_card(title: str, zone_name: str, zone_data: dict, office_name: str = "신우 공인중개사사무소") -> QImage:
    width = 680
    height = 430

    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor("#FFFFFF"))

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # 1. 외곽 둥근 카드 (테두리 & 은은한 배경)
    card_rect = QRectF(4, 4, width - 8, height - 8)
    p.setBrush(QColor("#F8FAFC"))
    p.setPen(QPen(QColor("#CBD5E1"), 1.5))
    p.drawRoundedRect(card_rect, 14, 14)

    # 2. 상단 헤더 배너
    banner_rect = QRectF(14, 14, width - 28, 72)
    p.setBrush(QColor("#1E3A8A"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(banner_rect, 10, 10)

    p.setPen(QColor("#93C5FD"))
    p.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Bold))
    p.drawText(QRectF(28, 22, width - 56, 18), Qt.AlignmentFlag.AlignLeft, f"📊 정비사업 자동 수집 분석 대시보드 | {zone_name}")

    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont("Malgun Gothic", 14, QFont.Weight.Bold))
    clean_title = title if len(title) <= 28 else title[:27] + "..."
    p.drawText(QRectF(28, 42, width - 56, 36), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clean_title)

    # 3. 사업 추진 로드맵 게이지 바
    step_y = 96
    p.setPen(QColor("#334155"))
    p.setFont(QFont("Malgun Gothic", 11, QFont.Weight.Bold))
    p.drawText(QRectF(16, step_y, width - 32, 20), Qt.AlignmentFlag.AlignLeft, "🚀 사업 추진 단계 로드맵")

    bar_y = step_y + 24
    bar_rect = QRectF(16, bar_y, width - 32, 26)
    p.setBrush(QColor("#E2E8F0"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(bar_rect, 13, 13)

    progress_val = zone_data.get("progress", 70)
    stage_text = zone_data.get("stage", "사업시행인가 완료")
    fill_w = max(100.0, (width - 32) * (progress_val / 100.0))
    fill_rect = QRectF(16, bar_y, fill_w, 26)
    fill_grad = QLinearGradient(16, bar_y, 16 + fill_w, bar_y)
    fill_grad.setColorAt(0.0, QColor("#2563EB"))
    fill_grad.setColorAt(1.0, QColor("#059669"))
    p.setBrush(QBrush(fill_grad))
    p.drawRoundedRect(fill_rect, 13, 13)

    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Bold))
    p.drawText(fill_rect, Qt.AlignmentFlag.AlignCenter, f"현재 공정률: {progress_val}% ({stage_text})")

    # 4. 4대 핵심 지표 2x2 카드
    grid_y = 158
    box_w = (width - 40) / 2
    box_h = 98

    metrics = [
        ("🏢 총 세대수", zone_data.get("units", "약 2,870세대"), "#1D4ED8", "#EFF6FF", "#BFDBFE"),
        ("🏗️ 시공 브랜드", zone_data.get("builder", "현대건설 & GS건설"), "#047857", "#ECFDF5", "#A7F3D0"),
        ("📌 추진 현황", stage_text, "#7C3AED", "#F5F3FF", "#DDD6FE"),
        ("📍 건축 규모", zone_data.get("scale", "지하 2층 ~ 지상 38층"), "#B45309", "#FFFBEB", "#FDE68A"),
    ]

    for idx, (label, val, text_color, bg_color, border_color) in enumerate(metrics):
        r = idx // 2
        c = idx % 2
        bx = 16 + c * (box_w + 8)
        by = grid_y + r * (box_h + 8)
        b_rect = QRectF(bx, by, box_w, box_h)

        p.setBrush(QColor(bg_color))
        p.setPen(QPen(QColor(border_color), 1.2))
        p.drawRoundedRect(b_rect, 10, 10)

        # 라벨
        p.setPen(QColor(text_color))
        p.setFont(QFont("Malgun Gothic", 11, QFont.Weight.Bold))
        p.drawText(QRectF(bx + 12, by + 10, box_w - 24, 22), Qt.AlignmentFlag.AlignLeft, label)

        # 수치/내용
        p.setPen(QColor("#0F172A"))
        p.setFont(QFont("Malgun Gothic", 13, QFont.Weight.Bold))
        val_str = val if len(val) <= 22 else val[:21] + "..."
        p.drawText(QRectF(bx + 12, by + 36, box_w - 24, 52), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, val_str)

    # 5. 하단 푸터
    footer_rect = QRectF(16, height - 32, width - 32, 22)
    p.setPen(QColor("#64748B"))
    p.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Normal))
    p.drawText(footer_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"🏢 {office_name} | 네이버 블로그 공식 포스팅 요약 차트")

    p.end()
    return img

test_zone = {
    "units": "약 2,870세대 (대단지 프리미엄)",
    "builder": "현대건설 & GS건설 컨소시엄",
    "stage": "사업시행인가 완료 (관리처분 준비)",
    "progress": 70,
    "scale": "지하 2층 ~ 지상 38층, 20여 개 동"
}
card = create_dashboard_card("도마·변동 5구역 정비사업 핵심 분석", "도마변동5구역", test_zone)
card.save("scratch/test_dashboard_680.png")
print("Saved scratch/test_dashboard_680.png")
