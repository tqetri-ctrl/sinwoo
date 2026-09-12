import sys
sys.path.insert(0, ".")
from PyQt6.QtWidgets import QApplication, QTextBrowser
from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QPen, QBrush, QLinearGradient, QTextDocument
from PyQt6.QtCore import Qt, QRectF, QUrl

app = QApplication(sys.argv)

def create_card_620(title, zone_name, zone_data, office_name="신우 공인중개사사무소"):
    width = 620
    height = 400
    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor("#FFFFFF"))

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # 1. 외곽 둥근 카드 (테두리 & 은은한 배경)
    card_rect = QRectF(2, 2, width - 4, height - 4)
    p.setBrush(QColor("#F8FAFC"))
    p.setPen(QPen(QColor("#CBD5E1"), 1.2))
    p.drawRoundedRect(card_rect, 12, 12)

    # 2. 상단 헤더 배너
    banner_rect = QRectF(12, 12, width - 24, 68)
    p.setBrush(QColor("#1E3A8A"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(banner_rect, 8, 8)

    p.setPen(QColor("#93C5FD"))
    p.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Bold))
    p.drawText(QRectF(24, 20, width - 48, 18), Qt.AlignmentFlag.AlignLeft, f"📊 정비사업 자동 수집 분석 대시보드 | {zone_name}")

    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont("Malgun Gothic", 13, QFont.Weight.Bold))
    clean_title = title if len(title) <= 28 else title[:27] + "..."
    p.drawText(QRectF(24, 40, width - 48, 34), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clean_title)

    # 3. 사업 추진 로드맵 게이지 바
    step_y = 90
    p.setPen(QColor("#334155"))
    p.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Bold))
    p.drawText(QRectF(14, step_y, width - 28, 18), Qt.AlignmentFlag.AlignLeft, "🚀 사업 추진 단계 로드맵")

    bar_y = step_y + 22
    bar_rect = QRectF(14, bar_y, width - 28, 24)
    p.setBrush(QColor("#E2E8F0"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(bar_rect, 12, 12)

    progress_val = zone_data.get("progress", 70)
    stage_text = zone_data.get("stage", "사업시행인가 완료")
    fill_w = max(90.0, (width - 28) * (progress_val / 100.0))
    fill_rect = QRectF(14, bar_y, fill_w, 24)
    fill_grad = QLinearGradient(14, bar_y, 14 + fill_w, bar_y)
    fill_grad.setColorAt(0.0, QColor("#2563EB"))
    fill_grad.setColorAt(1.0, QColor("#059669"))
    p.setBrush(QBrush(fill_grad))
    p.drawRoundedRect(fill_rect, 12, 12)

    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Bold))
    p.drawText(fill_rect, Qt.AlignmentFlag.AlignCenter, f"현재 공정률: {progress_val}% ({stage_text})")

    # 4. 4대 핵심 지표 2x2 카드
    grid_y = 146
    box_w = (width - 36) / 2
    box_h = 92

    metrics = [
        ("🏢 총 세대수", zone_data.get("units", "약 2,870세대"), "#1D4ED8", "#EFF6FF", "#BFDBFE"),
        ("🏗️ 시공 브랜드", zone_data.get("builder", "현대건설 & GS건설"), "#047857", "#ECFDF5", "#A7F3D0"),
        ("📌 추진 현황", stage_text, "#7C3AED", "#F5F3FF", "#DDD6FE"),
        ("📍 건축 규모", zone_data.get("scale", "지하 2층 ~ 지상 38층"), "#B45309", "#FFFBEB", "#FDE68A"),
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

        # 라벨
        p.setPen(QColor(text_color))
        p.setFont(QFont("Malgun Gothic", 10, QFont.Weight.Bold))
        p.drawText(QRectF(bx + 10, by + 8, box_w - 20, 20), Qt.AlignmentFlag.AlignLeft, label)

        # 수치/내용
        p.setPen(QColor("#0F172A"))
        p.setFont(QFont("Malgun Gothic", 12, QFont.Weight.Bold))
        val_str = val if len(val) <= 22 else val[:21] + "..."
        p.drawText(QRectF(bx + 10, by + 30, box_w - 20, 52), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, val_str)

    # 5. 하단 푸터
    footer_rect = QRectF(14, height - 30, width - 28, 20)
    p.setPen(QColor("#64748B"))
    p.setFont(QFont("Malgun Gothic", 9, QFont.Weight.Normal))
    p.drawText(footer_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"🏢 {office_name} | 네이버 블로그 공식 포스팅 요약 차트")

    p.end()
    return img

test_zone = {
    "units": "약 2,870세대 (대단지)",
    "builder": "현대건설 & GS건설",
    "stage": "사업시행인가 완료",
    "progress": 70,
    "scale": "지하 2층 ~ 지상 38층, 20개동"
}
chart_620 = create_card_620("도마·변동 5구역 정비사업 핵심 분석", "도마변동5구역", test_zone)

tb = QTextBrowser()
tb.resize(800, 750)
tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("chart_preview.png"), chart_620)

html = f"""
<div style="max-width: 660px; margin: 0 auto; font-family: 'Malgun Gothic';">
  <div class="visual-card-box chart-visual" style="margin: 12px 0; background: #F8FAFC; border: 1.5px solid #BFDBFE; border-radius: 12px; padding: 10px; text-align: center;">
    <div style="font-size: 13px; font-weight: 700; color: #1D4ED8; margin-bottom: 8px; text-align: left;">
      📊 <strong>[핵심 요약 인포그래픽 카드]</strong> - 도마변동 5구역 핵심 사업 요약표
    </div>
    <img src="chart_preview.png" width="620" height="400" style="display: block; margin: 0 auto;">
    <div style="font-size: 12px; color: #64748B; margin-top: 6px; text-align: center;">
      💡 상단 <strong>[📊 차트 복사]</strong> 버튼을 누르면 이 고화질 카드가 클립보드에 복사되어 블로그에 바로 첨부됩니다.
    </div>
  </div>
</div>
"""
tb.setHtml(html)
tb.show()
tb.grab().save("scratch/test_preview_620.png")
print("Saved scratch/test_preview_620.png")
