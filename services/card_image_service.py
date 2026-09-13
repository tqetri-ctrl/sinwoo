"""
카드뉴스 슬라이드 이미지 생성 및 일괄 내보내기 서비스 (services/card_image_service.py)
- 슬라이드별 1:1 고해상도(720x720) 카드뉴스 PNG 렌더링
- 네이버 블로그 포토 앨범, 스마트에디터 사진 첨부 및 인스타그램 카드뉴스 완벽 규격
- 번호순(card_01.png, card_02.png...) 일괄 저장 지원
"""

import os
import re
# pyrefly: ignore [missing-import]
from PyQt6.QtCore import QPointF, QRectF, Qt
# pyrefly: ignore [missing-import]
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QImage,
    QLinearGradient,
    QPainter,
    QPen,
)
from services.text_utils import deduplicate_consecutive_emojis, strip_leading_emojis
from ui.styles import _split_into_cards

FONT_FAMILY = "Malgun Gothic"


def _draw_card_header(p: QPainter, badge: str, office_name: str, width: int):
    """카드 상단 뱃지 및 사무소 브랜딩 렌더링"""
    # 뱃지 배경 캡슐
    badge_clean = deduplicate_consecutive_emojis(badge).strip()
    is_cover = "01" in badge or "INTRO" in badge or "표지" in badge
    badge_bg = QColor("#1E3A8A") if is_cover else QColor("#03C75A")

    p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
    fm = QFontMetrics(p.font())
    badge_w = fm.horizontalAdvance(badge_clean) + 26
    badge_h = 30
    badge_rect = QRectF(40, 40, badge_w, badge_h)

    p.setBrush(QBrush(badge_bg))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(badge_rect, 15, 15)

    p.setPen(QColor("#FFFFFF"))
    p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_clean)

    # 우측 상단 사무소 상호
    if office_name:
        clean_office = strip_leading_emojis(office_name).strip()
        p.setPen(QColor("#64748B"))
        p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        p.drawText(QRectF(width - 320, 40, 280, badge_h), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"🏢 {clean_office}")

    # 상단 구분선
    p.setPen(QPen(QColor("#E2E8F0"), 1))
    p.drawLine(40, 84, width - 40, 84)


def _draw_card_footer(p: QPainter, slide_idx: int, total_slides: int, office_name: str, office_phone: str, width: int, height: int):
    """카드 하단 푸터 및 슬라이드 번호 렌더링"""
    footer_y = height - 60
    p.setPen(QPen(QColor("#E2E8F0"), 1))
    p.drawLine(40, footer_y - 12, width - 40, footer_y - 12)

    # 좌측 사무소 연락처
    clean_office = strip_leading_emojis(office_name).strip() or "신우 공인중개사사무소"
    contact_str = f"{clean_office} | ☎ {office_phone}" if office_phone else f"{clean_office} | 친절한 부동산 가이드"
    p.setPen(QColor("#64748B"))
    p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Normal))
    p.drawText(QRectF(40, footer_y, 400, 30), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, contact_str)

    # 우측 슬라이드 번호 뱃지 (예: 1 / 6)
    page_str = f"{slide_idx} / {total_slides}"
    page_rect = QRectF(width - 120, footer_y, 80, 26)
    p.setBrush(QColor("#F1F5F9"))
    p.setPen(QPen(QColor("#CBD5E1"), 1))
    p.drawRoundedRect(page_rect, 13, 13)

    p.setPen(QColor("#475569"))
    p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
    p.drawText(page_rect, Qt.AlignmentFlag.AlignCenter, page_str)


def _draw_card_title(p: QPainter, title: str, width: int, y: int = 100) -> int:
    """카드 소제목 렌더링 (헤드라인)"""
    clean_title = deduplicate_consecutive_emojis(title).strip()
    if not clean_title:
        return y

    p.setPen(QColor("#0F172A"))
    p.setFont(QFont(FONT_FAMILY, 19, QFont.Weight.Bold))
    rect = QRectF(40, y, width - 80, 48)
    p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clean_title)
    return y + 54


def _draw_card_visual(p: QPainter, img: QImage, width: int, y: int) -> int:
    """차트 또는 지도 이미지 임베드 렌더링"""
    if img is None or img.isNull():
        return y

    max_w = width - 80
    max_h = 240
    scaled = img.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    ix = int((width - scaled.width()) / 2)
    iy = int(y + 6)
    p.drawImage(ix, iy, scaled)
    return iy + scaled.height() + 16


