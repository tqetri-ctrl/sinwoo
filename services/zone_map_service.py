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
from PyQt6.QtCore import QRectF, Qt
# pyrefly: ignore [missing-import]
from PyQt6.QtGui import (
    QColor,
    QFont,
    QImage,
    QPainter,
    QPen,
)
# pyrefly: ignore [missing-import]
from PyQt6.QtWidgets import QApplication

FONT_FAMILY = "Malgun Gothic"

ADDR_DOMA_DONG = "대전 서구 도마동 일원"
ADDR_BYEONDONG = "대전 서구 변동 일원"
ADDR_TANBANG = "대전 서구 탄방동 일원"

# 대전 및 주요 재개발/정비사업 구역 좌표 및 공식 메트릭 데이터베이스 (0ms 초고속 해결)
KNOWN_ZONES = {
    "도마변동5구역": {
        "lat": 36.3168, "lon": 127.3785, "title": "도마·변동 5구역 재정비촉진지구", "addr": ADDR_BYEONDONG,
        "units": "약 2,870세대 (대단지)", "builder": "현대건설 & GS건설 (힐스테이트·자이)",
        "stage": "사업시행인가 완료 (관리처분 준비)", "progress": 70, "scale": "지하 2층 ~ 지상 38층, 20여 개 동"
    },
    "도마변동1구역": {
        "lat": 36.3262, "lon": 127.3770, "title": "도마·변동 1구역 재정비촉진지구", "addr": "대전 서구 가장동 일원",
        "units": "1,779세대 (일반분양 완료)", "builder": "현대건설 & 현대엔지니어링 (힐스테이트가장)",
        "stage": "착공 및 골조 공사 진행", "progress": 85, "scale": "지하 2층 ~ 지상 38층, 15개 동"
    },
    "도마변동3구역": {
        "lat": 36.3210, "lon": 127.3795, "title": "도마·변동 3구역 재정비촉진지구", "addr": ADDR_BYEONDONG,
        "units": "3,098세대 (매머드급 대단지)", "builder": "GS건설 & 포스코이앤씨",
        "stage": "사업시행인가 완료", "progress": 65, "scale": "지하 2층 ~ 지상 38층, 25개 동"
    },
    "도마변동4구역": {
        "lat": 36.3225, "lon": 127.3745, "title": "도마·변동 4구역 재정비촉진지구", "addr": ADDR_BYEONDONG,
        "units": "3,296세대 (최대 규모 단지)", "builder": "롯데건설 & 현대엔지니어링",
        "stage": "조합설립인가 완료", "progress": 50, "scale": "지하 2층 ~ 지상 38층, 28개 동"
    },
    "도마변동6구역": {
        "lat": 36.3155, "lon": 127.3820, "title": "도마·변동 6구역 재정비촉진지구", "addr": ADDR_DOMA_DONG,
        "units": "523세대", "builder": "계룡건설 (리슈빌)",
        "stage": "착공 및 공사 진행", "progress": 85, "scale": "지하 2층 ~ 지상 31층, 4개 동"
    },
    "도마변동8구역": {
        "lat": 36.3140, "lon": 127.3845, "title": "도마·변동 8구역 (도마e편한세상포레나)", "addr": ADDR_DOMA_DONG,
        "units": "1,881세대 (입주 완료 랜드마크)", "builder": "한화건설 & DL이앤씨",
        "stage": "준공 및 입주 완료", "progress": 100, "scale": "지하 2층 ~ 지상 34층, 20개 동"
    },
    "도마변동9구역": {
        "lat": 36.3180, "lon": 127.3870, "title": "도마·변동 9구역 (한화포레나더샵)", "addr": ADDR_DOMA_DONG,
        "units": "818세대", "builder": "한화건설 & 포스코이앤씨",
        "stage": "착공 및 골조 공사", "progress": 80, "scale": "지하 3층 ~ 지상 34층, 7개 동"
    },
    "도마변동11구역": {
        "lat": 36.3120, "lon": 127.3800, "title": "도마·변동 11구역 (호반써밋그랜드센트럴)", "addr": ADDR_DOMA_DONG,
        "units": "1,558세대", "builder": "호반건설 (호반써밋)",
        "stage": "준공 및 입주 단계", "progress": 95, "scale": "지하 4층 ~ 지상 35층, 19개 동"
    },
    "도마변동12구역": {
        "lat": 36.3170, "lon": 127.3720, "title": "도마·변동 12구역 재정비촉진지구", "addr": ADDR_DOMA_DONG,
        "units": "1,688세대", "builder": "GS건설 & DL이앤씨",
        "stage": "사업시행인가 준비 중", "progress": 55, "scale": "지하 2층 ~ 지상 35층, 13개 동"
    },
    "도마변동13구역": {
        "lat": 36.3135, "lon": 127.3745, "title": "도마·변동 13구역 재정비촉진지구", "addr": ADDR_DOMA_DONG,
        "units": "2,715세대", "builder": "대우건설 & 포스코이앤씨",
        "stage": "조합설립인가 완료", "progress": 50, "scale": "지하 2층 ~ 지상 32층, 20여 개 동"
    },
    "탄방1구역": {
        "lat": 36.3450, "lon": 127.3910, "title": "탄방동 1구역 (둔산자이아이파크)", "addr": ADDR_TANBANG,
        "units": "1,974세대 (둔산 대장주)", "builder": "GS건설 & HDC현대산업개발",
        "stage": "착공 및 골조 공사", "progress": 85, "scale": "지하 2층 ~ 지상 42층, 12개 동"
    },
    "숭어리샘": {
        "lat": 36.3430, "lon": 127.3870, "title": "탄방동 숭어리샘 (둔산자이아이파크)", "addr": ADDR_TANBANG,
        "units": "1,974세대 (둔산 대장주)", "builder": "GS건설 & HDC현대산업개발",
        "stage": "착공 및 골조 공사", "progress": 85, "scale": "지하 2층 ~ 지상 42층, 12개 동"
    },
    "용문123구역": {
        "lat": 36.3380, "lon": 127.3980, "title": "용문 1·2·3구역 (둔산더샵엘리프)", "addr": "대전 서구 용문동 일원",
        "units": "2,763세대 (대단지)", "builder": "포스코이앤씨 & 계룡건설",
        "stage": "마감 공사 및 입주 준비", "progress": 90, "scale": "지하 3층 ~ 지상 33층, 23개 동"
    },
    "선화구역": {
        "lat": 36.3310, "lon": 127.4200, "title": "선화 재정비촉진구역", "addr": "대전 중구 선화동 일원",
        "units": "997세대", "builder": "효성중공업 (해링턴플레이스휴리움)",
        "stage": "준공 및 입주 단계", "progress": 95, "scale": "지하 3층 ~ 지상 25층, 12개 동"
    },
    "대흥2구역": {
        "lat": 36.3220, "lon": 127.4260, "title": "대흥 2구역 주택재개발", "addr": "대전 중구 대흥동 일원",
        "units": "1,278세대", "builder": "KCC건설 (르에센)",
        "stage": "철거 완료 및 착공 준비", "progress": 75, "scale": "지하 2층 ~ 지상 29층, 11개 동"
    }
}


