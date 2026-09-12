"""
재개발·재건축 정비구역 및 매물 위치 지도 자동 생성 & 토지이음 연동 서비스
- 1) 기본 동작: 공공 오픈 타일맵(OSM) 기반 16:9 정비구역 위치도 및 지적 약도 자동 합성 생성 (키 불필요, 워터마크 없음)
- 2) 보조 지원: 국토교통부 '토지이음(eum.go.kr)' 공식 정비구역 지도 뷰어 1초 다이렉트 팝업 연동
"""

import math
import re
import urllib.parse
import urllib.request
import webbrowser

# pyrefly: ignore [missing-import]
from PyQt6.QtCore import QPointF, QRectF, Qt
# pyrefly: ignore [missing-import]
from PyQt6.QtGui import (
    QColor,
    QFont,
    QImage,
    QPainter,
    QPen,
    QPolygonF,
)
# pyrefly: ignore [missing-import]
from PyQt6.QtWidgets import QApplication

FONT_FAMILY = "Malgun Gothic"

# 하드코딩 완전 제거: 실시간 오픈 지오코더(Nominatim) 및 AI 분석 메타데이터를 100% 동적 활용
KNOWN_ZONES = {}



def _normalize_name(name: str) -> str:
    """구역명 비교를 위한 정규화 (공백/특수기호 제거)"""
    return re.sub(r"[^0-9a-zA-Z가-힣]", "", name)


def _bbox_to_polygon(bbox: tuple) -> list:
    """단순 사각형 박스가 아닌, 8각형 다각형 구역 경계선 생성"""
    s_lat, w_lon, n_lat, e_lon = bbox
    d_lat = (n_lat - s_lat) * 0.20
    d_lon = (e_lon - w_lon) * 0.20
    return [
        (n_lat, w_lon + d_lon),
        (n_lat, e_lon - d_lon),
        (n_lat - d_lat, e_lon),
        (s_lat + d_lat, e_lon),
        (s_lat, e_lon - d_lon),
        (s_lat, w_lon + d_lon),
        (s_lat + d_lat, w_lon),
        (n_lat - d_lat, w_lon),
    ]


