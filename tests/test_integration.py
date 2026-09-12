"""
통합 기능 자동화 테스트 (tests/test_integration.py)
- 1) 정비구역 비정형 다각형 지도 생성 및 중복 방지 검증
- 2) AI 인포그래픽 핵심 데이터 파싱 및 고화질 카드 렌더링 검증
- 3) 거시/정책 뉴스 시 지도 자동 생략 검증
- 4) 구역명/위치 자동 탐색 검증
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# pyrefly: ignore [missing-import]
from PyQt6.QtWidgets import QApplication  # type: ignore
from services.gemini_service import (
    _extract_titles, _extract_body, _extract_tags,
    _extract_dashboard_data, _extract_map_data
)
from services.chart_service import render_infographic_card
from services.zone_map_service import generate_zone_map_image, extract_zone_keyword
from ui.styles import generate_blog_preview_html

app = QApplication.instance() or QApplication(sys.argv)

SAMPLE_RESPONSE_HANNAM = """
[제목 후보]
1. [한남3구역] 2026년 관리처분계획 및 이주 현황 총정리!
2. 한남3구역 디에이치 한남 최신 재개발 사업 추진 분석
3. 한남재정비촉진지구 대장주 한남3구역 입지와 미래 가치

[블로그 본문]
안녕하세요! 신우 공인중개사사무소입니다. 😊
오늘은 서울 한남뉴타운의 핵심, 한남3구역 재정비촉진지구의 최신 소식을 전해드립니다.

[📊 추천 자료: 한남3구역 핵심 사업 추진 인포그래픽]

한남3구역은 현재 이주가 90% 이상 진행되었으며 철거 작업을 눈앞에 두고 있습니다.

### 1. 사업 개요 및 입지 분석
한남3구역은 한강변을 접하고 있어 뛰어난 조망권을 자랑합니다.

[🗺️ 정비구역 / 매물 위치도: 상단 '구역 지도 복사' 후 본문에 붙여넣기]

[🗺️ 네이버 지도 첨부 추천: '한남3구역' 검색 후 등록]

궁금하신 점은 언제든 신우 공인중개사사무소로 문의주세요!

[인포그래픽 핵심 데이터]
- 대시보드 분류: 한남3구역 재정비촉진지구 핵심 분석
- 사업지/주제명: 한남3구역 (디에이치 한남)
- 추진단계/현황: 이주 및 철거 진행 중 (착공 준비)
- 진행률: 75%
- 핵심지표1: 총 건립 세대 | 5,816세대 (매머드급 단지)
- 핵심지표2: 시공사 브랜드 | 현대건설 (디에이치 한남)
- 핵심지표3: 현재 공정단계 | 이주율 90% 돌파, 철거 착수
- 핵심지표4: 단지 규모 | 지하 6층 ~ 지상 22층, 197개동

[지도 시각화 데이터]
- 지도생성: Y
- 지도검색어: 서울 용산구 한남동
- 지도표시명칭: 한남3구역 재정비촉진지구 (디에이치 한남)
- 지도지역설명: 서울 용산구 한남동 일원

[네이버 블로그 추천 태그]
#한남3구역 #한남뉴타운 #디에이치한남 #재개발
"""

SAMPLE_RESPONSE_POLICY = """
[제목 후보]
1. 2026년 스트레스 DSR 3단계 시행과 주택담보대출 한도 변화 총정리
2. 대출 규제 강화! 스트레스 DSR 3단계 핵심 체크포인트
3. 내 대출 한도는 얼마나 줄어들까? 2026 DSR 완벽 가이드

[블로그 본문]
안녕하세요! 신우 공인중개사사무소입니다. 😊
오늘은 올해부터 전면 시행되는 2026년 스트레스 DSR 3단계 정책에 대해 안내해 드립니다.

[📊 추천 자료: 스트레스 DSR 핵심 지표 인포그래픽 카드]

이번 규제로 수도권 주택담보대출 한도가 대폭 조정됩니다.

궁금하신 점은 언제든 신우 공인중개사사무소로 문의주세요!

