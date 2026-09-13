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
    QFontMetrics,
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


def _draw_fitted_title(p: QPainter, rect: QRectF, title: str, max_size: int = 13, min_size: int = 9, color: QColor = QColor("#FFFFFF")):
    """인포그래픽 배너 타이틀이 잘리거나 '...'로 생략되지 않도록 가용 너비에 맞춰 폰트 크기 자동 조절"""
    p.setPen(color)
    clean_title = title.replace("📌 ", "").strip()
    fitted_font = None
    for size in range(max_size, min_size - 1, -1):
        font = QFont(FONT_FAMILY, size, QFont.Weight.Bold)
        fm = QFontMetrics(font)
        if fm.horizontalAdvance(clean_title) <= rect.width():
            fitted_font = font
            break

    if fitted_font:
        p.setFont(fitted_font)
        p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clean_title)
    else:
        font = QFont(FONT_FAMILY, min_size, QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap, clean_title)


def _draw_fitted_metric_value(p: QPainter, rect: QRectF, val: str, color: QColor = QColor("#0F172A")):
    """지표 수치/내용이 잘리지 않고 온전히 표시되도록 폰트 자동 조절 및 줄바꿈 지원"""
    p.setPen(color)
    clean_val = str(val).strip()

    fitted_font = None
    for size in [12, 11, 10]:
        font = QFont(FONT_FAMILY, size, QFont.Weight.Bold)
        fm = QFontMetrics(font)
        if fm.horizontalAdvance(clean_val) <= rect.width():
            fitted_font = font
            break

    if fitted_font:
        p.setFont(fitted_font)
        p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clean_val)
    else:
        p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        p.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap, clean_val)


def _build_zone_dashboard_metrics(zone_data: dict, stage_text: str) -> list:
    """대시보드 4대 지표 카드 데이터 생성 (커스텀 지표 또는 표준 지표)"""
    custom_metrics = zone_data.get("metrics")
    if custom_metrics and len(custom_metrics) >= 4:
        icons = ["🏢", "🏗️", "📌", "📍"]
        colors = [
            ("#1D4ED8", "#EFF6FF", "#BFDBFE"),
            ("#047857", "#ECFDF5", "#A7F3D0"),
            ("#7C3AED", "#F5F3FF", "#DDD6FE"),
            ("#B45309", "#FFFBEB", "#FDE68A"),
        ]
        known_icons = ("🏢", "🏗️", "📌", "📍", "🏷️", "💰", "📐", "🌟", "📊", "🚀", "⚡", "👉")
        metrics = []
        for i in range(4):
            lbl, val = custom_metrics[i]
            prefix = "" if any(lbl.startswith(ic) for ic in known_icons) else f"{icons[i]} "
            metrics.append((f"{prefix}{lbl}".strip(), val, colors[i][0], colors[i][1], colors[i][2]))
        return metrics

    return [
        ("🏢 사업 규모", zone_data.get("units", "상세 세대수 본문 참조"), "#1D4ED8", "#EFF6FF", "#BFDBFE"),
        ("🏗️ 시공 브랜드", zone_data.get("builder", "시공사 정보 본문 참조"), "#047857", "#ECFDF5", "#A7F3D0"),
        ("📌 추진 현황", stage_text or "사업 추진 및 시행 단계", "#7C3AED", "#F5F3FF", "#DDD6FE"),
        ("📍 건축 규모", zone_data.get("scale", "상세 계획 본문 참조"), "#B45309", "#FFFBEB", "#FDE68A"),
    ]


