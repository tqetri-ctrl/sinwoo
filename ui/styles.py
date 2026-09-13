"""
단정하고 깔끔한 (Clean & Neat) 모던 데스크톱 GUI 스타일시트 및 HTML 미리보기 템플릿
"""

import re
import markdown
from services.text_utils import strip_leading_emojis, deduplicate_consecutive_emojis

MAIN_STYLESHEET = """
/* 전체 기본 설정 */
QWidget {
    font-family: 'Pretendard', 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 15px;
    color: #2D3748;
    background-color: #F8FAFC;
}

/* 카드 컨테이너 */
QFrame#CardFrame {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 8px 10px;
}

QFrame#HeaderCard {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 4px 16px;
    max-height: 50px;
}

/* 라벨 스타일 */
QLabel {
    background-color: transparent;
}

QLabel#StepBadge {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 13px;
    border-radius: 10px;
    padding: 2px 8px;
}

QLabel#StepTitle {
    font-size: 16px;
    font-weight: bold;
    color: #1E293B;
}

QLabel#AppTitle {
    font-size: 18px;
    font-weight: bold;
    color: #0F172A;
}

QLabel#AppSubtitle {
    font-size: 14px;
    color: #64748B;
}

/* 스크롤 영역 및 스크롤바 */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #F1F5F9;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* 탭 위젯 */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background-color: #FFFFFF;
    top: -1px;
}

QTabBar::tab {
    background-color: #F1F5F9;
    color: #64748B;
    padding: 6px 14px;
    border: 1px solid #E2E8F0;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-weight: bold;
    font-size: 14px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #2563EB;
    border-bottom: 1px solid #FFFFFF;
}

QTabBar::tab:hover:!selected {
    background-color: #E2E8F0;
    color: #334155;
}

/* 텍스트 입력창 */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 15px;
    color: #1E293B;
    selection-background-color: #93C5FD;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1.5px solid #2563EB;
    background-color: #FFFFFF;
}

/* 콤보박스 */
QComboBox {
    background-color: #FFFFFF;
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 14px;
    color: #1E293B;
}

QComboBox:focus {
    border: 1.5px solid #2563EB;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}

/* 버튼 스타일 */
QPushButton {
    background-color: #FFFFFF;
    color: #334155;
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #F8FAFC;
    border-color: #94A3B8;
    color: #0F172A;
}

QPushButton:pressed {
    background-color: #F1F5F9;
}

/* 메인 생성 버튼 (큼직하고 돋보이는 블루) */
QPushButton#GenerateButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 9px;
    padding: 11px 20px;
    font-size: 17px;
    font-weight: bold;
}

QPushButton#GenerateButton:hover {
    background-color: #1D4ED8;
}

QPushButton#GenerateButton:pressed {
    background-color: #1E40AF;
}

QPushButton#GenerateButton:disabled {
    background-color: #94A3B8;
    color: #F1F5F9;
}

/* 네이버 블로그 복사 버튼 (네이버 대표 그린 포인트) */
QPushButton#NaverCopyButton {
    background-color: #03C75A;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 16px;
    font-weight: bold;
}

QPushButton#NaverCopyButton:hover {
    background-color: #02B350;
}

QPushButton#NaverCopyButton:pressed {
    background-color: #029E47;
}

/* 차트 이미지 복사 버튼 (로열 블루 포인트) */
QPushButton#ChartCopyButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 15px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#ChartCopyButton:hover {
    background-color: #1D4ED8;
}

QPushButton#ChartCopyButton:pressed {
    background-color: #1E40AF;
}

/* 정비구역 지도 복사 버튼 (스카이 블루) */
QPushButton#ZoneMapCopyButton {
    background-color: #0284C7;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#ZoneMapCopyButton:hover {
    background-color: #0369A1;
}

QPushButton#ZoneMapCopyButton:pressed {
    background-color: #075985;
}

/* 토지이음 바로가기 버튼 (틸/청록) */
QPushButton#EumOpenButton {
    background-color: #0D9488;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 13px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#EumOpenButton:hover {
    background-color: #0F766E;
}

QPushButton#EumOpenButton:pressed {
    background-color: #115E59;
}

/* 라디오 버튼 (카드형 톤앤매너 선택용) */
QRadioButton {
    font-size: 15px;
    font-weight: 500;
    color: #334155;
    spacing: 8px;
    padding: 6px;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #94A3B8;
    background-color: #FFFFFF;
}

QRadioButton::indicator:checked {
    border: 2px solid #2563EB;
    background-color: #2563EB;
}

/* 스크롤바 */
QScrollBar:vertical {
    border: none;
    background: #F1F5F9;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
/* 사진 목록 리스트 및 칩 */
QListWidget#PhotoList {
    background-color: #F8FAFC;
    border: 1.5px dashed #CBD5E1;
    border-radius: 8px;
    padding: 6px;
    font-size: 14px;
}

QListWidget#PhotoList::item {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 6px 10px;
    margin-bottom: 4px;
    color: #1E293B;
}

QListWidget#PhotoList::item:hover {
    background-color: #EFF6FF;
    border-color: #93C5FD;
}

QListWidget#PhotoList::item:selected {
    background-color: #DBEAFE;
    color: #1E40AF;
    font-weight: bold;
}
"""

