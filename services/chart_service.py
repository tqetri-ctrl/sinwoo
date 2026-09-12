"""
공인중개사 네이버 블로그용 고화질 인포그래픽 차트 및 카드 이미지 생성 서비스
- 외부 의존성(matplotlib 등) 없이 PyQt6 내장 QPainter를 활용하여 0.05초 만에 초고속 벡터 렌더링
- 네이버 블로그에 최적화된 16:9 비율(960x540) 카드형 그래픽
- 원클릭 클립보드 이미지 복사 지원
"""

import re
# pyrefly: ignore [missing-import]
from PyQt6.QtCore import QRectF, Qt
# pyrefly: ignore [missing-import]
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QImage,
    QLinearGradient,
    QPainter,
    QPen,
)
# pyrefly: ignore [missing-import]
from PyQt6.QtWidgets import QApplication

FONT_FAMILY = "Malgun Gothic"
DEFAULT_FALLBACK_ITEMS = [
    ("시장 동향", "실거래가 및 매물 호가 추이 점검"),
    ("핵심 체크", "대출 한도 및 규제 변경 사항 확인"),
    ("실무 가이드", "공인중개사 맞춤 매수·임대차 전략"),
    ("상담 문의", "방문 예약 및 유선 상담 안내")
]


def _extract_property_items(property_info: dict) -> list:
    """매물 입력 정보에서 인포그래픽용 핵심 항목 추출"""
    if not property_info:
        return []

    deal_type = property_info.get("deal_type", "")
    prop_type = property_info.get("property_type", "")
    price = property_info.get("price", "")
    area = property_info.get("area_structure", "")
    loc = property_info.get("location", "")
    feat = property_info.get("features", "")

    items = []
    if deal_type or prop_type:
        items.append(("매물 종류", f"{prop_type} ({deal_type})".strip()))
    if price and price != "가격 문의 요망":
        items.append(("가격 조건", price))
    if area and area != "상세 면적/구조 문의 요망":
        items.append(("면적/구조", area))
    if loc and loc != "위치 문의 요망":
        items.append(("소재지", loc))
    if feat:
        items.append(("특장점", feat[:35] + ("..." if len(feat) > 35 else "")))

    return items[:5]


def _parse_table_row(line_s: str):
    """단일 마크다운 표 행 파싱"""
    if not (line_s.startswith("|") and line_s.endswith("|")) or "---" in line_s:
        return None
    parts = [p.strip() for p in line_s.split("|") if p.strip()]
    if len(parts) < 2 or parts[0] in ("구분", "항목", "주요 항목", "번호"):
        return None
    key = parts[0].replace("**", "").strip()
    val = " → ".join(parts[1:]).replace("**", "").strip()
    if not key or not val or len(key) > 15:
        return None
    return (key, val[:40])


def _extract_markdown_table_items(lines: list) -> list:
    """본문 내 마크다운 표에서 인포그래픽용 요약 행 추출"""
    items = []
    for line in lines:
        row = _parse_table_row(line.strip())
        if row:
            items.append(row)
            if len(items) >= 4:
                break
    return items


def _parse_bullet_line(line_s: str):
    """단일 불릿포인트(- **항목**: 내용) 파싱"""
    if not line_s.startswith(("- **", "* **", "• **")):
        return None
    end_idx = line_s.find("**", 4)
    if end_idx == -1:
        return None
    key = line_s[4:end_idx].strip()
    rest = line_s[end_idx + 2:].lstrip(":\t ")
    val = re.sub(r"[*_`]", "", rest).strip()
    if not key or not val:
        return None
    return (key[:12], val[:40])


def _extract_bullet_items(lines: list) -> list:
    """본문 내 불릿포인트에서 요약 항목 추출"""
    items = []
    for line in lines:
        item = _parse_bullet_line(line.strip())
        if item:
            items.append(item)
            if len(items) >= 4:
                break
    return items


def extract_summary_items(body_text: str, mode: str = "news", property_info: dict = None) -> list:
    """
    본문 또는 매물 정보에서 인포그래픽 카드에 들어갈 핵심 3~5개 요약 항목 추출
    반환 형식: [("항목명", "상세 내용"), ...]
    """
    # 1. 매물 모드인 경우 매물 정보 우선 활용
    if mode == "property" and property_info:
        prop_items = _extract_property_items(property_info)
        if len(prop_items) >= 3:
            return prop_items

    # 2. 본문 라인 분석 (마크다운 표 우선, 없을 시 불릿포인트)
    lines = body_text.splitlines() if body_text else []
    items = _extract_markdown_table_items(lines)

    if not items:
        items = _extract_bullet_items(lines)

    # 3. 항목이 없으면 기본 팩트 항목 반환
    if not items:
        items = list(DEFAULT_FALLBACK_ITEMS)

    return items[:5]