def _draw_card_bullets(p: QPainter, lines: list, width: int, start_y: int):
    """본문 불릿 포인트 및 텍스트 렌더링"""
    curr_y = start_y
    colors = [
        ("#2563EB", "#EFF6FF", "#BFDBFE"),
        ("#059669", "#ECFDF5", "#A7F3D0"),
        ("#D97706", "#FFFBEB", "#FDE68A"),
        ("#7C3AED", "#F5F3FF", "#DDD6FE"),
    ]

    for idx, raw_line in enumerate(lines):
        line = deduplicate_consecutive_emojis(raw_line).strip()
        if not line:
            curr_y += 10
            continue

        if curr_y > 580:
            break

        # 불릿 항목 체크
        is_bullet = bool(re.match(r'^[-*•\d\.]+\s*', line))
        content = re.sub(r'^[-*•\d\.]+\s*', '', line).strip()
        content = content.replace("**", "").replace("__", "")

        c_idx = idx % len(colors)
        t_col, bg_col, brd_col = colors[c_idx]

        if is_bullet:
            box_rect = QRectF(40, curr_y, width - 80, 52)
            p.setBrush(QColor(bg_col))
            p.setPen(QPen(QColor(brd_col), 1))
            p.drawRoundedRect(box_rect, 8, 8)

            # 불릿 인덱스 점/뱃지
            badge_rect = QRectF(52, curr_y + 12, 28, 28)
            p.setBrush(QColor(t_col))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(badge_rect, 6, 6)

            p.setPen(QColor("#FFFFFF"))
            p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
            p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"{idx + 1}")

            # 텍스트 내용
            p.setPen(QColor("#1E293B"))
            p.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
            text_rect = QRectF(90, curr_y + 10, width - 142, 34)
            p.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap, content)
            curr_y += 62
        else:
            # 일반 텍스트 문단
            p.setPen(QColor("#334155"))
            p.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Medium))
            text_rect = QRectF(44, curr_y, width - 88, 44)
            p.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, content)
            curr_y += 50


def render_single_card_image(
    card: dict,
    slide_idx: int,
    total_slides: int,
    office_name: str = "",
    office_phone: str = "",
    chart_img: QImage = None,
    zone_map_img: QImage = None
) -> QImage:
    """개별 카드뉴스 슬라이드 720x720 고화질 이미지 렌더링"""
    width = 720
    height = 720

    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor("#F8FAFC"))

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # 1. 메인 카드 프레임 (모던 라운드 컨테이너)
    card_rect = QRectF(16, 16, width - 32, height - 32)
    p.setBrush(QColor("#FFFFFF"))
    p.setPen(QPen(QColor("#E2E8F0"), 1.5))
    p.drawRoundedRect(card_rect, 16, 16)

    # 2. 상단 헤더
    badge = card.get("badge", f"CARD {slide_idx:02d}")
    _draw_card_header(p, badge, office_name, width)

    # 3. 슬라이드 타이틀
    title = card.get("title", "")
    content = card.get("content", "")
    content_lines = [ln.strip() for ln in content.splitlines() if ln.strip()]

    # 만약 title이 비어있다면 본문의 첫 번째 마크다운 헤딩(### ...)에서 추출
    if not title and content_lines and content_lines[0].startswith("###"):
        title = re.sub(r'^###\s*', '', content_lines.pop(0)).strip()

    next_y = _draw_card_title(p, title or f"핵심 체크포인트 #{slide_idx}", width, y=100)

    # 4. 시각 자료(차트/지도) 임베드 여부 확인
    has_chart_placeholder = any("추천 자료" in ln or "차트" in ln for ln in content_lines)
    has_map_placeholder = any("위치도" in ln or "지도" in ln for ln in content_lines)

    target_visual = None
    if has_chart_placeholder and chart_img and not chart_img.isNull():
        target_visual = chart_img
    elif has_map_placeholder and zone_map_img and not zone_map_img.isNull():
        target_visual = zone_map_img

    if target_visual:
        next_y = _draw_card_visual(p, target_visual, width, next_y)
        # 플레이스홀더 라인 제외
        content_lines = [ln for ln in content_lines if not (ln.startswith("[") and ln.endswith("]"))]

    # 5. 본문 불릿/텍스트
    _draw_card_bullets(p, content_lines, width, next_y + 10)

    # 6. 하단 푸터 및 슬라이드 번호
    _draw_card_footer(p, slide_idx, total_slides, office_name, office_phone, width, height)

    p.end()
    return img


def export_card_news_images(
    body_markdown: str,
    output_dir: str,
    office_name: str = "",
    office_phone: str = "",
    chart_img: QImage = None,
    zone_map_img: QImage = None
) -> list[str]:
    """본문 마크다운에서 슬라이드를 추출하여 card_01.png, card_02.png... 로 일괄 저장"""
    cards = _split_into_cards(body_markdown)
    if not cards:
        # 카드 구조가 아닌 경우 헤딩(###) 단위로 분할 fallback
        pattern = re.compile(r'(?m)^(?=###\s+)')
        parts = [p.strip() for p in pattern.split(body_markdown) if p.strip()]
        cards = []
        for i, pt in enumerate(parts):
            lines = pt.splitlines()
            title = re.sub(r'^###\s*', '', lines[0]).strip() if lines else f"핵심 포인트 {i+1}"
            cards.append({
                "badge": f"CARD {i+1:02d} | 요약",
                "title": title,
                "content": "\n".join(lines[1:]).strip() if len(lines) > 1 else lines[0]
            })

    if not cards:
        return []

    os.makedirs(output_dir, exist_ok=True)
    saved_files = []
    total = len(cards)

    for idx, card in enumerate(cards):
        slide_num = idx + 1
        img = render_single_card_image(
            card=card,
            slide_idx=slide_num,
            total_slides=total,
            office_name=office_name,
            office_phone=office_phone,
            chart_img=chart_img,
            zone_map_img=zone_map_img
        )
        out_path = os.path.join(output_dir, f"card_{slide_num:02d}.png")
        img.save(out_path, "PNG")
        saved_files.append(out_path)

    return saved_files