_PLACEHOLDER_RULES = [
    (("추천 스티커:", "추천스티커:", "스티커:"), "sticker-box", "✨", "[네이버 스티커]"),
    (("추천 자료:", "추천자료:", "추천 표:", "추천표:", "추천 차트:", "추천차트:", "자료:", "추천 그래프:", "추천그래프:"), "data-box", "📊", "[자료/그래프]"),
    (("네이버 지도", "지도 첨부", "추천 지도", "지도:", "네이버지도", "구역 지도", "구역지도", "정비구역 지도", "정비구역", "위치도", "매물 위치도", "토지이음"), "map-box", "🗺️", "[지도/위치도 첨부]"),
    (("추천 배너:", "추천배너:", "명함 배너:", "상담 배너:"), "banner-box", "📞", "[사무소 명함/상담 배너]"),
]


def _render_chart_embed(val: str = "") -> str:
    """인포그래픽 요약 카드 임베드 HTML 렌더링 (테이블 레이아웃으로 상하 여백 100% 제거)"""
    clean_val = strip_leading_emojis(val).strip()
    clean_val = re.sub(r'^(?:추천\s*(?:자료|표|차트|그래프)|자료)\s*[:：]\s*', '', clean_val).strip().strip("[] ")
    clean_val = strip_leading_emojis(clean_val).strip()
    desc = f" - {clean_val}" if clean_val else ""
    return (
        '<table class="embed-card-table" cellspacing="0" cellpadding="0" style="width: 100%; margin: 14px 0; background-color: #F8FAFC; border: 1.5px solid #BFDBFE; border-radius: 12px; border-collapse: separate;">'
        '<tr><td style="padding: 10px 14px 8px 14px; border: none; font-size: 13px; font-weight: bold; color: #1D4ED8; background-color: transparent;">'
        f'📊 <strong>[핵심 요약 인포그래픽 카드]</strong>{desc}'
        '</td></tr>'
        '<tr><td align="center" style="padding: 0 8px 12px 8px; border: none; background-color: transparent;">'
        '<img src="chart_preview.png" width="620" height="400" style="border-radius: 8px; border: 1px solid #CBD5E1;">'
        '</td></tr>'
        '</table>'
    )


