import sys
import re
sys.path.insert(0, ".")
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QImage,
    QLinearGradient,
    QPainter,
    QPen,
)

app = QApplication(sys.argv)
FONT_FAMILY = "Malgun Gothic"

def _draw_zone_dashboard(p: QPainter, width: int, height: int, title: str, zone_name: str, zone_data: dict, office_name: str):
    """정비사업 구역 데이터 자동 수집 대시보드 (진행률 로드맵 + 4대 지표)"""
    # 1. 외곽 둥근 카드
    card_rect = QRectF(2, 2, width - 4, height - 4)
    p.setBrush(QColor("#F8FAFC"))
    p.setPen(QPen(QColor("#CBD5E1"), 1.2))
    p.drawRoundedRect(card_rect, 12, 12)

    # 2. 상단 헤더 배너
    banner_rect = QRectF(12, 12, width - 24, 68)
    p.setBrush(QColor("#1E3A8A"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(banner_rect, 8, 8)

    p.setPen(QColor("#93C5FD"))
    p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
    p.drawText(QRectF(24, 20, width - 48, 18), Qt.AlignmentFlag.AlignLeft, f"📊 정비사업 자동 수집 분석 대시보드 | {zone_name}")

    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Bold))
    clean_title = title if len(title) <= 28 else title[:27] + "..."
    p.drawText(QRectF(24, 40, width - 48, 34), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clean_title)

    # 3. 로드맵 바
    step_y = 88
    p.setPen(QColor("#334155"))
    p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
    p.drawText(QRectF(14, step_y, width - 28, 18), Qt.AlignmentFlag.AlignLeft, "🚀 사업 추진 단계 로드맵")

    bar_y = step_y + 22
    bar_rect = QRectF(14, bar_y, width - 28, 24)
    p.setBrush(QColor("#E2E8F0"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(bar_rect, 12, 12)

    progress_val = zone_data.get("progress", 70)
    stage_text = zone_data.get("stage", "사업시행인가 완료")
    fill_w = max(90.0, (width - 28) * (progress_val / 100.0))
    fill_rect = QRectF(14, bar_y, fill_w, 24)
    fill_grad = QLinearGradient(14, bar_y, 14 + fill_w, bar_y)
    fill_grad.setColorAt(0.0, QColor("#2563EB"))
    fill_grad.setColorAt(1.0, QColor("#059669"))
    p.setBrush(QBrush(fill_grad))
    p.drawRoundedRect(fill_rect, 12, 12)

    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
    p.drawText(fill_rect, Qt.AlignmentFlag.AlignCenter, f"현재 공정률: {progress_val}% ({stage_text})")

    # 4. 4대 지표 그리드
    grid_y = 144
    box_w = (width - 36) / 2
    box_h = 94

    metrics = [
        ("🏢 총 세대수", zone_data.get("units", "약 2,870세대"), "#1D4ED8", "#EFF6FF", "#BFDBFE"),
        ("🏗️ 시공 브랜드", zone_data.get("builder", "현대건설 & GS건설"), "#047857", "#ECFDF5", "#A7F3D0"),
        ("📌 추진 현황", stage_text, "#7C3AED", "#F5F3FF", "#DDD6FE"),
        ("📍 건축 규모", zone_data.get("scale", "지하 2층 ~ 지상 38층"), "#B45309", "#FFFBEB", "#FDE68A"),
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

        p.setPen(QColor("#0F172A"))
        p.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        val_str = val if len(val) <= 22 else val[:21] + "..."
        p.drawText(QRectF(bx + 10, by + 30, box_w - 20, 54), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, val_str)

    # 5. 푸터
    footer_rect = QRectF(14, height - 30, width - 28, 20)
    p.setPen(QColor("#64748B"))
    p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Normal))
    p.drawText(footer_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"🏢 {office_name} | 네이버 블로그 공식 포스팅 요약 차트")


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
    p.drawText(QRectF(24, 20, width - 48, 18), Qt.AlignmentFlag.AlignLeft, f"🏠 공인중개사 추천 매물 브리핑 | {office_name}")

    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Bold))
    clean_title = title if len(title) <= 28 else title[:27] + "..."
    p.drawText(QRectF(24, 40, width - 48, 34), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clean_title)

    grid_y = 90
    box_w = (width - 36) / 2
    box_h = 92

    deal_type = prop_info.get("deal_type", "매매")
    prop_type = prop_info.get("property_type", "아파트")
    metrics = [
        ("🏷️ 매물 구분", f"{prop_type} ({deal_type})", "#0D9488", "#F0FDFA", "#99F6E4"),
        ("💰 가격 조건", prop_info.get("price", "협의 가능"), "#DC2626", "#FEF2F2", "#FECACA"),
        ("📐 면적 및 구조", prop_info.get("area_structure", "상세 문의"), "#2563EB", "#EFF6FF", "#BFDBFE"),
        ("📍 소재지 위치", prop_info.get("location", "대전 서구"), "#7C3AED", "#F5F3FF", "#DDD6FE"),
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

        p.setPen(QColor("#0F172A"))
        p.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        val_str = val if len(val) <= 22 else val[:21] + "..."
        p.drawText(QRectF(bx + 10, by + 30, box_w - 20, 52), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, val_str)

    feat = prop_info.get("features", "")
    if feat:
        feat_rect = QRectF(14, 298, width - 28, 56)
        p.setBrush(QColor("#FEF3C7"))
        p.setPen(QPen(QColor("#FDE68A"), 1.2))
        p.drawRoundedRect(feat_rect, 8, 8)

        p.setPen(QColor("#B45309"))
        p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        p.drawText(QRectF(24, 304, width - 48, 18), Qt.AlignmentFlag.AlignLeft, "🌟 매물 특장점 & 프리미엄 포인트")

        p.setPen(QColor("#1E293B"))
        p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.DemiBold))
        p.drawText(QRectF(24, 324, width - 48, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, feat[:45])

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

    p.setPen(QColor("#FFFFFF"))
    p.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Bold))
    clean_title = title if len(title) <= 28 else title[:27] + "..."
    p.drawText(QRectF(24, 40, width - 48, 34), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clean_title)

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
    p.drawText(footer_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"🏢 {office_name} | 네이버 블로그 공식 포스팅 요약 차트")

print("Code structure defined")