[인포그래픽 핵심 데이터]
- 대시보드 분류: 부동산 금융·대출 규제 핵심 분석
- 사업지/주제명: 스트레스 DSR 3단계 전국 시행
- 추진단계/현황: 2026년 상반기 전면 적용
- 진행률: 100%
- 핵심지표1: 가산 금리 | 수도권 1.2%p / 비수도권 0.75%p
- 핵심지표2: 적용 대상 | 은행권 및 2금융권 전세대출·신용대출
- 핵심지표3: 한도 영향 | 연소득 6천만원 기준 약 3,000만원 축소
- 핵심지표4: 대응 전략 | 잔금 대출 사전 시뮬레이션 필수

[지도 시각화 데이터]
- 지도생성: N
- 지도검색어: 없음
- 지도표시명칭: 없음
- 지도지역설명: 없음

[네이버 블로그 추천 태그]
#스트레스DSR #대출규제 #주택담보대출 #부동산금융
"""


def test_zone_extraction():
    """지명/정비구역 키워드 추출 테스트"""
    assert extract_zone_keyword("도마변동5구역 재개발 현황") == "도마변동5구역"
    assert extract_zone_keyword("대전 서구 탄방동 1구역 숭어리샘") in ["탄방1구역", "숭어리샘"]
    assert extract_zone_keyword("둔산더샵엘리프 용문123구역") == "용문123구역"
    print("[PASS] test_zone_extraction")


def test_hannam_case():
    """재개발 구역 케이스 테스트 (지도 + 차트 + 본문)"""
    dash = _extract_dashboard_data(SAMPLE_RESPONSE_HANNAM)
    assert dash is not None
    assert dash["target_name"] == "한남3구역 (디에이치 한남)"

    map_data = _extract_map_data(SAMPLE_RESPONSE_HANNAM)
    assert map_data is not None
    assert map_data["need_map"] is True
    assert map_data["map_query"] == "서울 용산구 한남동"

    body = _extract_body(SAMPLE_RESPONSE_HANNAM)
    assert "[인포그래픽 핵심 데이터]" not in body
    assert "[지도 시각화 데이터]" not in body

    # 지도 이미지 렌더링 검증
    map_img = generate_zone_map_image(map_data["map_query"], display_title=map_data["map_title"])
    assert map_img is not None
    assert not map_img.isNull()
    assert map_img.width() == 620
    assert map_img.height() == 400

    # 차트 이미지 렌더링 검증
    chart_img = render_infographic_card(
        title="[한남3구역] 2026년 관리처분계획 및 이주 현황 총정리!",
        card_category=dash["category"],
        zone_name=dash["target_name"],
        zone_data=dash
    )
    assert chart_img is not None
    assert not chart_img.isNull()

    # 미리보기 HTML 중복 렌더링 방지 검증
    html = generate_blog_preview_html("제목", body, ["#태그"], has_chart=True, has_zone_map=True)
    assert html.count("zone_map_preview.png") == 1
    assert html.count("chart_preview.png") == 1
    print("[PASS] test_hannam_case")


def test_policy_case():
    """거시 정책 케이스 테스트 (지도 비활성화 & 차트만 생성)"""
    dash = _extract_dashboard_data(SAMPLE_RESPONSE_POLICY)
    assert dash is not None

    map_data = _extract_map_data(SAMPLE_RESPONSE_POLICY)
    assert map_data is not None
    assert map_data["need_map"] is False

    # 정책 뉴스는 지도가 None이어야 함 (대전 도마동 임의 출력 방지)
    map_img = None if not map_data.get("need_map") else generate_zone_map_image(map_data["map_query"])
    assert map_img is None

    body = _extract_body(SAMPLE_RESPONSE_POLICY)
    html = generate_blog_preview_html("정책 제목", body, ["#태그"], has_chart=True, has_zone_map=False)
    assert html.count("zone_map_preview.png") == 0
    assert html.count("chart_preview.png") == 1
    print("[PASS] test_policy_case")


if __name__ == "__main__":
    print("\n[Running Integration Tests]")
    test_zone_extraction()
    test_hannam_case()
    test_policy_case()
    print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY!")

