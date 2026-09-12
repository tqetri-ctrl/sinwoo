import sys
sys.path.insert(0, ".")
from PyQt6.QtWidgets import QApplication, QTextBrowser
from PyQt6.QtGui import QImage, QPainter, QTextDocument
from PyQt6.QtCore import QUrl, QRectF
from ui.styles import generate_blog_preview_html
from services.chart_service import render_infographic_card
from services.zone_map_service import generate_zone_map_image, get_zone_data

app = QApplication(sys.argv)
tb = QTextBrowser()
tb.resize(760, 1000)

zone_data = get_zone_data("도마변동5구역")
chart_img = render_infographic_card(
    title="[도마변동5구역] 2026년 최신 사업 현황 총정리!",
    zone_name="도마변동5구역",
    zone_data=zone_data
)
map_img = generate_zone_map_image("도마변동5구역")

tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("chart_preview.png"), chart_img)
tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("zone_map_preview.png"), map_img)

sample_body = """
안녕하세요! 신우 공인중개사사무소입니다.
오늘은 대전 서구의 핵심 재개발 사업지인 **도마·변동 5구역**의 최신 사업 현황을 총정리해 드립니다.

[추천 차트: 도마변동 5구역 핵심 사업 요약표]

### 1. 도마변동 5구역 사업 개요 및 로드맵
도마변동 5구역은 총 2,870여 세대 규모로 건설되는 대단지 프리미엄 신축 아파트 단지입니다.

[추천 지도: 대전 서구 도마동 80-37 및 도마변동5구역 경계 구역 지도 첨부]

### 2. 입지 프리미엄 분석
유등천 수변 공원과 트램 2호선 등의 교통 호재를 모두 누리는 최상의 입지 조건입니다.
"""

html = generate_blog_preview_html(
    title="[도마변동5구역] 2026년 최신 현황 총정리!",
    body_markdown=sample_body,
    tags=["도마변동5구역", "대전재개발"],
    has_chart=True,
    has_zone_map=True
)

tb.setHtml(html)
doc = tb.document()
doc.setTextWidth(720)

# Render entire document onto high-res canvas
total_h = int(doc.size().height()) + 50
full_img = QImage(740, total_h, QImage.Format.Format_ARGB32)
full_img.fill(0xFFFFFFFF)

p = QPainter(full_img)
doc.drawContents(p, QRectF(10, 10, 720, total_h))
p.end()

full_img.save("scratch/full_page_render.png")
print("Saved scratch/full_page_render.png, total height:", total_h)
