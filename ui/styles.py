"""
단정하고 깔끔한 (Clean & Neat) 모던 데스크톱 GUI 스타일시트 및 HTML 미리보기 템플릿
"""

import re
import markdown

MAIN_STYLESHEET = """
/* 전체 기본 설정 */
QWidget {
    font-family: 'Pretendard', 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 13px;
    color: #2D3748;
    background-color: #F8FAFC;
}

/* 카드 컨테이너 */
QFrame#CardFrame {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px;
}

QFrame#HeaderCard {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 12px 20px;
}

/* 라벨 스타일 */
QLabel {
    background-color: transparent;
}

QLabel#StepBadge {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 12px;
    border-radius: 10px;
    padding: 2px 8px;
}

QLabel#StepTitle {
    font-size: 15px;
    font-weight: bold;
    color: #1E293B;
}

QLabel#AppTitle {
    font-size: 18px;
    font-weight: bold;
    color: #0F172A;
}

QLabel#AppSubtitle {
    font-size: 12px;
    color: #64748B;
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
    padding: 10px 18px;
    border: 1px solid #E2E8F0;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-weight: bold;
    font-size: 13px;
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
    padding: 10px;
    font-size: 13px;
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
    padding: 8px 12px;
    font-size: 13px;
    color: #1E293B;
}

QComboBox:focus {
    border: 1.5px solid #2563EB;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: none;
}

/* 버튼 스타일 */
QPushButton {
    background-color: #FFFFFF;
    color: #334155;
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
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
    border-radius: 10px;
    padding: 14px 24px;
    font-size: 16px;
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
    font-size: 14px;
    font-weight: bold;
}

QPushButton#NaverCopyButton:hover {
    background-color: #02B350;
}

QPushButton#NaverCopyButton:pressed {
    background-color: #029E47;
}

/* 라디오 버튼 (카드형 톤앤매너 선택용) */
QRadioButton {
    font-size: 13px;
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
    font-size: 12px;
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

def generate_blog_preview_html(title: str, body_markdown: str, tags: list) -> str:
    """
    네이버 블로그 스마트에디터 ONE과 흡사한 단정하고 깔끔한 HTML 미리보기 렌더링 생성
    """
    # 마크다운 ➔ HTML 변환 (tables 확장 포함)
    html_body = markdown.markdown(body_markdown, extensions=['extra', 'nl2br', 'tables'])
    
    # 플레이스홀더를 예쁜 블로그 요소 카드/배지로 시각화 (O(N) 선형 치환)
    def _replace_placeholder(match):
        raw = match.group(1).strip()
        # 이모지 제거 및 공백 정돈
        cleaned = re.sub(r'^[✨💡📸📊📞]\s*', '', raw).strip()
        
        # 1. 사진 계열 ([📸 사진 1: ...], [📸 현장 사진: ...], [📸 추천 사진: ...] 등)
        if re.match(r'^(사진\s*\d+|현장\s*사진|추천\s*사진|실제\s*사진|공간\s*사진)\s*:', cleaned):
            parts = cleaned.split(":", 1)
            prefix = parts[0].strip()
            val = parts[1].strip() if len(parts) > 1 else ""
            return f'<div class="placeholder-box photo-box"><span class="icon">📸</span><strong>[{prefix}]</strong> {val}</div>'
            
        if cleaned.startswith(("추천 스티커:", "추천스티커:", "스티커:")):
            val = cleaned.split(":", 1)[1].strip()
            return f'<div class="placeholder-box sticker-box"><span class="icon">✨</span><strong>[네이버 스티커]</strong> {val}</div>'
        if cleaned.startswith(("추천 자료:", "추천자료:", "추천 표:", "추천표:", "추천 차트:", "추천차트:", "자료:")):
            val = cleaned.split(":", 1)[1].strip()
            return f'<div class="placeholder-box data-box"><span class="icon">📊</span><strong>[자료/그래프]</strong> {val}</div>'
        if cleaned.startswith(("추천 배너:", "추천배너:", "명함 배너:", "상담 배너:")):
            val = cleaned.split(":", 1)[1].strip()
            return f'<div class="placeholder-box banner-box"><span class="icon">📞</span><strong>[사무소 명함/상담 배너]</strong> {val}</div>'
        
        return match.group(0)

    html_body = re.sub(r'\[([^\]\r\n]+)\]', _replace_placeholder, html_body)

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
            line-height: 1.85;
            padding: 30px 40px;
            margin: 0;
            font-size: 15px;
            letter-spacing: -0.3px;
        }}
        .blog-container {{
            max-width: 720px;
            margin: 0 auto;
        }}
        .blog-header {{
            border-bottom: 2px solid #03C75A;
            padding-bottom: 18px;
            margin-bottom: 30px;
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
            margin-bottom: 20px;
            word-break: keep-all;
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
        .banner-box {{
            background-color: #ECFDF5;
            border: 1.5px solid #059669;
            color: #065F46;
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