def _render_map_embed(val: str = "") -> str:
    """정비구역/매물 위치도 임베드 HTML 렌더링 (테이블 레이아웃으로 상하 여백 100% 제거)"""
    clean_val = strip_leading_emojis(val).strip()
    clean_val = re.sub(r'^(?:정비구역\s*(?:/\s*매물\s*)?위치도|매물\s*위치도|위치도)\s*[:：]\s*', '', clean_val).strip().strip("[] ")
    clean_val = strip_leading_emojis(clean_val).strip()
    desc = f" - {clean_val}" if clean_val else ""
    return (
        '<table class="embed-card-table" cellspacing="0" cellpadding="0" style="width: 100%; margin: 14px 0; background-color: #F0F9FF; border: 1.5px solid #BAE6FD; border-radius: 12px; border-collapse: separate;">'
        '<tr><td style="padding: 10px 14px 8px 14px; border: none; font-size: 13px; font-weight: bold; color: #0284C7; background-color: transparent;">'
        f'🗺️ <strong>[정비구역 / 매물 위치도]</strong>{desc}'
        '</td></tr>'
        '<tr><td align="center" style="padding: 0 8px 12px 8px; border: none; background-color: transparent;">'
        '<img src="zone_map_preview.png" width="620" height="400" style="border-radius: 8px; border: 1px solid #CBD5E1;">'
        '</td></tr>'
        '</table>'
    )


def _render_photo_placeholder(cleaned: str) -> str:
    """사진 계열 플레이스홀더 렌더링 (중복 이모지 자동 정제)"""
    if not re.match(r'^(사진\s*\d+|현장\s*사진|추천\s*사진|실제\s*사진|공간\s*사진)\s*:', cleaned):
        return ""
    parts = cleaned.split(":", 1)
    prefix = strip_leading_emojis(parts[0]).strip()
    val = strip_leading_emojis(parts[1]).strip().strip("[] ") if len(parts) > 1 else ""
    val = strip_leading_emojis(val).strip()
    return f'<div class="placeholder-box photo-box"><span class="icon">📸</span><strong>[{prefix}]</strong> {val}</div>'


def _render_rule_box(box_cls: str, icon: str, label: str, val: str, has_chart: bool, has_zone_map: bool, state: dict = None) -> str:
    """규칙 기반 박스 또는 시각적 임베드 렌더링 (중복 임베드 및 중복 이모지 자동 방지)"""
    st = state if state is not None else {}
    if box_cls == "data-box" and has_chart and not st.get("chart_done", False):
        st["chart_done"] = True
        return _render_chart_embed(val)
    if box_cls == "map-box" and has_zone_map and not st.get("map_done", False):
        st["map_done"] = True
        return _render_map_embed(val)
    if box_cls == "map-box" and (st.get("map_done", False) or not has_zone_map):
        # 이미 지도가 위에서 임베드되었거나 지도가 없는 경우 중복 지도 박스 생략
        return ""
    clean_val = strip_leading_emojis(val).strip().strip("[] ")
    clean_val = strip_leading_emojis(clean_val).strip()
    return f'<div class="placeholder-box {box_cls}"><span class="icon">{icon}</span><strong>{label}</strong> {clean_val}</div>'


def _render_placeholder_box(match, has_chart: bool = False, has_zone_map: bool = False, state: dict = None) -> str:
    """플레이스홀더 텍스트를 시각적 요소 카드 또는 실제 이미지 임베드로 변환"""
    raw = match.group(1).strip()
    cleaned = re.sub(r'^[^0-9a-zA-Z가-힣]+', '', raw).strip()

    photo_box = _render_photo_placeholder(cleaned)
    if photo_box:
        return photo_box

    for prefixes, box_cls, icon, label in _PLACEHOLDER_RULES:
        if cleaned.startswith(prefixes):
            val = cleaned.split(":", 1)[1].strip() if ":" in cleaned else cleaned
            return _render_rule_box(box_cls, icon, label, val, has_chart, has_zone_map, state)

    return match.group(0)


def is_card_news_text(text: str) -> bool:
    """텍스트가 슬라이드형 카드뉴스([카드 01], [Card 01] 등) 구조인지 감지"""
    if not text:
        return False
    return bool(re.search(r'(?:###\s*)?\[(?:카드|Card)\s*\d+', text, re.IGNORECASE))


