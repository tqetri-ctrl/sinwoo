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
from services.chart_service import render_infographic_card, _build_zone_dashboard_metrics, _resolve_progress_bar_text
from services.text_utils import deduplicate_consecutive_emojis, has_leading_emoji, strip_leading_emojis
from services.zone_map_service import generate_zone_map_image, extract_zone_keyword
from ui.styles import (
    generate_blog_preview_html, is_card_news_text, render_card_news_blocks,
    _render_placeholder_box, _render_chart_embed, _render_map_embed
)

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
    # 블로그 무관 안내문 제거 검증 (네이버 지도 검색 등록 및 상단 복사 지시문 제거)
    assert "네이버 지도 첨부 추천" not in body
    assert "상단 '구역 지도 복사' 후 본문에 붙여넣기" not in body
    # 플레이스홀더는 원형 보존 검증
    assert "[🗺️ 정비구역 / 매물 위치도]" in body
    assert "[📊 추천 자료: 한남3구역 핵심 사업 추진 인포그래픽]" in body

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


SAMPLE_RESPONSE_CARD_NEWS = """
[제목 후보]
1. ⚡ 3분 만에 끝내는 2026 재개발 핵심 총정리
2. 한눈에 보는 재개발 사업 단계별 완벽 가이드
3. 정비사업 투자 전 반드시 알아야 할 체크포인트

[블로그 본문]
[카드 01 | 표지]
# ⚡ 2026 재개발 핵심 총정리
- 바쁜 분들을 위한 한눈에 쏙 들어오는 3분 카드뉴스

[카드 02 | 이슈 브리핑]
### 🔍 왜 지금 주목해야 할까요?
- 최근 정부의 정비사업 규제 완화 발표로 전국 주요 사업지가 들썩이고 있습니다.
- 사업 단계에 따라 기대 수익과 투자 리스크가 극명하게 갈리기 때문입니다.

[카드 03 | 핵심 팩트 체크]
### 📌 3대 핵심 추진 단계
- **조합설립**: 사업 본격 착수 (진행률 약 35%)
- **사업시행인가**: 건축 및 세대수 확정 (진행률 약 55%)
- **관리처분인가**: 조합원 분양가 및 비례율 산정 (진행률 약 70%)

[카드 04 | 한눈에 보는 수치]
### 📊 단계별 진행률 & 지표
| 단계 구분 | 종전 평균 소요 | 개편 후 단축 목표 |
| :--- | :--- | :--- |
| 구역지정~인가 | 5.2년 | 3.5년 |
| 인가~착공 | 4.8년 | 3.0년 |

[📊 추천 자료: 정비사업 단계별 핵심 요약 카드]

[카드 05 | 공인중개사 실전 가이드]
### 💡 실거주 & 투자자 맞춤 가이드
- **실거주 목적**: 사업시행인가 완료 후 이주비 대출 조건을 꼼꼼히 확인하세요.
- **투자 목적**: 관리처분인가 전후 프리미엄(P) 변동폭을 반드시 점검하세요.

[카드 06 | 에필로그 & 상담 안내]
### 🤝 신우공인중개사 3줄 브리핑
- 정비사업은 추진 단계에 맞는 타이밍 선점이 핵심입니다.
- 복잡한 권리가액 및 비례율 계산, 전문가와 함께하세요.
- 친절하고 정확한 상담으로 보답하겠습니다.

[📞 추천 배너: 신우 공인중개사사무소 명함 배너]

[인포그래픽 핵심 데이터]
- 대시보드 분류: 2026 재개발 정비사업 핵심 요약
- 사업지/주제명: 2026 정비사업 가이드
- 추진단계/현황: 사업시행인가 및 관리처분 단계
- 진행률: 70%
- 핵심지표1: 단축 목표 | 평균 10년 -> 6.5년 단축
- 핵심지표2: 안전진단 | 통과 기준 대폭 완화
- 핵심지표3: 분양권 자격 | 권리산정기준일 주의
- 핵심지표4: 자금 조달 | 이주비/중도금 대출 점검

[지도 시각화 데이터]
- 지도생성: N
- 지도검색어: 없음
- 지도표시명칭: 없음
- 지도지역설명: 없음

[네이버 블로그 추천 태그]
#재개발 #카드뉴스 #정비사업 #신우공인중개사 #부동산투자
"""


