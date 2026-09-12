import sys
sys.path.insert(0, ".")
from PyQt6.QtWidgets import QApplication, QTextBrowser
from PyQt6.QtGui import QImage, QTextDocument
from PyQt6.QtCore import QUrl
from ui.styles import generate_blog_preview_html

app = QApplication(sys.argv)
tb = QTextBrowser()
tb.resize(800, 950)

# Load images into resources
chart_img = QImage("scratch/test_dashboard_680.png")
map_img = QImage("scratch/test_map_zoom17.png")

tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("chart_preview.png"), chart_img)
tb.document().addResource(QTextDocument.ResourceType.ImageResource.value, QUrl("zone_map_preview.png"), map_img)

sample_body = """
안녕하세요! 신우 공인중개사사무소입니다.
오늘은 대전 서구의 핵심 재정비촉진지구인 **도마·변동 5구역**의 2026년 최신 사업 현황 및 입지 분석을 전해드립니다.

[추천 차트: 도마변동 5구역 핵심 사업 요약표]

### 1. 사업 개요 및 추진 단계 로드맵
도마변동 5구역은 총 2,870여 세대 규모로 조성되는 대단지 프리미엄 신축 아파트 단지입니다.
현재 사업시행인가를 완료하고 관리처분인가를 준비하는 단계로 진입하여 투자가치가 매우 높습니다.

[추천 지도: 대전 서구 도마동 80-37 및 도마변동5구역 경계 구역 지도 첨부]

### 2. 입지 프리미엄
유등천 수변 공원과 인접해 쾌적한 힐링 라이프를 누릴 수 있으며, 트램 2호선 및 충청권 광역철도 호재를 공유합니다.
"""

# Let's test with current styles.py
html = generate_blog_preview_html(
    title="[도마변동5구역] 2026년 최신 사업 현황 총정리! 사업시행인가 이후 관리처분계획",
    body_markdown=sample_body,
    tags=["도마변동5구역", "대전재개발", "도마변동재개발", "신우부동산"],
    has_chart=True,
    has_zone_map=True
)

tb.setHtml(html)
tb.show()
tb.grab().save("scratch/test_preview_full.png")
print("Saved scratch/test_preview_full.png")