def _split_into_cards(text: str) -> list:
    """본문 마크다운을 카드 블록 목록으로 분할"""
    pattern = re.compile(r'(?m)^\s*(?:###\s*)?\[((?:카드|Card)\s*\d+)(?:\s*[\|\:–-]([^\]\n]+))?\]', re.IGNORECASE)
    matches = list(pattern.finditer(text))
    if not matches:
        return []

    cards = []
    preamble = text[:matches[0].start()].strip()
    if preamble:
        cards.append({
            "badge": "INTRO",
            "title": "안내",
            "content": deduplicate_consecutive_emojis(preamble)
        })

    for i, m in enumerate(matches):
        raw_label = m.group(1).strip()
        subtitle = deduplicate_consecutive_emojis((m.group(2) or "").strip())
        digits = re.findall(r'\d+', raw_label)
        card_num = f"{int(digits[0]):02d}" if digits else "01"
        badge = f"CARD {card_num}"
        if subtitle:
            badge += f" | {subtitle}"

        start_idx = m.end()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = deduplicate_consecutive_emojis(text[start_idx:end_idx].strip())
        cards.append({
            "badge": badge,
            "title": subtitle,
            "content": content
        })

    return cards


def render_card_news_blocks(
    body_markdown: str,
    has_chart: bool = False,
    has_zone_map: bool = False,
    embed_state: dict = None,
    for_clipboard: bool = False
) -> str:
    """카드뉴스 블록을 HTML 카드 프레임으로 렌더링 (미리보기 및 클립보드 공용)"""
    st = embed_state if embed_state is not None else {"chart_done": False, "map_done": False}
    cards = _split_into_cards(body_markdown)
    if not cards:
        return ""

    card_html_list = []
    for card in cards:
        c_md = card["content"]
        c_html = markdown.markdown(c_md, extensions=['extra', 'nl2br', 'tables'])
        c_html = re.sub(
            r'\[([^\]\r\n]+)\]',
            lambda m: _render_placeholder_box(m, has_chart, has_zone_map, st),
            c_html
        )
        c_html = re.sub(
            r'<p>\s*(<table class="embed-card-table"[^>]*>.*?</table>)\s*</p>',
            r'\1',
            c_html,
            flags=re.DOTALL
        )

        if for_clipboard:
            # 네이버 블로그 스마트에디터 ONE 친화적 인라인 스타일 박스
            c_html = c_html.replace('<table>', '<table style="width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 13.5px; background-color: #FFFFFF; border: 1px solid #CBD5E1;">')
            c_html = c_html.replace('<th>', '<th style="background-color: #F1F5F9; color: #1E293B; font-weight: bold; padding: 8px 12px; border: 1px solid #CBD5E1; text-align: center;">')
            c_html = c_html.replace('<td>', '<td style="padding: 8px 12px; border: 1px solid #CBD5E1; color: #334155;">')
            c_html = c_html.replace('<h1>', '<h2 style="font-size: 18px; font-weight: bold; color: #0F172A; margin: 6px 0 10px 0;">')
            c_html = c_html.replace('</h1>', '</h2>')
            c_html = c_html.replace('<h3>', '<h3 style="font-size: 16px; font-weight: bold; color: #1E293B; border-left: 3px solid #03C75A; padding-left: 8px; margin: 10px 0 8px 0;">')

            card_box = (
                '<div style="background-color: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 12px; '
                'padding: 18px 20px; margin: 20px 0; font-family: \'Malgun Gothic\', \'맑은 고딕\', sans-serif;">'
                f'<div style="display: inline-block; background-color: #03C75A; color: #FFFFFF; font-size: 12px; font-weight: bold; padding: 4px 12px; border-radius: 20px; margin-bottom: 12px;">{card["badge"]}</div>'
                f'<div style="color: #1E293B; font-size: 14.5px; line-height: 1.8;">{c_html}</div>'
                '</div>'
            )
        else:
            card_box = (
                '<div class="card-news-frame">'
                f'<div class="card-news-badge">{card["badge"]}</div>'
                f'<div class="card-news-body">{c_html}</div>'
                '</div>'
            )
        card_html_list.append(card_box)

    return "\n".join(card_html_list)