def test_card_news_case():
    """3분 요약 카드뉴스 포맷 감지, 카드 슬라이드 분할 및 HTML 박스 서식 검증"""
    body = _extract_body(SAMPLE_RESPONSE_CARD_NEWS)
    assert is_card_news_text(body) is True

    # 1) UI 미리보기 HTML 렌더링 검증
    html = generate_blog_preview_html("3분 카드뉴스", body, ["#재개발", "#카드뉴스"], has_chart=True, has_zone_map=False)
    assert '<div class="card-news-frame">' in html
    assert html.count('<div class="card-news-frame">') == 6
    assert "CARD 01 | 표지" in html
    assert "CARD 04 | 한눈에 보는 수치" in html
    assert "CARD 06 | 에필로그 &amp; 상담 안내" in html or "CARD 06 | 에필로그" in html
    assert html.count("chart_preview.png") == 1

    # 2) 네이버 블로그 스마트에디터 ONE 복사용 인라인 스타일 박스 검증
    clip_html = render_card_news_blocks(body, has_chart=True, has_zone_map=False, for_clipboard=True)
    assert "background-color: #F8FAFC" in clip_html
    assert "border: 1.5px solid #CBD5E1" in clip_html
    assert "CARD 01 | 표지" in clip_html
    assert "CARD 06" in clip_html
    print("[PASS] test_card_news_case")


