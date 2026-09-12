"""
실시간 부동산 뉴스 및 보도자료 수집 서비스 (하이브리드 지원)
- 1) 무료 오픈 실시간 뉴스 RSS 검색 (Google News RSS, API 키 불필요, 100% 무료)
- 2) 네이버 뉴스 공식 오픈 API (Client ID/Secret 등록 시 네이버 뉴스 우선 수집)
"""

import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime


def _clean_html_tags(text: str) -> str:
    """HTML 엔티티 및 태그 제거"""
    if not text:
        return ""
    # &quot;, &amp;, &lt;, &gt;, &apos; 등 변환
    decoded = html.unescape(text)
    # <b> 태그 등 HTML 태그 제거
    cleaned = re.sub(r"<[^>]+>", "", decoded)
    return cleaned.strip()


def _parse_pub_date(pub_date_str: str) -> str:
    """RFC 822 또는 다양한 날짜 문자열을 알기 쉬운 한국어 형식으로 변환"""
    if not pub_date_str:
        return ""
    try:
        # e.g., 'Fri, 04 Sep 2026 06:28:20 GMT'
        # e.g., 'Fri, 04 Sep 2026 15:28:20 +0900'
        parts = pub_date_str.split()
        if len(parts) >= 4:
            # day, month, year
            day = parts[1]
            month_str = parts[2]
            year = parts[3]
            month_map = {
                "Jan": "1월", "Feb": "2월", "Mar": "3월", "Apr": "4월",
                "May": "5월", "Jun": "6월", "Jul": "7월", "Aug": "8월",
                "Sep": "9월", "Oct": "10월", "Nov": "11월", "Dec": "12월"
            }
            month = month_map.get(month_str, month_str)
            return f"{year}년 {month} {day}일"
    except Exception:
        pass
    return pub_date_str[:16]


def _extract_source_and_title(clean_title: str, source_elem) -> tuple:
    """기사 제목에서 언론사명 분리"""
    source_name = ""
    if source_elem is not None and source_elem.text:
        source_name = source_elem.text.strip()
    elif " - " in clean_title:
        parts = clean_title.rsplit(" - ", 1)
        clean_title = parts[0].strip()
        source_name = parts[1].strip()
    return clean_title, source_name or "주요 언론사"


def _parse_rss_item(item) -> dict:
    """개별 RSS item 요소를 기사 딕셔너리로 변환"""
    title_elem = item.find("title")
    link_elem = item.find("link")
    pub_date_elem = item.find("pubDate")
    desc_elem = item.find("description")
    source_elem = item.find("source")

    raw_title = title_elem.text if title_elem is not None and title_elem.text else ""
    clean_title = _clean_html_tags(raw_title)
    if not clean_title:
        return {}

    clean_title, source_name = _extract_source_and_title(clean_title, source_elem)
    raw_desc = desc_elem.text if desc_elem is not None and desc_elem.text else ""
    raw_date = pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text else ""
    link = link_elem.text if link_elem is not None and link_elem.text else ""

    return {
        "title": clean_title,
        "description": _clean_html_tags(raw_desc),
        "pub_date": _parse_pub_date(raw_date),
        "source": source_name,
        "link": link
    }


def search_google_news_rss(query: str, max_results: int = 5) -> list:
    """
    Google News RSS를 통한 100% 무료 실시간 최신 뉴스 검색 (API 키 불필요)
    """
    articles = []
    try:
        encoded_query = urllib.parse.quote(f"{query} 부동산")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

        with urllib.request.urlopen(req, timeout=5) as resp:
            xml_data = resp.read()
            tree = ET.fromstring(xml_data)
            for item in tree.findall(".//item")[:max_results]:
                parsed = _parse_rss_item(item)
                if parsed:
                    articles.append(parsed)
    except Exception as e:
        print(f"[NewsSearch] Google News RSS 검색 실패: {e}")

    return articles


def search_naver_news_api(query: str, client_id: str, client_secret: str, max_results: int = 5) -> list:
    """
    네이버 공식 오픈 API를 통한 실시간 뉴스 검색 (일 25,000건 무료)
    """
    articles = []
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display={max_results}&sort=sim"
        req = urllib.request.Request(
            url,
            headers={
                "X-Naver-Client-Id": client_id.strip(),
                "X-Naver-Client-Secret": client_secret.strip(),
                "User-Agent": "Sinwoo-Blog-Maker/1.0"
            }
        )

        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("items", []):
                    clean_title = _clean_html_tags(item.get("title", ""))
                    clean_desc = _clean_html_tags(item.get("description", ""))
                    raw_date = item.get("pubDate", "")
                    formatted_date = _parse_pub_date(raw_date)
                    link = item.get("originallink", "") or item.get("link", "")

                    if clean_title:
                        articles.append({
                            "title": clean_title,
                            "description": clean_desc,
                            "pub_date": formatted_date,
                            "source": "네이버 뉴스",
                            "link": link
                        })
    except Exception as e:
        print(f"[NewsSearch] 네이버 뉴스 API 검색 실패: {e}")

    return articles


