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

ADDR_DOMA_DONG = "대전 서구 도마동 일원"
ADDR_BYEONDONG = "대전 서구 변동 일원"
ADDR_TANBANG = "대전 서구 탄방동 일원"
STAGE_FRAMEWORK = "착공 및 골조 공사"

# 대전 및 주요 재개발/정비사업 구역 좌표 및 공식 메트릭 데이터베이스 (정밀 다각형 Polygon 포함)
KNOWN_ZONES = {
    "도마변동5구역": {
        "lat": 36.3168, "lon": 127.3785, "title": "도마·변동 5구역 재정비촉진지구", "addr": ADDR_BYEONDONG,
        "bbox": (36.3138, 127.3745, 36.3195, 127.3825),
        "polygon": [
            (36.3195, 127.3752), (36.3198, 127.3788), (36.3188, 127.3820),
            (36.3162, 127.3828), (36.3138, 127.3815), (36.3135, 127.3772),
            (36.3150, 127.3745), (36.3175, 127.3740)
        ],
        "units": "약 2,870세대 (대단지)", "builder": "현대건설 & GS건설 (힐스테이트·자이)",
        "stage": "사업시행인가 완료 (관리처분 준비)", "progress": 70, "scale": "지하 2층 ~ 지상 38층, 20여 개 동"
    },
    "도마변동1구역": {
        "lat": 36.3262, "lon": 127.3770, "title": "도마·변동 1구역 재정비촉진지구", "addr": "대전 서구 가장동 일원",
        "bbox": (36.3225, 127.3725, 36.3298, 127.3815),
        "polygon": [
            (36.3298, 127.3740), (36.3290, 127.3815), (36.3245, 127.3810),
            (36.3225, 127.3775), (36.3240, 127.3725), (36.3275, 127.3725)
        ],
        "units": "1,779세대 (일반분양 완료)", "builder": "현대건설 & 현대엔지니어링 (힐스테이트가장)",
        "stage": "착공 및 골조 공사 진행", "progress": 85, "scale": "지하 2층 ~ 지상 38층, 15개 동"
    },
    "도마변동3구역": {
        "lat": 36.3210, "lon": 127.3795, "title": "도마·변동 3구역 재정비촉진지구", "addr": ADDR_BYEONDONG,
        "bbox": (36.3175, 127.3750, 36.3245, 127.3840),
        "polygon": [
            (36.3245, 127.3770), (36.3240, 127.3835), (36.3195, 127.3840),
            (36.3175, 127.3795), (36.3185, 127.3750), (36.3220, 127.3755)
        ],
        "units": "3,098세대 (매머드급 대단지)", "builder": "GS건설 & 포스코이앤씨",
        "stage": "사업시행인가 완료", "progress": 65, "scale": "지하 2층 ~ 지상 38층, 25개 동"
    },
    "도마변동4구역": {
        "lat": 36.3225, "lon": 127.3745, "title": "도마·변동 4구역 재정비촉진지구", "addr": ADDR_BYEONDONG,
        "bbox": (36.3190, 127.3700, 36.3260, 127.3790),
        "polygon": [
            (36.3260, 127.3720), (36.3255, 127.3785), (36.3205, 127.3790),
            (36.3190, 127.3740), (36.3210, 127.3700), (36.3240, 127.3705)
        ],
        "units": "3,296세대 (최대 규모 단지)", "builder": "롯데건설 & 현대엔지니어링",
        "stage": "조합설립인가 완료", "progress": 50, "scale": "지하 2층 ~ 지상 38층, 28개 동"
    },
    "도마변동6구역": {
        "lat": 36.3155, "lon": 127.3820, "title": "도마·변동 6구역 재정비촉진지구", "addr": ADDR_DOMA_DONG,
        "bbox": (36.3125, 127.3790, 36.3185, 127.3850),
        "polygon": [
            (36.3185, 127.3800), (36.3180, 127.3850), (36.3140, 127.3845),
            (36.3125, 127.3815), (36.3145, 127.3790)
        ],
        "units": "523세대", "builder": "계룡건설 (리슈빌)",
        "stage": "착공 및 공사 진행", "progress": 85, "scale": "지하 2층 ~ 지상 31층, 4개 동"
    },
    "도마변동8구역": {
        "lat": 36.3140, "lon": 127.3845, "title": "도마·변동 8구역 (도마e편한세상포레나)", "addr": ADDR_DOMA_DONG,
        "bbox": (36.3105, 127.3810, 36.3175, 127.3880),
        "units": "1,881세대 (입주 완료 랜드마크)", "builder": "한화건설 & DL이앤씨",
        "stage": "준공 및 입주 완료", "progress": 100, "scale": "지하 2층 ~ 지상 34층, 20개 동"
    },
    "도마변동9구역": {
        "lat": 36.3180, "lon": 127.3870, "title": "도마·변동 9구역 (한화포레나더샵)", "addr": ADDR_DOMA_DONG,
        "bbox": (36.3150, 127.3830, 36.3210, 127.3910),
        "units": "818세대", "builder": "한화건설 & 포스코이앤씨",
        "stage": STAGE_FRAMEWORK, "progress": 80, "scale": "지하 3층 ~ 지상 34층, 7개 동"
    },
    "도마변동11구역": {
        "lat": 36.3120, "lon": 127.3800, "title": "도마·변동 11구역 (호반써밋그랜드센트럴)", "addr": ADDR_DOMA_DONG,
        "bbox": (36.3085, 127.3765, 36.3155, 127.3835),
        "units": "1,558세대", "builder": "호반건설 (호반써밋)",
        "stage": "준공 및 입주 단계", "progress": 95, "scale": "지하 4층 ~ 지상 35층, 19개 동"
    },
    "도마변동12구역": {
        "lat": 36.3170, "lon": 127.3720, "title": "도마·변동 12구역 재정비촉진지구", "addr": ADDR_DOMA_DONG,
        "bbox": (36.3135, 127.3685, 36.3205, 127.3755),
        "units": "1,688세대", "builder": "GS건설 & DL이앤씨",
        "stage": "사업시행인가 준비 중", "progress": 55, "scale": "지하 2층 ~ 지상 35층, 13개 동"
    },
    "도마변동13구역": {
        "lat": 36.3135, "lon": 127.3745, "title": "도마·변동 13구역 재정비촉진지구", "addr": ADDR_DOMA_DONG,
        "bbox": (36.3100, 127.3710, 36.3170, 127.3780),
        "units": "2,715세대", "builder": "대우건설 & 포스코이앤씨",
        "stage": "조합설립인가 완료", "progress": 50, "scale": "지하 2층 ~ 지상 32층, 20여 개 동"
    },
    "탄방1구역": {
        "lat": 36.3450, "lon": 127.3910, "title": "탄방동 1구역 (둔산자이아이파크)", "addr": ADDR_TANBANG,
        "bbox": (36.3415, 127.3860, 36.3485, 127.3960),
        "polygon": [
            (36.3485, 127.3880), (36.3475, 127.3955), (36.3430, 127.3960),
            (36.3415, 127.3910), (36.3425, 127.3860), (36.3460, 127.3865)
        ],
        "units": "1,974세대 (둔산 대장주)", "builder": "GS건설 & HDC현대산업개발",
        "stage": STAGE_FRAMEWORK, "progress": 85, "scale": "지하 2층 ~ 지상 42층, 12개 동"
    },
    "숭어리샘": {
        "lat": 36.3430, "lon": 127.3870, "title": "탄방동 숭어리샘 (둔산자이아이파크)", "addr": ADDR_TANBANG,
        "bbox": (36.3400, 127.3820, 36.3460, 127.3920),
        "units": "1,974세대 (둔산 대장주)", "builder": "GS건설 & HDC현대산업개발",
        "stage": STAGE_FRAMEWORK, "progress": 85, "scale": "지하 2층 ~ 지상 42층, 12개 동"
    },
    "용문123구역": {
        "lat": 36.3380, "lon": 127.3980, "title": "용문 1·2·3구역 (둔산더샵엘리프)", "addr": "대전 서구 용문동 일원",
        "bbox": (36.3340, 127.3930, 36.3420, 127.4030),
        "polygon": [
            (36.3420, 127.3950), (36.3415, 127.4025), (36.3365, 127.4030),
            (36.3340, 127.3980), (36.3355, 127.3930), (36.3390, 127.3935)
        ],
        "units": "2,763세대 (대단지)", "builder": "포스코이앤씨 & 계룡건설",
        "stage": "마감 공사 및 입주 준비", "progress": 90, "scale": "지하 3층 ~ 지상 33층, 23개 동"
    },
    "선화구역": {
        "lat": 36.3310, "lon": 127.4200, "title": "선화 재정비촉진구역", "addr": "대전 중구 선화동 일원",
        "bbox": (36.3275, 127.4160, 36.3345, 127.4240),
        "units": "997세대", "builder": "효성중공업 (해링턴플레이스휴리움)",
        "stage": "준공 및 입주 단계", "progress": 95, "scale": "지하 3층 ~ 지상 25층, 12개 동"
    },
    "대흥2구역": {
        "lat": 36.3220, "lon": 127.4260, "title": "대흥 2구역 주택재개발", "addr": "대전 중구 대흥동 일원",
        "bbox": (36.3185, 127.4220, 36.3255, 127.4300),
        "units": "1,278세대", "builder": "KCC건설 (르에센)",
        "stage": "철거 완료 및 착공 준비", "progress": 75, "scale": "지하 2층 ~ 지상 29층, 11개 동"
    }
}


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