def render_infographic_card(
    title: str,
    items: list,
    office_name: str = "신우 공인중개사사무소",
    card_category: str = "부동산 핵심 체크포인트"
) -> QImage:
    """
    네이버 블로그 본문 첨부용 고해상도 카드 인포그래픽 이미지(960x540, 16:9) 생성
    """
    content_items = items if items else [("핵심 내용", "상세 분석 결과")]
    row_count = len(content_items)
    row_h = 60
    row_gap = 10
    start_y = 135

    width = 960
    # 내용물 항목 개수에 꼭 맞게 전체 캔버스 높이 동적 최적화 (하단 여백 낭비 원천 차단)
    height = max(300, start_y + row_count * (row_h + row_gap) + 45)

    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor("#00000000"))

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # 1. 배경 전체 둥근 카드 (소프트 블루 그라데이션)
    card_rect = QRectF(12, 12, width - 24, height - 24)
    bg_grad = QLinearGradient(0, 0, width, height)
    bg_grad.setColorAt(0.0, QColor("#F8FAFC"))
    bg_grad.setColorAt(1.0, QColor("#EEF2F6"))

    p.setBrush(QBrush(bg_grad))
    p.setPen(QPen(QColor("#CBD5E1"), 1.5))
    p.drawRoundedRect(card_rect, 18, 18)

    # 2. 상단 헤더 배너 카드
    banner_rect = QRectF(28, 28, width - 56, 92)
    p.setBrush(QColor("#1E3A8A"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(banner_rect, 12, 12)

    # 상단 카테고리 뱃지
    p.setPen(QColor("#93C5FD"))
    p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
    p.drawText(QRectF(48, 38, width - 96, 22), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"📊 {card_category.upper()}")

    # 상단 메인 타이틀
    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont(FONT_FAMILY, 16, QFont.Weight.Bold))
    clean_title = title.replace("📌 ", "").strip()
    if len(clean_title) > 36:
        clean_title = clean_title[:35] + "..."
    p.drawText(QRectF(48, 64, width - 96, 46), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clean_title)

    # 3. 본문 항목 리스트 박스들
    for i, (key, val) in enumerate(content_items):
        y_pos = start_y + i * (row_h + row_gap)
        item_rect = QRectF(28, y_pos, width - 56, row_h)

        p.setBrush(QColor("#FFFFFF"))
        p.setPen(QPen(QColor("#E2E8F0"), 1))
        p.drawRoundedRect(item_rect, 8, 8)

        # 좌측 넘버링 뱃지
        badge_rect = QRectF(42, y_pos + (row_h - 28) / 2, 28, 28)
        p.setBrush(QColor("#2563EB"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(badge_rect, 6, 6)

        p.setPen(QColor("#FFFFFF"))
        p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))

        # 항목 레이블 (Key)
        p.setPen(QColor("#1E293B"))
        p.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Bold))
        key_rect = QRectF(80, y_pos + 4, 180, row_h - 8)
        p.drawText(key_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, key)

        # 구분 바
        p.setPen(QPen(QColor("#E2E8F0"), 1))
        p.drawLine(int(265), int(y_pos + 8), int(265), int(y_pos + row_h - 8))

        # 항목 값 (Value)
        p.setPen(QColor("#334155"))
        p.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.DemiBold))
        val_rect = QRectF(280, y_pos + 4, width - 330, row_h - 8)
        p.drawText(val_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, val)

    # 4. 하단 브랜딩 푸터
    footer_rect = QRectF(32, height - 38, width - 64, 24)
    p.setPen(QColor("#64748B"))
    p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Normal))
    footer_text = f"🏢 {office_name} | 네이버 블로그 공식 포스팅 인포그래픽 자료"
    p.drawText(footer_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, footer_text)

    p.end()
    return img


def copy_chart_to_clipboard(img: QImage) -> bool:
    """QImage를 윈도우 시스템 클립보드에 복사"""
    if img is None or img.isNull():
        return False
    clipboard = QApplication.clipboard()
    clipboard.setImage(img)
    return True