def _render_card_news_preview(
    body_markdown: str,
    has_chart: bool,
    has_zone_map: bool,
    embed_state: dict
) -> str:
    """카드뉴스 미리보기 HTML 변환 및 미배치 임베드 보강"""
    html_body = render_card_news_blocks(body_markdown, has_chart, has_zone_map, embed_state, for_clipboard=False)
    if has_chart and not embed_state.get("chart_done", False):
        chart_html = _render_chart_embed("본문 핵심 데이터 요약")
        html_body = f"{html_body}\n{chart_html}"
    if has_zone_map and not embed_state.get("map_done", False):
        map_html = _render_map_embed("현장 및 주변 정비구역 위치도")
        html_body = f"{html_body}\n{map_html}"
    return html_body


def _render_standard_blog_body(
    body_markdown: str,
    has_chart: bool,
    has_zone_map: bool,
    embed_state: dict
) -> str:
    """일반 블로그 마크다운 ➔ HTML 변환 및 플레이스홀더/차트/지도 임베드"""
    html_body = markdown.markdown(body_markdown, extensions=['extra', 'nl2br', 'tables'])
    html_body = re.sub(
        r'\[([^\]\r\n]+)\]',
        lambda m: _render_placeholder_box(m, has_chart, has_zone_map, embed_state),
        html_body
    )
    html_body = re.sub(
        r'<p>\s*(<table class="embed-card-table"[^>]*>.*?</table>)\s*</p>',
        r'\1',
        html_body,
        flags=re.DOTALL
    )

    if has_chart and "chart_preview.png" not in html_body:
        chart_html = _render_chart_embed("본문 핵심 데이터 요약")
        if "</table>" in html_body:
            parts = html_body.split("</table>", 1)
            html_body = f"{parts[0]}</table>{chart_html}{parts[1]}"
        else:
            html_body = f"{chart_html}{html_body}"

    if has_zone_map and "zone_map_preview.png" not in html_body:
        map_html = _render_map_embed("현장 및 주변 정비구역 위치도")
        html_body = f"{html_body}{map_html}"

    return html_body