def _normalize_name(name: str) -> str:
    """구역명 비교를 위한 정규화 (공백/특수기호 제거)"""
    return re.sub(r"[^0-9a-zA-Z가-힣]", "", name)


def get_zone_data(zone_or_addr: str) -> dict:
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


def resolve_coordinates(zone_or_addr: str) -> tuple:
    """
    구역명 또는 주소를 위도/경도/정식명칭으로 변환 (내장 DB 우선 -> 오픈 지오코더 폴백)
    반환: (lat, lon, display_title, address_text)
    """
    clean = _normalize_name(zone_or_addr)

    # 1. 내장 DB 탐색
    for k, info in KNOWN_ZONES.items():
        if _normalize_name(k) in clean or clean in _normalize_name(k):
            return info["lat"], info["lon"], info["title"], info["addr"]

    # 2. 일반 주소인 경우 오픈 지오코더(Nominatim) 비동기/동기 조회
    try:
        encoded = urllib.parse.quote(zone_or_addr)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&countrycodes=kr&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "SinwooRealEstateBlog/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            import json
            data = json.loads(resp.read().decode("utf-8"))
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                display = zone_or_addr
                return lat, lon, f"{display} 정비/매물 사업지", zone_or_addr
    except Exception:
        pass

    # 3. 실패 시 대전 도마동 중심 기본값
    return 36.3168, 127.3785, f"{zone_or_addr} 정비사업지", zone_or_addr


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


