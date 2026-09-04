"""
실시간 부동산 뉴스 및 보도자료 수집 서비스 (하이브리드 지원)
- 1) 무료 오픈 실시간 뉴스 RSS 검색 (Google News RSS, API 키 불필요, 100% 무료)
- 2) 네이버 뉴스 공식 오픈 API (Client ID/Secret 등록 시 네이버 뉴스 우선 수집)
"""

import html
import json
import re
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
        return None

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


def fetch_hybrid_news(query: str, config: dict = None, max_results: int = 5) -> list:
    """
    하이브리드 뉴스 수집 메인 함수:
    1) 네이버 API 키가 있으면 네이버 뉴스 검색 우선 시도
    2) 키가 없거나 실패 시 100% 무료 Google News RSS 실시간 검색 자동 수행
    """
    cfg = config or {}
    naver_id = cfg.get("naver_client_id", "").strip()
    naver_secret = cfg.get("naver_client_secret", "").strip()

    # 1. 네이버 API 키가 설정되어 있으면 네이버 뉴스 검색 우선
    if naver_id and naver_secret:
        naver_results = search_naver_news_api(query, naver_id, naver_secret, max_results=max_results)
        if naver_results:
            return naver_results

    # 2. 키가 없거나 실패 시 완전 무료 오픈 RSS 검색 실행
    return search_google_news_rss(query, max_results=max_results)


def format_news_for_prompt(articles: list) -> str:
    """수집된 뉴스 기사 목록을 Gemini 프롬프트용 텍스트 블록으로 포맷팅"""
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

    lines.append("\n※ 위 최신 팩트를 바탕으로 공인중개사의 신뢰감 있는 시장 해설과 대응 전략을 제시하세요.")
    return "\n".join(lines)
