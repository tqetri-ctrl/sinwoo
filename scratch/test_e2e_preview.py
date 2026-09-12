import sys
sys.path.insert(0, ".")
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

app = QApplication(sys.argv)
win = MainWindow()
win.resize(1200, 850)

# Simulate generated blog post about 도마변동5구역
sample_body = """
안녕하세요! 신우 공인중개사사무소입니다.
오늘은 대전 서구의 핵심 재개발 사업지인 **도마·변동 5구역**의 최신 사업 현황을 총정리해 드립니다.

[추천 차트: 도마변동 5구역 핵심 사업 요약표]

### 1. 도마변동 5구역 사업 개요 및 로드맵
도마변동 5구역은 총 2,870여 세대 규모로 건설되는 대단지 프리미엄 신축 아파트 단지입니다.
현재 사업시행인가를 완료하고 관리처분인가를 준비 중인 핵심 단계입니다.

[추천 지도: 대전 서구 도마동 80-37 및 도마변동5구역 경계 구역 지도 첨부]

### 2. 입지 프리미엄 분석
유등천 수변 공원과 트램 2호선 등의 교통 호재를 모두 누리는 최상의 입지 조건을 갖추고 있습니다.
"""

win.edit_news_topic.setPlainText("도마변동5구역 사업시행인가 및 관리처분계획")
win.combo_titles.clear()
win.combo_titles.addItem("📌 [도마변동5구역] 2026년 최신 현황 총정리! 사업시행인가 이후 관리처분계획")
win.edit_body.setPlainText(sample_body)
win.edit_tags.setText("도마변동5구역 대전재개발 신우공인중개사")

# Trigger preview visuals generation
win.generate_preview_visuals(force_refresh=True)
win.update_preview()

win.show()
app.processEvents()

# Grab preview browser screenshot
preview_img = win.preview_browser.grab()
preview_img.save("scratch/e2e_preview_verified.png")
print("Saved scratch/e2e_preview_verified.png, size:", preview_img.width(), preview_img.height())
