import re

sample_ai_output = """
[제목 후보]
1. [도마변동5구역] 2026년 최신 사업 현황 총정리!
2. 도마변동 5구역 관리처분계획 및 프리미엄 분석

[블로그 본문]
안녕하세요! 신우 공인중개사사무소입니다.
오늘은 대전 서구의 핵심 재개발 단지인 도마변동5구역을 소개해 드립니다.

[인포그래픽 핵심 데이터]
- 대시보드 분류: 정비사업 핵심 요약
- 사업지/주제명: 도마·변동 5구역
- 추진단계/현황: 사업시행인가 완료 (관리처분인가 준비 중)
- 진행률: 70%
- 핵심지표1: 총 세대수 | 약 2,870세대 (대단지 프리미엄)
- 핵심지표2: 시공사/브랜드 | 현대건설 & GS건설 컨소시엄 (힐스테이트·자이)
- 핵심지표3: 현재 단계 | 사업시행인가 완료 (감정평가 준비)
- 핵심지표4: 건축 규모 | 지하 2층 ~ 지상 38층, 20여 개 동

[네이버 블로그 추천 태그]
#도마변동5구역 #대전재개발 #신우공인중개사
"""

SECTION_DASHBOARD = "[인포그래픽 핵심 데이터]"

def parse_dashboard_data(text: str) -> dict:
    if SECTION_DASHBOARD not in text:
        return None
    part = text.split(SECTION_DASHBOARD, 1)[1]
    if "[네이버 블로그 추천 태그]" in part:
        part = part.split("[네이버 블로그 추천 태그]", 1)[0]
    
    data = {
        "category": "부동산 핵심 분석 대시보드",
        "target_name": "",
        "stage": "사업 추진 중",
        "progress": 70,
        "metrics": []
    }

    for line in part.strip().splitlines():
        line = line.strip().lstrip("-*• ")
        if not line:
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            if "분류" in k:
                data["category"] = v
            elif "주제" in k or "구역" in k or "사업지" in k or "대상" in k:
                data["target_name"] = v
            elif "단계" in k or "현황" in k:
                data["stage"] = v
            elif "진행률" in k or "공정률" in k:
                digits = re.findall(r'\d+', v)
                if digits:
                    data["progress"] = min(100, max(0, int(digits[0])))
            elif "지표" in k or "항목" in k:
                if "|" in v:
                    m_label, m_val = v.split("|", 1)
                    data["metrics"].append((m_label.strip(), m_val.strip()))
                else:
                    data["metrics"].append((k, v))

    return data

parsed = parse_dashboard_data(sample_ai_output)
print("Parsed dashboard data:", parsed)