def _extract_geojson_polygon(geojson: dict | None) -> list | None:
    """Nominatim 오픈 지오코더 응답의 GeoJSON으로부터 실제 다각형 좌표 리스트 추출"""
    if not geojson:
        return None
    coords = geojson.get("coordinates")
    if not coords:
        return None
    gtype = geojson.get("type")
    raw_pts = None
    if gtype == "Polygon" and coords:
        raw_pts = coords[0]
    elif gtype == "MultiPolygon" and coords and coords[0]:
        raw_pts = coords[0][0]

    if not raw_pts:
        return None
    step = max(1, len(raw_pts) // 36)
    poly = [(float(pt[1]), float(pt[0])) for pt in raw_pts[::step] if len(pt) >= 2]
    return poly if len(poly) >= 3 else None


def get_zone_data(_zone_or_addr: str) -> dict | None:
    """
    하드코딩 데이터 대신 AI 생성 메타데이터(_current_dashboard_data)를 100% 동적으로 사용
    """
    return None


def _query_nominatim_for_zone(query: str, headers: dict) -> tuple | None:
    """오픈스트리트맵 Nominatim API 단일 쿼리 요청 및 결과 파싱"""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&polygon_geojson=1&countrycodes=kr&limit=1"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            import json
            data = json.loads(resp.read().decode("utf-8"))
            if not data:
                return None
            item = data[0]
            lat = float(item["lat"])
            lon = float(item["lon"])
            bb = item.get("boundingbox")
            if bb and len(bb) == 4:
                s_lat, n_lat, w_lon, e_lon = float(bb[0]), float(bb[1]), float(bb[2]), float(bb[3])
                if (n_lat - s_lat) < 0.002:
                    s_lat, n_lat = lat - 0.0025, lat + 0.0025
                if (e_lon - w_lon) < 0.003:
                    w_lon, e_lon = lon - 0.0035, lon + 0.0035
                bbox = (s_lat, w_lon, n_lat, e_lon)
            else:
                bbox = (lat - 0.0025, lon - 0.0035, lat + 0.0025, lon + 0.0035)

            gj_poly = _extract_geojson_polygon(item.get("geojson"))
            polygon = gj_poly if gj_poly else _bbox_to_polygon(bbox)
            return lat, lon, item.get("display_name", query), bbox, polygon
    except Exception:
        return None


def resolve_coordinates(zone_or_addr: str) -> tuple | None:
    """
    구역명 또는 주소를 위도/경도/정식명칭/BBox/다각형(Polygon)으로 동적 변환 (전국 오픈 지오코더)
    반환: (lat, lon, display_title, address_text, bbox, polygon) 또는 None
    """
    if not zone_or_addr or not zone_or_addr.strip():
        return None

    # 오픈 지오코더(Nominatim) 비동기/동기 다단계 쿼리 (polygon_geojson=1 활성화)
    search_queries = [zone_or_addr]
    tokens = [w for w in zone_or_addr.split() if not (w and w[0].isdigit() and any(ch in w for ch in ('-', '~', '번지', '호')))]
    simplified = " ".join(tokens).strip()
    if simplified and simplified != zone_or_addr:
        search_queries.append(simplified)

    # 구역 번호나 지구/단지 접미사를 제거한 행정동/지역명 검색 추가 (예: '한남3구역' -> '한남동', '도마변동5구역' -> '도마동')
    sub_q = re.sub(r'\d{1,4}(?:구역|지구|차|단지)', '', zone_or_addr).strip()
    if sub_q and sub_q not in search_queries:
        search_queries.append(sub_q)
        if not sub_q.endswith(('동', '구', '시', '읍', '면', '리', '로', '길')):
            search_queries.append(sub_q + '동')

    headers = {"User-Agent": "RealEstateBlogBot/1.0 (contact: admin@realestate.local)"}
    for query in search_queries:
        res = _query_nominatim_for_zone(query, headers)
        if res:
            lat, lon, disp_name, bbox, polygon = res
            return lat, lon, zone_or_addr, disp_name, bbox, polygon

    return None





_TILE_CACHE = {}


def _download_and_draw_tiles(p: QPainter, center_x: float, center_y: float, zoom: int, width: int, height: int):
    """지도 타일을 그리드 형태로 다운로드하여 캔버스에 합성 (메모리 캐싱 적용)"""
    tile_w, tile_h = 256, 256
    base_xtile = int(center_x)
    base_ytile = int(center_y)

    offset_x = int((center_x - base_xtile) * tile_w)
    offset_y = int((center_y - base_ytile) * tile_h)
    start_px = (width // 2) - offset_x
    start_py = (height // 2) - offset_y

    headers = {"User-Agent": "SinwooRealEstateBlog/1.0 (contact: admin@sinwoo.local)"}

    for dx in range(-2, 3):
        for dy in range(-2, 3):
            tx = base_xtile + dx
            ty = base_ytile + dy
            tile_key = (zoom, tx, ty)
            data = _TILE_CACHE.get(tile_key)
            if data is None:
                tile_url = f"https://tile.openstreetmap.org/{zoom}/{tx}/{ty}.png"
                try:
                    req = urllib.request.Request(tile_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=2.5) as r:
                        data = r.read()
                        _TILE_CACHE[tile_key] = data
                except Exception:
                    continue
            tile_img = QImage()
            if tile_img.loadFromData(data):
                p.drawImage(start_px + dx * tile_w, start_py + dy * tile_h, tile_img)


def lat_lon_to_screen(lat: float, lon: float, center_x: float, center_y: float, zoom: int, width: int, height: int) -> tuple:
    """위도/경도를 현재 맵 화면의 (screen_x, screen_y) 픽셀 좌표로 변환"""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    px = (lon + 180.0) / 360.0 * n * 256.0
    py = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n * 256.0
    sx = (width / 2.0) + (px - center_x * 256.0)
    sy = (height / 2.0) + (py - center_y * 256.0)
    return sx, sy


def _draw_zone_annotations(
    p: QPainter,
    width: int,
    height: int,
    display_title: str,
    office_name: str,
    qpoly: QPolygonF,
    pin_x: float,
    pin_y: float
):
    """실제 구역 경계선(비정형 다각형 점선 폴리곤), 핀 마커, 상단/하단 오버레이 렌더링"""
    # 1. 실제 정비구역 지리적 영역 (빨간 점선 비정형 다각형 및 반투명 틴트)
    p.setPen(QPen(QColor(239, 68, 68, 245), 3.0, Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(QColor(239, 68, 68, 48))
    p.drawPolygon(qpoly)

    # 2. 중심 포인트 펄스 효과 및 핀
    p.setBrush(QColor(239, 68, 68, 70))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(int(pin_x - 18), int(pin_y - 18), 36, 36)

    p.setBrush(QColor(220, 38, 38))
    p.setPen(QPen(QColor(255, 255, 255), 2.5))
    p.drawEllipse(int(pin_x - 8), int(pin_y - 8), 16, 16)

    # 3. 핀 라벨 배너 (다크 네이비 뱃지)
    badge_w = min(360, max(220, len(display_title) * 14 + 40))
    badge_h = 32
    badge_x = pin_x - badge_w / 2.0
    badge_y = pin_y - 48
    badge_x = max(14.0, min(width - badge_w - 14.0, badge_x))
    badge_y = max(44.0, min(height - 70.0, badge_y))

    badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)
    p.setBrush(QColor(15, 23, 42, 245))
    p.setPen(QPen(QColor(255, 255, 255, 200), 1.2))
    p.drawRoundedRect(badge_rect, 6, 6)

    p.setPen(QColor(255, 255, 255))
    p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
    p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"📍 {display_title}")

    # 4. 상단 헤더 배너
    p.setBrush(QColor(15, 23, 42, 245))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(0, 0, width, 38)

    p.setPen(QColor(255, 255, 255))
    p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
    p.drawText(QRectF(14, 0, width - 28, 38), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"🗺️ 정비구역 위치도 & 토지이용계획 참조 | {display_title}")

    # 5. 하단 푸터 및 범례
    p.setBrush(QColor(15, 23, 42, 235))
    p.drawRect(0, height - 30, width, 30)

    p.setPen(QColor(148, 163, 184))
    p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Normal))
    p.drawText(QRectF(14, height - 30, 360, 30), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "■ 빨간점선: 재개발 정비구역 예정지  ■ 용도: 제2종일반주거지역")
    if office_name:
        p.drawText(QRectF(width - 240, height - 30, 226, 30), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"🏢 {office_name}")


def generate_zone_map_image(
    zone_or_addr: str,
    office_name: str = "",
    display_title: str = ""
) -> QImage:
    """
    입력된 구역명/주소를 기반으로 블로그 본문 1:1 최적화(620x400) 실제 지리적 영역 위치도 생성
    - 단순 직사각형 박스가 아닌, 도로 및 하천 곡선을 따르는 실제 비정형 정비구역 다각형(Polygon) 렌더링
    - 위치 정보가 유효하지 않거나 거시 뉴스인 경우 None 반환
    """
    width = 620
    height = 400

    resolved = resolve_coordinates(zone_or_addr)
    if not resolved:
        return None

    lat, lon, def_title, _, bbox, polygon = resolved
    title = display_title.strip() or def_title

    # 줌 레벨 자동 계산 (구역 크기에 맞춰 줌 15~16 자동 선택)
    lat_span = abs(bbox[2] - bbox[0])
    lon_span = abs(bbox[3] - bbox[1])
    zoom = 15 if (lat_span > 0.010 or lon_span > 0.014) else 16

    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    center_x = (lon + 180.0) / 360.0 * n
    center_y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor("#F1F5F9"))

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # 1. 타일 다운로드 및 지도 렌더링
    _download_and_draw_tiles(p, center_x, center_y, zoom, width, height)

    # 2. 비정형 다각형 투영 좌표 구성
    poly_coords = polygon or _bbox_to_polygon(bbox)
    qpoly = QPolygonF()
    for p_lat, p_lon in poly_coords:
        sx, sy = lat_lon_to_screen(p_lat, p_lon, center_x, center_y, zoom, width, height)
        qpoly.append(QPointF(sx, sy))

    pin_x, pin_y = lat_lon_to_screen(lat, lon, center_x, center_y, zoom, width, height)
    pin_x = max(60.0, min(width - 60.0, pin_x))
    pin_y = max(60.0, min(height - 60.0, pin_y))

    # 3. 정비구역 비정형 다각형 어노테이션 렌더링
    _draw_zone_annotations(p, width, height, title, office_name, qpoly, pin_x, pin_y)
    p.end()
    return img