def _draw_zone_dashboard(p: QPainter, width: int, height: int, title: str, zone_name: str, zone_data: dict, office_name: str):
    """정비사업 구역 데이터 자동 수집 대시보드 (진행률 로드맵 + 4대 지표)"""
    card_rect = QRectF(2, 2, width - 4, height - 4)
    p.setBrush(QColor("#F8FAFC"))
    p.setPen(QPen(QColor("#CBD5E1"), 1.2))
    p.drawRoundedRect(card_rect, 12, 12)

    banner_rect = QRectF(12, 12, width - 24, 68)
    p.setBrush(QColor("#1E3A8A"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(banner_rect, 8, 8)

    cat_title = zone_data.get("category")
    if not cat_title:
        cat_title = f"정비사업 핵심 지표 대시보드 | {zone_name}" if zone_name else "부동산 핵심 분석 대시보드"
    elif zone_name and zone_name not in cat_title:
        cat_title = f"{cat_title} | {zone_name}"

    p.setPen(QColor("#93C5FD"))
    p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
    p.drawText(QRectF(24, 20, width - 48, 18), Qt.AlignmentFlag.AlignLeft, f"📊 {cat_title}")

    _draw_fitted_title(p, QRectF(24, 38, width - 48, 36), title)

    step_y = 88
    p.setPen(QColor("#334155"))
    is_prop = any(k in cat_title for k in ("매물", "단지", "아파트", "빌라", "오피스텔", "주택", "룸투어"))
    is_redev = any(k in cat_title for k in ("정비", "재개발", "재건축", "모아타운", "뉴타운", "입주권"))
    is_infra = any(k in cat_title for k in ("교통", "철도", "노선", "GTX", "지하철", "도로", "트램", "인프라"))

    progress_val = zone_data.get("progress", 70)
    stage_text = zone_data.get("stage", "사업시행인가 완료")

    if is_redev:
        step_label = "🚀 정비사업 추진 단계 로드맵"
    elif is_infra:
        step_label = "🚆 노선 및 인프라 개통 로드맵"
    elif is_prop:
        if progress_val >= 100:
            if any(k in stage_text for k in ("신축", "첫 입주", "미입주")):
                step_label = "✨ 신축 분양/준공 완료 현황"
            else:
                step_label = "🔑 매물 점유 상태 및 입주 가능 시기"
        else:
            step_label = "🏗️ 단지 공정률 및 입주 예정 일정"
    else:
        step_label = "🎯 정책 시행 및 추진 로드맵"
    p.drawText(QRectF(14, step_y, width - 28, 18), Qt.AlignmentFlag.AlignLeft, step_label)

    bar_y = step_y + 22
    bar_rect = QRectF(14, bar_y, width - 28, 24)
    p.setBrush(QColor("#E2E8F0"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(bar_rect, 12, 12)

    fill_w = max(90.0, (width - 28) * (progress_val / 100.0))
    fill_rect = QRectF(14, bar_y, fill_w, 24)
    fill_grad = QLinearGradient(14, bar_y, 14 + fill_w, bar_y)
    fill_grad.setColorAt(0.0, QColor("#2563EB"))
    fill_grad.setColorAt(1.0, QColor("#059669"))
    p.setBrush(QBrush(fill_grad))
    p.drawRoundedRect(fill_rect, 12, 12)

    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
    if is_prop and progress_val >= 100:
        if any(k in stage_text for k in ("신축", "첫 입주", "미입주")):
            bar_text = f"✨ 신축 첫 입주: {stage_text} (준공 완료)"
        else:
            clean_stage = stage_text if stage_text else "즉시 입주 가능"
            bar_text = f"🔑 입주 상태: {clean_stage}"
    elif progress_val >= 100:
        bar_text = f"✅ 시행 및 정착 완료: {stage_text}"
    else:
        bar_text = f"현재 진행률: {progress_val}% ({stage_text})"
    p.drawText(fill_rect, Qt.AlignmentFlag.AlignCenter, bar_text)

    grid_y = 144
    box_w = (width - 36) / 2
    box_h = 94

    metrics = _build_zone_dashboard_metrics(zone_data, stage_text)

    for idx, (label, val, text_color, bg_color, border_color) in enumerate(metrics):
        r = idx // 2
        c = idx % 2
        bx = 14 + c * (box_w + 8)
        by = grid_y + r * (box_h + 8)
        b_rect = QRectF(bx, by, box_w, box_h)

        p.setBrush(QColor(bg_color))
        p.setPen(QPen(QColor(border_color), 1.2))
        p.drawRoundedRect(b_rect, 8, 8)

        p.setPen(QColor(text_color))
        p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        p.drawText(QRectF(bx + 10, by + 8, box_w - 20, 20), Qt.AlignmentFlag.AlignLeft, label)

        _draw_fitted_metric_value(p, QRectF(bx + 10, by + 30, box_w - 20, 54), val)

    footer_rect = QRectF(14, height - 30, width - 28, 20)
    p.setPen(QColor("#64748B"))
    p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Normal))
    office_str = f"🏢 {office_name} | " if office_name else ""
    p.drawText(footer_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{office_str}네이버 블로그 공식 포스팅 요약 차트")


def _draw_property_dashboard(p: QPainter, width: int, height: int, title: str, prop_info: dict, office_name: str):
    """매물 핵심 지표 2x2 대시보드 + 특장점 하이라이트"""
    card_rect = QRectF(2, 2, width - 4, height - 4)
    p.setBrush(QColor("#F8FAFC"))
    p.setPen(QPen(QColor("#CBD5E1"), 1.2))
    p.drawRoundedRect(card_rect, 12, 12)

    banner_rect = QRectF(12, 12, width - 24, 68)
    p.setBrush(QColor("#0F766E"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(banner_rect, 8, 8)

    p.setPen(QColor("#99F6E4"))
    p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
    header_title = f"🏠 공인중개사 추천 매물 브리핑 | {office_name}" if office_name else "🏠 공인중개사 추천 매물 브리핑"
    p.drawText(QRectF(24, 20, width - 48, 18), Qt.AlignmentFlag.AlignLeft, header_title)

    _draw_fitted_title(p, QRectF(24, 38, width - 48, 36), title)

    grid_y = 90
    box_w = (width - 36) / 2
    box_h = 92

    deal_type = prop_info.get("deal_type", "매매")
    prop_type = prop_info.get("property_type", "아파트")
    metrics = [
        ("🏷️ 매물 구분", f"{prop_type} ({deal_type})", "#0D9488", "#F0FDFA", "#99F6E4"),
        ("💰 가격 조건", prop_info.get("price", "협의 가능"), "#DC2626", "#FEF2F2", "#FECACA"),
        ("📐 면적 및 구조", prop_info.get("area_structure", "상세 문의"), "#2563EB", "#EFF6FF", "#BFDBFE"),
        ("📍 소재지 위치", prop_info.get("location", "상세 위치 문의"), "#7C3AED", "#F5F3FF", "#DDD6FE"),
    ]


    for idx, (label, val, text_color, bg_color, border_color) in enumerate(metrics):
        r = idx // 2
        c = idx % 2
        bx = 14 + c * (box_w + 8)
        by = grid_y + r * (box_h + 8)
        b_rect = QRectF(bx, by, box_w, box_h)

        p.setBrush(QColor(bg_color))
        p.setPen(QPen(QColor(border_color), 1.2))
        p.drawRoundedRect(b_rect, 8, 8)

        p.setPen(QColor(text_color))
        p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        p.drawText(QRectF(bx + 10, by + 8, box_w - 20, 20), Qt.AlignmentFlag.AlignLeft, label)

        _draw_fitted_metric_value(p, QRectF(bx + 10, by + 30, box_w - 20, 52), val)

    feat = prop_info.get("features", "")
    if feat:
        feat_rect = QRectF(14, 298, width - 28, 56)
        p.setBrush(QColor("#FEF3C7"))
        p.setPen(QPen(QColor("#FDE68A"), 1.2))
        p.drawRoundedRect(feat_rect, 8, 8)

        p.setPen(QColor("#B45309"))
        p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        p.drawText(QRectF(24, 304, width - 48, 18), Qt.AlignmentFlag.AlignLeft, "🌟 매물 특장점 & 프리미엄 포인트")

        _draw_fitted_title(p, QRectF(24, 324, width - 48, 24), feat, max_size=11, min_size=9, color=QColor("#1E293B"))

    footer_rect = QRectF(14, height - 30, width - 28, 20)
    p.setPen(QColor("#64748B"))
    p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Normal))
    p.drawText(footer_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"🏢 {office_name} | 네이버 블로그 공식 포스팅 요약 차트")


def _draw_generic_dashboard(p: QPainter, width: int, height: int, title: str, items: list, office_name: str, card_category: str):
    """일반 뉴스/분석 2x2 그리드 대시보드"""
    card_rect = QRectF(2, 2, width - 4, height - 4)
    p.setBrush(QColor("#F8FAFC"))
    p.setPen(QPen(QColor("#CBD5E1"), 1.2))
    p.drawRoundedRect(card_rect, 12, 12)

    banner_rect = QRectF(12, 12, width - 24, 68)
    p.setBrush(QColor("#1E3A8A"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(banner_rect, 8, 8)

    p.setPen(QColor("#93C5FD"))
    p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
    p.drawText(QRectF(24, 20, width - 48, 18), Qt.AlignmentFlag.AlignLeft, f"📊 {card_category.upper()}")

    _draw_fitted_title(p, QRectF(24, 38, width - 48, 36), title)

    grid_y = 92
    box_w = (width - 36) / 2
    box_h = 126

    content_items = (items[:4] if items else []) + [("체크 포인트", "상세 분석 내용")] * 4
    content_items = content_items[:4]

    colors = [
        ("#1D4ED8", "#EFF6FF", "#BFDBFE", "1"),
        ("#047857", "#ECFDF5", "#A7F3D0", "2"),
        ("#7C3AED", "#F5F3FF", "#DDD6FE", "3"),
        ("#B45309", "#FFFBEB", "#FDE68A", "4"),
    ]

    for idx, (key, val) in enumerate(content_items):
        r = idx // 2
        c = idx % 2
        bx = 14 + c * (box_w + 8)
        by = grid_y + r * (box_h + 8)
        b_rect = QRectF(bx, by, box_w, box_h)

        t_col, bg_col, brd_col, num_str = colors[idx]

        p.setBrush(QColor(bg_col))
        p.setPen(QPen(QColor(brd_col), 1.2))
        p.drawRoundedRect(b_rect, 8, 8)

        # 넘버링 뱃지
        badge_rect = QRectF(bx + 10, by + 10, 22, 22)
        p.setBrush(QColor(t_col))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(badge_rect, 4, 4)
        p.setPen(QColor("#FFFFFF"))
        p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Bold))
        p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, num_str)

        # 항목명
        p.setPen(QColor(t_col))
        p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        p.drawText(QRectF(bx + 38, by + 10, box_w - 48, 22), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, key)

        # 구분 라인
        p.setPen(QPen(QColor(brd_col), 1))
        p.drawLine(int(bx + 10), int(by + 36), int(bx + box_w - 10), int(by + 36))

        # 내용
        p.setPen(QColor("#1E293B"))
        p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.DemiBold))
        p.drawText(QRectF(bx + 10, by + 42, box_w - 20, 74), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, val)

    footer_rect = QRectF(14, height - 30, width - 28, 20)
    p.setPen(QColor("#64748B"))
    p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Normal))
    office_str = f"🏢 {office_name} | " if office_name else ""
    p.drawText(footer_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{office_str}네이버 블로그 공식 포스팅 요약 차트")


def render_infographic_card(
    title: str,
    items: list = None,
    office_name: str = "",
    card_category: str = "부동산 핵심 체크포인트",
    zone_name: str = "",
    zone_data: dict = None,
    property_info: dict = None
) -> QImage:
    """
    네이버 블로그 본문 1:1 최적화(620x400) 고해상도 대시보드 인포그래픽 카드 생성
    - 정비구역 데이터(세대수, 시공사, 단계, 공정률 바) 자동 수집 시각화
    - 매물 정보(가격, 면적, 특장점) 4대 지표 카드 시각화
    - 불필요한 하단 여백 완전 제거 (1:1 픽셀 매칭)
    """
    width = 620
    height = 400

    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor("#FFFFFF"))

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    clean_title = title.replace("📌 ", "").strip()

    if zone_data:
        _draw_zone_dashboard(p, width, height, clean_title, zone_name or "정비사업지", zone_data, office_name)
    elif property_info and any(property_info.values()):
        _draw_property_dashboard(p, width, height, clean_title, property_info, office_name)
    else:
        _draw_generic_dashboard(p, width, height, clean_title, items or [], office_name, card_category)

    p.end()
    return img


def copy_chart_to_clipboard(img: QImage) -> bool:
    """QImage를 윈도우 시스템 클립보드에 복사"""
    if img is None or img.isNull():
        return False
    clipboard = QApplication.clipboard()
    clipboard.setImage(img)
    return True