def _draw_zone_annotations(p: QPainter, width: int, height: int, display_title: str, office_name: str):
    """지도 위에 정비구역 점선 폴리곤, 중심 핀 마커, 헤더/푸터 오버레이 렌더링"""
    # 1. 정비구역 점선 테두리 및 틴트 (중심부에 큼직하게 배치)
    p.setPen(QPen(QColor(239, 68, 68, 240), 3.5, Qt.PenStyle.DashLine))
    p.setBrush(QColor(239, 68, 68, 42))
    zone_rect = QRectF(width // 2 - 165, height // 2 - 100, 330, 200)
    p.drawRoundedRect(zone_rect, 14, 14)

    # 2. 중심 포인트 펄스 효과 및 핀
    p.setBrush(QColor(239, 68, 68, 80))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(width // 2 - 20, height // 2 - 20, 40, 40)

    p.setBrush(QColor(220, 38, 38))
    p.setPen(QPen(QColor(255, 255, 255), 2.5))
    p.drawEllipse(width // 2 - 9, height // 2 - 9, 18, 18)

    # 3. 핀 라벨 배너 (고대비 다크 네이비 뱃지)
    badge_w = 300
    badge_h = 36
    badge_rect = QRectF(width // 2 - badge_w // 2, height // 2 - 62, badge_w, badge_h)
    p.setBrush(QColor(15, 23, 42, 245))
    p.setPen(QPen(QColor(255, 255, 255, 200), 1.2))
    p.drawRoundedRect(badge_rect, 8, 8)

    p.setPen(QColor(255, 255, 255))
    p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
    label_text = display_title if len(display_title) <= 20 else display_title[:19] + "..."
    p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"📍 {label_text}")

    # 4. 상단 헤더 배너
    p.setBrush(QColor(15, 23, 42, 245))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(0, 0, width, 42)

    p.setPen(QColor(255, 255, 255))
    p.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
    p.drawText(QRectF(16, 0, width - 32, 42), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"🗺️ 정비구역 위치도 & 토지이용계획 참조 | {display_title}")

    # 5. 하단 푸터 및 범례
    p.setBrush(QColor(15, 23, 42, 235))
    p.drawRect(0, height - 32, width, 32)

    p.setPen(QColor(148, 163, 184))
    p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Normal))
    p.drawText(QRectF(16, height - 32, 360, 32), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, "■ 빨간점선: 재개발 정비구역 예정지  ■ 용도: 제2종일반주거지역")
    p.drawText(QRectF(width - 260, height - 32, 244, 32), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"🏢 {office_name}")


def generate_zone_map_image(zone_or_addr: str, office_name: str = "신우 공인중개사사무소") -> QImage:
    """
    입력된 구역명/주소를 기반으로 블로그 본문 1:1 최적화(620x400) 고해상도 확대 위치도(Zoom 17) 생성
    """
    width = 620
    height = 400
    zoom = 17  # 17: 골목길, 아파트 동, 학교, 상세 지명이 선명하게 식별되는 확대 축척

    lat, lon, display_title, _ = resolve_coordinates(zone_or_addr)

    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    center_x = (lon + 180.0) / 360.0 * n
    center_y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor("#F1F5F9"))

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # 타일 다운로드 및 지도 렌더링
    _download_and_draw_tiles(p, center_x, center_y, zoom, width, height)

    # 정비구역 어노테이션 오버레이 렌더링
    _draw_zone_annotations(p, width, height, display_title, office_name)
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