YONHAP_ECONOMY_RSS = "https://www.yna.co.kr/rss/economy.xml"
REAL_ESTATE_KEYWORDS = [
    "부동산", "아파트", "청약", "분양", "전세", "월세", "주택", "재건축", "재개발",
    "토지", "빌라", "오피스텔", "상가", "임대", "국토부", "LH", "HUG", "공인중개",
    "집값", "매매", "취득세", "양도세", "공시지가", "금리", "건설", "분양가", "입주", "공공주택"
]

# 연합뉴스 RSS 캐시 (3분 유효, 중복 네트워크 트래픽 및 지연 완전 제거)
_YONHAP_CACHE = {
    "articles": [],
    "last_fetched": 0.0
}
CACHE_TTL = 180  # 3분(180초)

_STOPWORDS = {
    "관련", "대해", "대한", "및", "등", "뉴스", "소식", "최근", "올해", "내년",
    "오늘", "내일", "기준", "어떻게", "무엇", "이유", "전망", "분석", "시장",
    "이", "그", "저", "것", "수"
}


def _get_or_fetch_yonhap_cache(force_refresh: bool = False) -> list:
    """연합뉴스 경제 RSS를 조회하여 캐시에 보관 (TTL: 3분, 네트워크 부하 최소화)"""
    global _YONHAP_CACHE
    now = time.time()
    if not force_refresh and _YONHAP_CACHE["articles"] and (now - _YONHAP_CACHE["last_fetched"] < CACHE_TTL):
        return _YONHAP_CACHE["articles"]

    articles = []
    try:
        req = urllib.request.Request(
            YONHAP_ECONOMY_RSS,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            xml_data = resp.read()
            tree = ET.fromstring(xml_data)
            for item in tree.findall(".//item"):
                title = item.findtext("title") or ""
                desc = item.findtext("description") or ""
                link = item.findtext("link") or ""
                raw_date = item.findtext("pubDate") or ""

                clean_title = _clean_html_tags(title)
                clean_desc = _clean_html_tags(desc)

                if clean_title:
                    articles.append({
                        "title": clean_title,
                        "description": clean_desc,
                        "pub_date": _parse_pub_date(raw_date),
                        "source": "연합뉴스",
                        "link": link
                    })

            if articles:
                _YONHAP_CACHE["articles"] = articles
                _YONHAP_CACHE["last_fetched"] = now
    except Exception as e:
        print(f"[NewsSearch] 연합뉴스 경제 RSS 수집 실패: {e}")

    return _YONHAP_CACHE["articles"]


def fetch_yonhap_realestate_news(max_results: int = 12) -> list:
    """
    연합뉴스 경제 RSS에서 국가기간통신사의 최고 공신력 부동산/주택/정책 속보만 필터링 수집
    (인메모리 캐시 적용으로 초고속 반환, 100% 무료)
    """
    all_articles = _get_or_fetch_yonhap_cache()
    filtered = []
    for art in all_articles:
        combined = f"{art.get('title', '')} {art.get('description', '')}"
        if any(kw in combined for kw in REAL_ESTATE_KEYWORDS):
            filtered.append(art)
            if len(filtered) >= max_results:
                break
    return filtered


def _extract_query_keywords(query: str) -> list:
    """사용자 입력 검색어에서 의미 있는 핵심 키워드 토큰 추출"""
    if not query:
        return []
    cleaned = re.sub(r"[^\w\s]", " ", query)
    tokens = cleaned.split()
    keywords = []
    for token in tokens:
        t = token.strip()
        if len(t) >= 2 and t not in _STOPWORDS:
            keywords.append(t)
    return keywords


def _score_yonhap_article(art: dict, clean_query: str, keywords: list) -> int:
    """단일 연합뉴스 기사와 검색어 간 연관도 점수 계산"""
    title = art.get("title", "")
    desc = art.get("description", "")
    combined = f"{title} {desc}"

    score = 0
    # 1. 완전 일치 또는 문구 포함 가산점
    if clean_query and clean_query in title:
        score += 10
    elif clean_query and clean_query in desc:
        score += 4

    # 2. 키워드별 매칭 가산점 (제목 3점, 요약 1점)
    for kw in keywords:
        if kw in title:
            score += 3
        elif kw in desc:
            score += 1

    # 3. 부동산 핵심 키워드 포함 시 보너스 (부동산 관련성 보장)
    if any(rw in combined for rw in REAL_ESTATE_KEYWORDS):
        score += 1

    return score


def search_yonhap_by_keywords(query: str, max_results: int = 5) -> list:
    """
    캐시된 연합뉴스 속보 중에서 사용자 검색 키워드와 연관성이 높은 기사를 인메모리 매칭
    (네트워크 추가 지연 0ms, 100% 무료 공신력 최우선 기사 추출)
    """
    all_articles = _get_or_fetch_yonhap_cache()
    if not all_articles:
        return []

    keywords = _extract_query_keywords(query)
    clean_query = query.strip()

    scored_articles = []
    for art in all_articles:
        score = _score_yonhap_article(art, clean_query, keywords)
        # 최소 1개 이상 제목 키워드 매칭(3점) 또는 구문 일치 시 후보 채택
        if score >= 3:
            scored_articles.append((score, art))

    # 점수 높은 순 정렬
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    return [art for _, art in scored_articles[:max_results]]


def _add_unique_articles(target: list, candidates: list, seen: set, max_count: int):
    """중복 기사를 배제하며 대상 목록에 기사 추가"""
    for art in candidates:
        norm = re.sub(r"[\W_]+", "", art.get("title", ""))
        if norm and norm not in seen:
            seen.add(norm)
            target.append(art)
            if len(target) >= max_count:
                break


def _fetch_external_news(query: str, needed: int, config: dict = None) -> list:
    """네이버 API 또는 Google News RSS를 통한 외부 뉴스 보강"""
    if needed <= 0:
        return []

    cfg = config or {}
    naver_id = cfg.get("naver_client_id", "").strip()
    naver_secret = cfg.get("naver_client_secret", "").strip()

    results = []
    if naver_id and naver_secret:
        results = search_naver_news_api(query, naver_id, naver_secret, max_results=needed)

    if len(results) < needed:
        remaining = needed - len(results)
        google_results = search_google_news_rss(query, max_results=remaining + 2)
        results.extend(google_results)

    return results


def fetch_hybrid_news(query: str, config: dict = None, max_results: int = 5) -> list:
    """
    하이브리드 스마트 뉴스 수집 파이프라인:
    1단계: 캐시된 연합뉴스(국가기간통신사) 실시간 RSS에서 키워드 인메모리 검색 (<1ms 지연, 최고 공신력)
    2단계: 연합뉴스 매칭 결과가 max_results보다 부족한 경우, 네이버 API(설정 시) 또는 Google News RSS로 부족한 수량만큼 실시간 보강
    3단계: 중복 기사 필터링 후 최종 기사 목록 반환
    """
    articles = []
    seen_titles = set()

    # 1. 최고 공신력 연합뉴스 인메모리 키워드 매칭 우선 수행
    yonhap_matches = search_yonhap_by_keywords(query, max_results=max_results)
    _add_unique_articles(articles, yonhap_matches, seen_titles, max_results)

    # 2. 기사 부족 시 외부 검색(네이버/구글)으로 실시간 보강
    if len(articles) < max_results:
        remaining = max_results - len(articles)
        supplementary = _fetch_external_news(query, remaining, config)
        _add_unique_articles(articles, supplementary, seen_titles, max_results)

    return articles[:max_results]


def format_news_for_prompt(articles: list) -> str:
    """수집된 뉴스 기사 목록을 Gemini 프롬프트용 텍스트 블록으로 포맷팅 (저작권 보호 및 안전 인용 원칙 포함)"""
    if not articles:
        return ""

    lines = [
        "\n### [📡 실시간 수집된 최신 언론 보도 및 핵심 팩트 자료]",
        "아래는 인터넷에서 실시간으로 수집된 최신 관련 기사들입니다. 이 팩트와 발표 시점, 주요 수치를 본문에 자연스럽게 인용하여 신뢰성을 극대화하세요:\n"
    ]

    for idx, art in enumerate(articles, 1):
        title = art.get("title", "")
        source = art.get("source", "")
        date = art.get("pub_date", "")
        desc = art.get("description", "")
        meta = []
        if source:
            meta.append(f"출처: {source}")
        if date:
            meta.append(f"보도일: {date}")
        meta_str = f" ({', '.join(meta)})" if meta else ""

        lines.append(f"{idx}. **{title}**{meta_str}")
        if desc:
            lines.append(f"   - 핵심 내용: {desc}")

    lines.extend([
        "\n※ [🚨 기사 저작권 보호 및 안전한 블로그 작성 필수 원칙 (엄격 준수)]:",
        "1. **기사 문장 단순 복사/전재(Ctrl+C, Ctrl+V) 절대 금지**: 언론사 기사의 특정 문장이나 단락을 그대로 옮겨 적는 것은 저작권 침해에 해당하므로 절대 불가합니다.",
        "2. **객관적 팩트(Fact) 및 발표 데이터만 인용**: 정책 변경점, 통계 수치, 공급 가구수, 규제 일자 등 '사실' 자체만 인용하세요.",
        "3. **공인중개사의 독창적인 해설/전략 중심(80% 이상)**: 기사 내용 요약은 1~2문장으로 압축하고, 전체 글의 80% 이상은 공인중개사의 전문 시각에서 분석한 '실제 시장 파급 효과', '내 집 마련 및 투자자 행동 요령', '현장 실무 팁' 등 완전히 새로운 독창적 창작물로 서술하세요.",
        "4. **정확한 출처 표기**: 본문 서두에 '최근 연합뉴스 등 언론 보도에 따르면'과 같이 출처를 자연스럽게 명시하여 신뢰도와 적법 인용 요건을 확보하세요."
    ])
    return "\n".join(lines)