def generate_blog_preview_html(
    title: str,
    body_markdown: str,
    tags: list,
    has_chart: bool = False,
    has_zone_map: bool = False
) -> str:
    """
    네이버 블로그 스마트에디터 ONE과 흡사한 단정하고 깔끔한 HTML 미리보기 렌더링 생성
    (실제 생성된 인포그래픽 차트 및 구역 지도 이미지 인라인 임베드 지원)
    """
    embed_state = {"chart_done": False, "map_done": False}

    if is_card_news_text(body_markdown):
        html_body = _render_card_news_preview(body_markdown, has_chart, has_zone_map, embed_state)
    else:
        html_body = _render_standard_blog_body(body_markdown, has_chart, has_zone_map, embed_state)

    tag_html = " ".join([f'<span class="tag-badge">{t}</span>' for t in tags])

    full_html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Malgun Gothic", "맑은 고딕", "NanumSquare", sans-serif;
            background-color: #FFFFFF;
            color: #222222;
            padding: 24px 20px;
            margin: 0;
            font-size: 15px;
            letter-spacing: -0.3px;
        }}
        .blog-container {{
            max-width: 680px;
            margin: 0 auto;
        }}
        .blog-header {{
            border-bottom: 2px solid #03C75A;
            padding-bottom: 18px;
            margin-bottom: 24px;
        }}
        .blog-category {{
            font-size: 13px;
            font-weight: 700;
            color: #03C75A;
            margin-bottom: 6px;
            text-transform: uppercase;
        }}
        .blog-title {{
            font-size: 24px;
            font-weight: 800;
            color: #111111;
            line-height: 1.4;
            margin: 0;
        }}
        .blog-content {{
            font-size: 15px;
            color: #333333;
        }}
        .blog-content p {{
            line-height: 1.85;
            margin-bottom: 20px;
            word-break: keep-all;
        }}
        table.embed-card-table td {{
            border: none !important;
        }}
        .blog-content h1, .blog-content h2, .blog-content h3 {{
            color: #111111;
            margin-top: 32px;
            margin-bottom: 16px;
            font-weight: 700;
            line-height: 1.4;
        }}
        .blog-content h3 {{
            font-size: 18px;
            border-left: 4px solid #03C75A;
            padding-left: 10px;
        }}
        .blog-content strong {{
            color: #111111;
            background: linear-gradient(to top, #DCFCE7 40%, transparent 40%);
            padding: 0 2px;
        }}
        /* 표(Table) 스타일 - 네이버 블로그 스마트에디터풍 */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        th, td {{
            border: 1px solid #E2E8F0;
            padding: 10px 14px;
            text-align: left;
        }}
        th {{
            background-color: #F1F5F9;
            font-weight: bold;
            color: #1E293B;
            width: 25%;
        }}
        td {{
            background-color: #FFFFFF;
            color: #334155;
        }}
        /* 리스트 스타일 */
        ul, ol {{
            padding-left: 24px;
            margin-bottom: 20px;
        }}
        li {{
            margin-bottom: 6px;
        }}
        /* 플레이스홀더 박스 */
        .placeholder-box {{
            margin: 22px 0;
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 13px;
            display: flex;
            align-items: center;
            line-height: 1.5;
        }}
        .placeholder-box .icon {{
            font-size: 18px;
            margin-right: 10px;
        }}
        .sticker-box {{
            background-color: #FEF3C7;
            border: 1px dashed #F59E0B;
            color: #92400E;
        }}
        .photo-box {{
            background-color: #EFF6FF;
            border: 1.5px dashed #3B82F6;
            color: #1E40AF;
        }}
        .data-box {{
            background-color: #F3E8FF;
            border: 1px dashed #A855F7;
            color: #6B21A8;
        }}
        .map-box {{
            background-color: #E0F2FE;
            border: 1.5px dashed #0284C7;
            color: #0369A1;
        }}
        .banner-box {{
            background-color: #ECFDF5;
            border: 1.5px solid #059669;
            color: #065F46;
        }}
        /* 카드뉴스 전용 슬라이드 박스 */
        .card-news-frame {{
            background-color: #F8FAFC;
            border: 1.5px solid #E2E8F0;
            border-radius: 14px;
            padding: 20px 22px;
            margin: 22px 0;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.04);
            transition: all 0.2s ease;
        }}
        .card-news-frame:hover {{
            border-color: #86EFAC;
            box-shadow: 0 6px 16px rgba(3, 199, 90, 0.08);
        }}
        .card-news-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #03C75A, #059669);
            color: #FFFFFF;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.4px;
            padding: 4px 12px;
            border-radius: 20px;
            margin-bottom: 12px;
        }}
        .card-news-body h1 {{
            font-size: 20px;
            font-weight: 800;
            color: #0F172A;
            margin: 4px 0 12px 0;
            line-height: 1.4;
        }}
        .card-news-body h2 {{
            font-size: 18px;
            font-weight: 700;
            color: #0F172A;
            margin: 6px 0 10px 0;
        }}
        .card-news-body h3 {{
            font-size: 16px;
            font-weight: 700;
            color: #1E293B;
            border-left: 3px solid #03C75A;
            padding-left: 8px;
            margin: 10px 0 10px 0;
        }}
        .card-news-body p {{
            font-size: 14.5px;
            line-height: 1.75;
            margin-bottom: 12px;
            color: #334155;
        }}
        .card-news-body ul, .card-news-body ol {{
            margin-bottom: 12px;
            padding-left: 22px;
        }}
        .blog-tags {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #E5E7EB;
        }}
        .tag-badge {{
            display: inline-block;
            background-color: #F3F4F6;
            color: #4B5563;
            font-size: 13px;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 16px;
            margin-right: 6px;
            margin-bottom: 8px;
        }}
    </style>
    </head>
    <body>
    <div class="blog-container">
        <div class="blog-header">
            <div class="blog-category">부동산 소식 & 매물 브리핑</div>
            <h1 class="blog-title">{title}</h1>
        </div>
        <div class="blog-content">
            {html_body}
        </div>
        <div class="blog-tags">
            {tag_html}
        </div>
    </div>
    </body>
    </html>
    """
    return full_html