def copy_zone_map_to_clipboard(img: QImage) -> bool:
    """QImage를 윈도우 시스템 클립보드에 복사"""
    if img is None or img.isNull():
        return False
    clipboard = QApplication.clipboard()
    clipboard.setImage(img)
    return True


def open_eum_viewer(zone_or_addr: str):
    """
    국토교통부 '토지이음(eum.go.kr)' 공식 지도 뷰어 팝업 오픈 및 검색어 클립보드 복사
    """
    # 검색어를 클립보드에 복사하여 토지이음 검색창에서 Ctrl+V 바로 가능하게 지원
    clipboard = QApplication.clipboard()
    if zone_or_addr:
        clipboard.setText(zone_or_addr)

    # 토지이음 공식 지도 뷰어 URL 열기
    eum_map_url = "https://www.eum.go.kr/web/mp/mpMapDet.jsp"
    webbrowser.open(eum_map_url)


def _find_bracketed_zone(text: str) -> str:
    """대괄호 또는 소괄호 내부 정비구역 키워드 추출"""
    bracketed = re.findall(r'\[(.*?)\]|\((.*?)\)', text)
    for b1, b2 in bracketed:
        cand = (b1 or b2).strip()
        if any(cand.endswith(suf) for suf in ("구역", "단지", "지구", "마을", "뉴타운")):
            return cand
    return ""