def test_emoji_deduplication():
    """프로젝트 전체 이모지 중복 발생 방지 검증"""
    import re

    # 1. 텍스트 연속 중복 이모지 축약 검증
    sample_text = "## ⚡ ⚡ 신속통합기획 🔍  🔍 핵심 체크포인트 😊😊 안녕하세요! 🏢 🏢 신우부동산 🏗️ 🏗️ 건설"
    deduped = deduplicate_consecutive_emojis(sample_text)
    assert "⚡ ⚡" not in deduped
    assert "🔍  🔍" not in deduped
    assert "😊😊" not in deduped
    assert "🏢 🏢" not in deduped
    assert "🏗️ 🏗️" not in deduped
    assert "## ⚡ 신속통합기획" in deduped
    assert "🔍 핵심 체크포인트" in deduped
    assert "😊 안녕하세요!" in deduped
    assert "🏢 신우부동산" in deduped
    assert "🏗️ 건설" in deduped

    # 2. 선행 이모지 감지 및 제거 검증
    assert has_leading_emoji("🏢 사업 규모") is True
    assert has_leading_emoji("사업 규모") is False
    assert has_leading_emoji("🏘️ 총 건립 세대") is True
    assert strip_leading_emojis("🏢 🏢 신우부동산") == "신우부동산"
    assert strip_leading_emojis("✨ 환하게 웃는 스티커") == "환하게 웃는 스티커"
    assert strip_leading_emojis("📸 거실 전경") == "거실 전경"

    # 3. clean_body_instructions의 플레이스홀더 및 본문 이모지 정제 검증
    raw_blog_body = """
    ## ⚡ ⚡ 신속통합기획 추진 현황
    
    [✨ 추천 스티커: ✨ 환하게 웃으며 인사하는 스티커]
    [📸 추천 사진: 📸 단지 조감도 사진]
    [📊 추천 자료: 📊 사업 추진 일정표]
    
    궁금한 점은 문의주세요! 😊 😊
    """
    cleaned_body = _extract_body(raw_blog_body)
    assert "⚡ ⚡" not in cleaned_body
    assert "😊 😊" not in cleaned_body
    assert "[✨ 추천 스티커: 환하게 웃으며 인사하는 스티커]" in cleaned_body
    assert "[📸 추천 사진: 단지 조감도 사진]" in cleaned_body
    assert "[📊 추천 자료: 사업 추진 일정표]" in cleaned_body

    # 4. 차트 대시보드 4대 지표 카드 중복 아이콘 방지 검증
    zone_data_with_emojis = {
        "metrics": [
            ("🏘️ 단지 세대수", "5,000세대"),
            ("🛠️ 시공 브랜드", "현대건설"),
            ("📌 추진 현황", "관리처분인가"),
            ("📍 사업 면적", "30만㎡"),
        ]
    }
    metrics = _build_zone_dashboard_metrics(zone_data_with_emojis, "관리처분인가")
    assert metrics[0][0] == "🏘️ 단지 세대수"  # '🏢 🏘️'로 중복 추가되지 않아야 함!
    assert metrics[1][0] == "🛠️ 시공 브랜드"  # '🏗️ 🛠️'로 중복 추가되지 않아야 함!

    # 5. 프로그레스 바 상태 텍스트 중복 방지 검증
    p1 = _resolve_progress_bar_text("재개발 매물", "🔑 즉시 입주 가능 (현재 공실)", 100)
    assert p1 == "🔑 입주 상태: 즉시 입주 가능 (현재 공실)"  # '🔑 입주 상태: 🔑 즉시...' X
    assert p1.count("🔑") == 1

    p2 = _resolve_progress_bar_text("아파트 단지", "✨ 신축 첫 입주 (준공 완료)", 100)
    assert p2 == "✨ 신축 첫 입주: 준공 완료" or p2 == "✨ 신축 첫 입주: (준공 완료)" or "준공" in p2
    assert p2.count("✨") == 1

    p3 = _resolve_progress_bar_text("정책 분석", "✅ 2026년 상반기 전면 적용", 100)
    assert p3 == "✅ 시행 및 정착 완료: 2026년 상반기 전면 적용"
    assert p3.count("✅") == 1

    # 6. UI 플레이스홀더 박스 렌더링 시 내부 중복 이모지 정제 검증
    match_sticker = re.search(r'\[([^\]\r\n]+)\]', '[✨ 추천 스티커: ✨ 박수 치는 캐릭터]')
    html_sticker = _render_placeholder_box(match_sticker)
    assert '<span class="icon">✨</span><strong>[네이버 스티커]</strong> 박수 치는 캐릭터' in html_sticker
    assert "✨ [네이버 스티커] ✨" not in html_sticker

    match_photo = re.search(r'\[([^\]\r\n]+)\]', '[📸 추천 사진: 📸 거실 및 침실 사진]')
    html_photo = _render_placeholder_box(match_photo)
    assert '<span class="icon">📸</span><strong>[추천 사진]</strong> 거실 및 침실 사진' in html_photo
    assert "📸 [추천 사진] 📸" not in html_photo

    # 7. 임베드 카드 타이틀 중복 방지 검증
    chart_html = _render_chart_embed("📊 한남3구역 인포그래픽 요약")
    assert "📊 <strong>[핵심 요약 인포그래픽 카드]</strong> - 한남3구역 인포그래픽 요약" in chart_html
    assert "카드] - 📊" not in chart_html

    map_html = _render_map_embed("🗺️ 정비구역 위치도 및 지적도")
    assert "🗺️ <strong>[정비구역 / 매물 위치도]</strong> - 정비구역 위치도 및 지적도" in map_html or "🗺️ <strong>[정비구역 / 매물 위치도]</strong> - 지적도" in map_html
    assert "위치도] - 🗺️" not in map_html

    print("[PASS] test_emoji_deduplication")


if __name__ == "__main__":
    print("\n[Running Integration Tests]")
    test_zone_extraction()
    test_hannam_case()
    test_policy_case()
    test_card_news_case()
    test_emoji_deduplication()
    print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY!")