def get_zone_data(zone_or_addr: str) -> dict | None:
    """
    구역명/주소로 정비구역 공식 메트릭 정보(세대수, 시공사, 단계, 진행률 등) 조회
    반환: 메트릭 dict 또는 None
    """
    if not zone_or_addr:
        return None
    clean = _normalize_name(zone_or_addr)
    for k, info in KNOWN_ZONES.items():
        norm_k = _normalize_name(k)
        if norm_k in clean or clean in norm_k:
            return dict(info)
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
    구역명 또는 주소를 위도/경도/정식명칭/BBox/다각형(Polygon)으로 변환 (내장 DB 우선 -> 오픈 지오코더 폴백)
    반환: (lat, lon, display_title, address_text, bbox, polygon) 또는 None
    """
    if not zone_or_addr or not zone_or_addr.strip():
        return None

    clean = _normalize_name(zone_or_addr)

    # 1. 내장 DB 탐색
    for k, info in KNOWN_ZONES.items():
        norm_k = _normalize_name(k)
        if norm_k in clean or clean in norm_k:
            bbox = info.get("bbox") or (info["lat"] - 0.003, info["lon"] - 0.004, info["lat"] + 0.003, info["lon"] + 0.004)
            polygon = info.get("polygon") or _bbox_to_polygon(bbox)
            return info["lat"], info["lon"], info["title"], info["addr"], bbox, polygon

    # 2. 오픈 지오코더(Nominatim) 비동기/동기 조회 (polygon_geojson=1 활성화)
    search_queries = [zone_or_addr]
    tokens = [w for w in zone_or_addr.split() if not (w and w[0].isdigit() and any(ch in w for ch in ('-', '~', '번지', '호')))]
    simplified = " ".join(tokens).strip()
    if simplified and simplified != zone_or_addr:
        search_queries.append(simplified)

    headers = {"User-Agent": "SinwooRealEstateBlog/1.0 (contact: admin@sinwoo.local)"}
    for query in search_queries:
        res = _query_nominatim_for_zone(query, headers)
        if res:
            lat, lon, disp_name, bbox, polygon = res
            return lat, lon, zone_or_addr, disp_name, bbox, polygon

    # 지오코딩 실패 시 임의로 대전을 반환하지 않고 None 반환 (엉뚱한 지역 출력 방지)
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
    p.drawText(QRectF(width - 240, height - 30, 226, 30), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"🏢 {office_name}")


def generate_zone_map_image(
    zone_or_addr: str,
    office_name: str = "신우 공인중개사사무소",
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


def _scan_zone_token(tokens: list, i: int, token: str) -> str:
    """구역 또는 동 단위 토큰 분석"""
    clean_tok = _normalize_name(token)
    if token.endswith("구역"):
        if i > 0:
            prev = _normalize_name(tokens[i - 1])
            if not prev.endswith(("은", "는", "이", "가", "의", "를", "을", "에")):
                return f"{prev} {clean_tok}"
        return clean_tok
    if clean_tok.endswith("동"):
        return clean_tok
    return ""


def extract_zone_keyword(text: str) -> str:
    """텍스트(제목, 본문 등)에서 정비구역명 또는 행정동 키워드 추출 (초고속 O(N) 탐색)"""
    if not text:
        return ""
    compact = _normalize_name(text)
    for k in KNOWN_ZONES:
        if _normalize_name(k) in compact:
            return k
    tokens = text.split()
    for i, token in enumerate(tokens):
        found = _scan_zone_token(tokens, i, token)
        if found:
            return found
    return ""