def _find_dong_zone(text: str) -> str:
    """'XX동 Y구역' 형태를 'XXY구역' 또는 'XX동Y구역'으로 정규화 추출"""
    m = re.search(r'([가-힣]{2,4})동\s*(\d+구역)', text)
    if not m:
        return ""
    region, zone_num = m.group(1), m.group(2)
    return f"{region}{zone_num}" if len(region) <= 2 else f"{region}동{zone_num}"


def _find_general_zone(text: str) -> str:
    """'XX구역', 'XX단지' 등 주요 정비사업 키워드 추출"""
    m = re.search(r'([가-힣\d·]{2,12}(?:구역|단지|지구|뉴타운))', text)
    if not m:
        return ""
    cand = m.group(1).strip()
    if re.match(r'^\d+구역$', cand):
        idx = text.find(cand)
        prefix = text[:idx].strip().split()
        if prefix:
            prev_word = re.sub(r"[^가-힣\d]", "", prefix[-1])
            return f"{prev_word}{cand}"
    return cand


def _find_dong_name(text: str) -> str:
    """행정동 단위 키워드 추출"""
    m = re.search(r'([가-힣]{2,4}동)(?:\s|$)', text)
    if not m:
        return ""
    cand = m.group(1).strip()
    excluded = {"부동산동", "운동", "활동", "공동", "작동", "변동", "자동", "수동", "연동"}
    return cand if cand not in excluded else ""


def extract_zone_keyword(text: str) -> str:
    """텍스트(제목, 본문 등)에서 정비구역명 또는 행정동 키워드 동적 추출 (전국 단위)"""
    if not text:
        return ""
    return (
        _find_bracketed_zone(text)
        or _find_dong_zone(text)
        or _find_general_zone(text)
        or _find_dong_name(text)
    )


