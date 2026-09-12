import sys
import os
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding='utf-8')
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, QRectF

app = QApplication(sys.argv)

def create_rich_chart_card(title, zone_info, office_name="신우 공인중개사사무소"):
    width = 720
    height = 460

    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor("#FFFFFF"))

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # 1. 배경 카드
    card_rect = QRectF(8, 8, width - 16, height - 16)
    p.setBrush(QColor("#F8FAFC"))
    p.setPen(QPen(QColor("#CBD5E1"), 1.5))
    p.drawRoundedRect(card_rect, 16, 16)

    # 2. 상단 헤더 배너
    banner_rect = QRectF(20, 20, width - 40, 80)
    p.setBrush(QColor("#1E3A8A"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(banner_rect, 10, 10)

    p.setPen(QColor("#93C5FD"))
    p.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Bold))
    p.drawText(QRectF(36, 28, width - 72, 20), Qt.AlignmentFlag.AlignLeft, "📊 공인중개사 전문 분석 | 정비사업 핵심 요약 대시보드")

    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont("Malgun Gothic", 15, QFont.Weight.Bold))
    p.drawText(QRectF(36, 50, width - 72, 40), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title[:30])

    # 3. 사업 추진 단계 로드맵 바 (5단계 프로그레스 게이지)
    step_y = 114
    p.setPen(QColor("#475569"))
    p.setFont(QFont("Malgun Gothic", 11, QFont.Weight.Bold))
    p.drawText(QRectF(22, step_y, width - 44, 22), Qt.AlignmentFlag.AlignLeft, "🚀 사업 추진 단계 로드맵")

    # 프로그레스 바 배경
    bar_y = step_y + 26
    bar_rect = QRectF(22, bar_y, width - 44, 26)
    p.setBrush(QColor("#E2E8F0"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(bar_rect, 13, 13)

    # 진행률 채우기
    progress_val = zone_info.get("progress", 70)
    fill_w = (width - 44) * (progress_val / 100.0)
    fill_rect = QRectF(22, bar_y, fill_w, 26)
    fill_grad = QLinearGradient(22, bar_y, 22 + fill_w, bar_y)
    fill_grad.setColorAt(0.0, QColor("#3B82F6"))
    fill_grad.setColorAt(1.0, QColor("#10B981"))
    p.setBrush(QBrush(fill_grad))
    p.drawRoundedRect(fill_rect, 13, 13)

    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Bold))
    p.drawText(fill_rect, Qt.AlignmentFlag.AlignCenter, f"현재 진행률: {progress_val}% ({zone_info.get('stage_name', '관리처분 준비중')})")

    # 4. 4대 핵심 지표 2x2 카드 그리드
    grid_y = 180
    box_w = (width - 54) / 2
    box_h = 96

    metrics = [
        ("🏢 총 세대수", zone_info.get("units", "약 2,870세대"), "#1D4ED8", "#EFF6FF", "#BFDBFE"),
        ("🏗️ 시공 브랜드", zone_info.get("builder", "현대건설 & GS건설"), "#047857", "#ECFDF5", "#A7F3D0"),
        ("📌 현재 단계", zone_info.get("stage", "사업시행인가 완료"), "#7C3AED", "#F5F3FF", "#DDD6FE"),
        ("📍 건축 규모", zone_info.get("scale", "지하 2층 ~ 지상 38층"), "#B45309", "#FFFBEB", "#FDE68A"),
    ]

    for idx, (label, val, text_color, bg_color, border_color) in enumerate(metrics):
        r = idx // 2
        c = idx % 2
        bx = 22 + c * (box_w + 10)
        by = grid_y + r * (box_h + 10)
        b_rect = QRectF(bx, by, box_w, box_h)

        p.setBrush(QColor(bg_color))
        p.setPen(QPen(QColor(border_color), 1.5))
        p.drawRoundedRect(b_rect, 10, 10)

        # 라벨
        p.setPen(QColor(text_color))
        p.setFont(QFont("Malgun Gothic", 11, QFont.Weight.Bold))
        p.drawText(QRectF(bx + 14, by + 12, box_w - 28, 22), Qt.AlignmentFlag.AlignLeft, label)

        # 값 (크고 굵은 폰트)
        p.setPen(QColor("#0F172A"))
        p.setFont(QFont("Malgun Gothic", 13, QFont.Weight.Bold))
        val_text = val if len(val) <= 24 else val[:23] + "..."
        p.drawText(QRectF(bx + 14, by + 40, box_w - 28, 44), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, val_text)

    # 5. 하단 푸터
    footer_rect = QRectF(22, height - 38, width - 44, 24)
    p.setPen(QColor("#64748B"))
    p.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Normal))
    p.drawText(footer_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"🏢 {office_name} | 네이버 블로그 공식 포스팅 요약 차트")

    p.end()
    return img

zone_info = {
    "units": "2,870세대 (대단지 프리미엄)",
    "builder": "힐스테이트 + 자이 컨소시엄",
    "stage": "사업시행인가 완료 (관리처분 준비)",
    "stage_name": "관리처분 준비중",
    "progress": 70,
    "scale": "지하 2층 ~ 지상 38층, 20여 개 동"
}
chart = create_rich_chart_card("도마변동 5구역 정비사업 핵심 분석", zone_info)
chart.save("scratch/test_rich_chart.png")
print("Saved scratch/test_rich_chart.png, size:", chart.width(), chart.height())
