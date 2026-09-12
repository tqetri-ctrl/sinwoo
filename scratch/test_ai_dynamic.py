import sys
sys.path.insert(0, ".")
from PyQt6.QtWidgets import QApplication
from services.gemini_service import _extract_dashboard_data
from services.chart_service import render_infographic_card

app = QApplication(sys.argv)

sample_ai_text = """
[제목 후보]
1. [한남3구역] 2026년 최신 관리처분계획 및 이주 현황 총정리!
2. 한남3구역 디에이치 한남 사업 로드맵

[블로그 본문]
안녕하세요! 신우 공인중개사사무소입니다.
오늘은 서울 용산의 대표 재개발 사업지인 한남3구역의 최신 현황을 브리핑해 드립니다.

[인포그래픽 핵심 데이터]
- 대시보드 분류: 한남3구역 재정비촉진지구 핵심 분석
- 사업지/주제명: 한남3구역 (디에이치 한남)
- 추진단계/현황: 이주 및 철거 진행 중 (착공 준비)
- 진행률: 75%
- 핵심지표1: 총 건립 세대 | 5,816세대 (매머드급 단지)
- 핵심지표2: 시공사 브랜드 | 현대건설 (디에이치 한남)
- 핵심지표3: 현재 공정단계 | 이주율 90% 돌파, 철거 착수
- 핵심지표4: 단지 규모 | 지하 6층 ~ 지상 22층, 197개동

[네이버 블로그 추천 태그]
#한남3구역 #디에이치한남 #용산재개발
"""

dashboard_data = _extract_dashboard_data(sample_ai_text)
print("Extracted dashboard data:", dashboard_data)

card_img = render_infographic_card(
    title="[한남3구역] 2026년 최신 관리처분계획 및 이주 현황 총정리!",
    zone_name=dashboard_data.get("target_name"),
    zone_data=dashboard_data,
    office_name="신우 공인중개사사무소"
)

card_img.save("scratch/test_ai_dynamic_card.png")
print("Saved scratch/test_ai_dynamic_card.png, size:", card_img.width(), card_img.height())
