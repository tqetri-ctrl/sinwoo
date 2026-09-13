"""
공인중개사 네이버 블로그 글 생성기 메인 윈도우 (PyQt6 기반)
- 초보자도 쉽게 사용하는 1-2-3-4 단계식 직관적 워크플로우
- 🏠 현장 사진 다중 첨부 기반 매물 소개 (매매/전세/월세/분양)
- 📰 최신 인터넷 기사 검색 기반 브리핑
- 📁 보도자료 및 문서(PDF, HWP, DOCX 등) 분석
- 네이버 블로그 스마트에디터 스타일 실시간 미리보기 & 원클릭 복사
"""

import os
import re
import sys
from datetime import datetime
# pyrefly: ignore [missing-import]
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QRadioButton, QButtonGroup,
    QTabWidget, QFileDialog, QMessageBox, QFrame, QSplitter,
    QDialog, QCheckBox, QComboBox, QTextBrowser, QApplication, QProgressBar,
    QListWidget, QListWidgetItem, QAbstractItemView, QScrollArea, QStackedWidget,
    QSizePolicy
)
# pyrefly: ignore [missing-import]
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QUrl
# pyrefly: ignore [missing-import]
from PyQt6.QtGui import QFont, QIcon, QClipboard, QTextDocument, QImage

from config import load_config, save_config
from prompts.blog_templates import TONE_PRESETS
from services.chart_service import extract_summary_items, render_infographic_card, copy_chart_to_clipboard
from services.gemini_service import GeminiBlogService, clean_body_instructions
from services.news_search_service import fetch_yonhap_realestate_news
from services.text_utils import strip_leading_emojis
from services.zone_map_service import (
    generate_zone_map_image, copy_zone_map_to_clipboard, open_eum_viewer,
    get_zone_data, extract_zone_keyword
)
from ui.settings_dialog import SettingsDialog
from ui.styles import (
    MAIN_STYLESHEET, generate_blog_preview_html, is_card_news_text, render_card_news_blocks
)
from ui.threads import YonhapNewsLoadThread, BlogGenerationThread

DEFAULT_MODEL_NAME = "gemini-3.6-flash"
FLASH_35_MODEL_NAME = "gemini-3.5-flash"
FLASH_35_LITE_MODEL_NAME = "gemini-3.5-flash-lite"
FLASH_31_LITE_MODEL_NAME = "gemini-3.1-flash-lite"
MUTED_TEXT_STYLE = "color: #475569; font-size: 13px;"
CARD_HEADER_STYLE = "font-weight: bold; font-size: 16px; color: #1E293B;"
GRID_LABEL_STYLE = "font-weight: 600; color: #334155; font-size: 13px;"


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.gemini_service = GeminiBlogService(
            api_key=self.config.get("gemini_api_key", ""),
            model_name=self.config.get("selected_model", DEFAULT_MODEL_NAME)
        )
        self.current_result = None
        self.property_photos = []  # 매물 탭 현장 사진 목록
        self.selected_doc_files = []  # 문서/자료 탭 첨부파일 목록
        self.yonhap_articles = []  # 연합뉴스 실시간 부동산 속보 목록
        self.yonhap_thread = None
        self._current_chart_img = None
        self._current_zone_map_img = None
        self._current_dashboard_data = None
        self._current_map_data = None

        self.init_window()
        self.init_ui()
        self.update_api_status_badge()
        self.load_yonhap_news()

    def init_window(self):
        self.setWindowTitle("신우 공인중개사 | AI 네이버 블로그 글 생성기")
        self.setStyleSheet(MAIN_STYLESHEET)

        # 1920x1080 FHD 및 다양한 스케일 환경에서 쾌적하게 꽉 차도록 넉넉한 창 크기 설정
        screen = QApplication.primaryScreen()
        if screen:
            avail_geo = screen.availableGeometry()
            target_w = max(1380, min(1680, int(avail_geo.width() * 0.90)))
            target_h = max(860, min(1000, int(avail_geo.height() * 0.90)))
            self.resize(target_w, target_h)

            # 화면 중앙 정렬
            x = avail_geo.x() + (avail_geo.width() - target_w) // 2
            y = avail_geo.y() + (avail_geo.height() - target_h) // 2
            self.move(x, y)
        else:
            self.resize(1500, 880)

        self.setMinimumSize(960, 640)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 상단 헤더 바 (높이 고정, 상단 여백 팽창 방지)
        header = self.create_header()
        main_layout.addWidget(header, 0)

        # 본문 반응형 스플리터 (화면 크기에 따라 가로/세로 유연하게 자동 조절)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setContentsMargins(12, 6, 12, 6)
        self.splitter.setHandleWidth(8)

        # 좌측: 1-2-3단계 입력 영역
        left_panel = self.create_left_input_panel()
        self.splitter.addWidget(left_panel)

        # 우측: 4단계 결과 미리보기 & 복사 영역
        right_panel = self.create_right_result_panel()
        self.splitter.addWidget(right_panel)

        # 좌측 입력창과 우측 미리보기가 5:5 비율로 균등하게 넉넉한 폭을 갖도록 설정
        self.splitter.setSizes([700, 780])
        self.splitter.setStretchFactor(0, 5)
        self.splitter.setStretchFactor(1, 5)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        main_layout.addWidget(self.splitter, 1)

    def resizeEvent(self, event):
        """화면 크기 변경 시 레이아웃을 최적화하는 반응형(Responsive) 이벤트 핸들러"""
        super().resizeEvent(event)
        width = event.size().width()

        # 960px 미만 (작은 창, 세로 모니터, 윈도우 좌우 분할 스냅): 상하 세로 분할로 자동 전환
        if width < 960:
            if self.splitter.orientation() != Qt.Orientation.Vertical:
                self.splitter.setOrientation(Qt.Orientation.Vertical)
                self.splitter.setSizes([420, 480])
            self.lbl_subtitle.setVisible(False)
        else:
            # 960px 이상 (일반 가로 모니터): 좌우 2단 컬럼으로 자동 복귀
            if self.splitter.orientation() != Qt.Orientation.Horizontal:
                self.splitter.setOrientation(Qt.Orientation.Horizontal)
                self.splitter.setSizes([width // 2, width // 2])
            self.lbl_subtitle.setVisible(True)

    def create_header(self) -> QWidget:
        """상단 헤더 카드 (로고, 상태, 간편 설정 버튼) - 슬림 바 (높이 고정으로 낭비 여백 원천 차단)"""
        header = QFrame()
        header.setObjectName("HeaderCard")
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header.setFixedHeight(50)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(12)

        # 좌측 타이틀 (가로 인라인 배치로 위아래 낭비 공간 최소화)
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        self.lbl_title = QLabel('🏢 <span style="color: #1D4ED8; font-weight: 800; font-size: 18px;">신우 공인중개사</span> <span style="color: #CBD5E1; font-weight: 300; font-size: 16px;">|</span> <span style="color: #0F172A; font-weight: 700; font-size: 17px;">AI 네이버 블로그 글 생성기</span>')
        self.lbl_title.setObjectName("AppTitle")
        title_layout.addWidget(self.lbl_title, 0, Qt.AlignmentFlag.AlignVCenter)

        self.lbl_subtitle = QLabel("· 현장 사진 매물 소개부터 부동산 정책/이슈 브리핑까지 원클릭 자동 생성")
        self.lbl_subtitle.setStyleSheet("color: #64748B; font-size: 13px;")
        title_layout.addWidget(self.lbl_subtitle, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(title_layout)

        layout.addStretch()

        # 우측 상태 및 설정 버튼
        self.lbl_api_status = QLabel("🟢 API 연결 완료")
        self.lbl_api_status.setStyleSheet("font-weight: bold; font-size: 13px; padding: 5px 12px; border-radius: 6px; background: #DCFCE7; color: #166534;")
        layout.addWidget(self.lbl_api_status, 0, Qt.AlignmentFlag.AlignVCenter)

        self.btn_settings = QPushButton("⚙️ 환경 설정 (API 키)")
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setStyleSheet("padding: 5px 12px; font-size: 13px;")
        self.btn_settings.clicked.connect(self.open_settings_dialog)
        layout.addWidget(self.btn_settings, 0, Qt.AlignmentFlag.AlignVCenter)

        return header

    def update_api_status_badge(self):
        key = self.config.get("gemini_api_key", "").strip()
        if key:
            self.lbl_api_status.setText("🟢 API 키 등록됨")
            self.lbl_api_status.setStyleSheet("font-weight: bold; font-size: 13px; padding: 5px 12px; border-radius: 6px; background: #DCFCE7; color: #166534;")
        else:
            self.lbl_api_status.setText("🟡 API 키 필요 (클릭)")
            self.lbl_api_status.setStyleSheet("font-weight: bold; font-size: 13px; padding: 5px 12px; border-radius: 6px; background: #FEF3C7; color: #92400E; cursor: pointer;")

    def open_settings_dialog(self):
        dlg = SettingsDialog(self, self.config)
        if dlg.exec():
            self.config = load_config()
            self.gemini_service.set_api_key(self.config.get("gemini_api_key", ""))
            self.gemini_service.set_model(self.config.get("selected_model", DEFAULT_MODEL_NAME))
            self.update_api_status_badge()
            QMessageBox.information(self, "완료", "설정이 성공적으로 저장되었습니다.")

    def create_left_input_panel(self) -> QWidget:
        """좌측 1-2-3단계 입력 영역 (상단 스크롤 + 하단 고정 생성 버튼)"""
        container = QWidget()
        container.setMinimumWidth(480)
        outer_layout = QVBoxLayout(container)
        outer_layout.setContentsMargins(0, 0, 4, 0)
        outer_layout.setSpacing(6)

        # 상단 스크롤 영역 (1단계 글감 + 2단계 말투)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_content.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(8)

        # ----------------------------------------------------
        # [1단계] 글감 넣기 카드 (3개 탭)
        # ----------------------------------------------------
        card_step1 = QFrame()
        card_step1.setObjectName("CardFrame")
        layout_step1 = QVBoxLayout(card_step1)
        layout_step1.setContentsMargins(10, 8, 10, 8)
        layout_step1.setSpacing(8)

        header_step1 = QHBoxLayout()
        header_step1.setSpacing(8)
        badge1 = QLabel("1단계")
        badge1.setObjectName("StepBadge")
        title1 = QLabel("글감 선택:")
        title1.setObjectName("StepTitle")
        header_step1.addWidget(badge1)
        header_step1.addWidget(title1)

        # 드롭다운 선택 메뉴 (여유로운 너비로 가려짐 없이 깔끔하게 표시)
        self.combo_input_mode = QComboBox()
        self.combo_input_mode.addItems([
            "🏠 현장 사진 매물 소개",
            "📰 부동산 뉴스/정보 실시간 브리핑",
            "📁 문서/자료 분석 (PDF/HWP)"
        ])
        self.combo_input_mode.setStyleSheet(
            "font-weight: bold; color: #1D4ED8; font-size: 14px; "
            "padding: 5px 10px; background-color: #EFF6FF; border: 1.5px solid #93C5FD;"
        )
        self.combo_input_mode.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        header_step1.addWidget(self.combo_input_mode, 1)
        layout_step1.addLayout(header_step1)

        # 모드 전환용 스택 위젯
        self.stacked_input = QStackedWidget()
        self.input_tab = self.stacked_input  # 호환성 별칭

        # ====================================================
        # 모드 1: 🏠 현장 사진 매물 소개
        # ====================================================
        tab_property = QWidget()
        tab_prop_layout = QVBoxLayout(tab_property)
        tab_prop_layout.setContentsMargins(0, 4, 0, 0)
        tab_prop_layout.setSpacing(6)

        # 1) 거래 유형 및 매물 종류 선택 (안정적인 4열 그리드 분할)
        prop_top_grid = QGridLayout()
        prop_top_grid.setHorizontalSpacing(8)
        prop_top_grid.setVerticalSpacing(4)

        lbl_deal = QLabel("거래 형태:")
        lbl_deal.setStyleSheet(GRID_LABEL_STYLE)
        prop_top_grid.addWidget(lbl_deal, 0, 0)
        self.combo_deal_type = QComboBox()
        self.combo_deal_type.addItems(["월세 (보증금/월세)", "전세", "매매", "단기임대", "분양/임대", "기타"])
        prop_top_grid.addWidget(self.combo_deal_type, 0, 1)

        lbl_ptype = QLabel("매물 종류:")
        lbl_ptype.setStyleSheet(GRID_LABEL_STYLE)
        prop_top_grid.addWidget(lbl_ptype, 0, 2)
        self.combo_prop_type = QComboBox()
        self.combo_prop_type.addItems(["아파트", "오피스텔", "빌라/다세대", "원룸/투룸", "상가/사무실", "단독/다가구", "토지/공장/창고", "기타"])
        prop_top_grid.addWidget(self.combo_prop_type, 0, 3)

        prop_top_grid.setColumnStretch(1, 1)
        prop_top_grid.setColumnStretch(3, 1)
        tab_prop_layout.addLayout(prop_top_grid)

        # 2) 매물 기본 정보 입력 그리드
        prop_grid = QGridLayout()
        prop_grid.setHorizontalSpacing(8)
        prop_grid.setVerticalSpacing(5)

        lbl_loc = QLabel("매물 위치/이름:")
        lbl_loc.setStyleSheet(GRID_LABEL_STYLE)
        prop_grid.addWidget(lbl_loc, 0, 0)
        self.edit_prop_location = QLineEdit()
        self.edit_prop_location.setPlaceholderText("예: 역삼동 신축 오피스텔 (역삼역 도보 3분)")
        prop_grid.addWidget(self.edit_prop_location, 0, 1)

        lbl_price = QLabel("가격 조건:")
        lbl_price.setStyleSheet(GRID_LABEL_STYLE)
        prop_grid.addWidget(lbl_price, 1, 0)
        self.edit_prop_price = QLineEdit()
        self.edit_prop_price.setPlaceholderText("예: 보증금 3,000만원 / 월세 150만원 (또는 매매 12억)")
        prop_grid.addWidget(self.edit_prop_price, 1, 1)

        lbl_area = QLabel("면적/구조/층수:")
        lbl_area.setStyleSheet(GRID_LABEL_STYLE)
        prop_grid.addWidget(lbl_area, 2, 0)
        self.edit_prop_area = QLineEdit()
        self.edit_prop_area.setPlaceholderText("예: 전용 59㎡(18평) / 방2 화1 / 15층 중 8층 (남향)")
        prop_grid.addWidget(self.edit_prop_area, 2, 1)

        lbl_feat = QLabel("특장점/옵션:")
        lbl_feat.setStyleSheet(GRID_LABEL_STYLE)
        prop_grid.addWidget(lbl_feat, 3, 0)
        self.edit_prop_features = QLineEdit()
        self.edit_prop_features.setPlaceholderText("예: 올수리 첫입주, 시스템에어컨 풀옵션, 주차가능, 채광굿")
        prop_grid.addWidget(self.edit_prop_features, 3, 1)

        lbl_memo = QLabel("추가 전달사항:")
        lbl_memo.setStyleSheet(GRID_LABEL_STYLE)
        prop_grid.addWidget(lbl_memo, 4, 0)
        self.edit_prop_memo = QLineEdit()
        self.edit_prop_memo.setPlaceholderText("예: 즉시입주 협의가능, 신혼부부나 직장인에게 강추")
        prop_grid.addWidget(self.edit_prop_memo, 4, 1)

        prop_grid.setColumnStretch(0, 0)
        prop_grid.setColumnStretch(1, 1)
        tab_prop_layout.addLayout(prop_grid)

        # 3) 현장 사진 다중 첨부 영역
        photo_header = QHBoxLayout()
        self.lbl_photo_count = QLabel("📷 등록 사진: 0장 (여러 장 선택 가능)")
        self.lbl_photo_count.setStyleSheet("font-weight: bold; color: #2563EB; font-size: 13px;")
        photo_header.addWidget(self.lbl_photo_count)
        photo_header.addStretch()

        btn_add_photos = QPushButton("📸 사진 추가")
        btn_add_photos.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_photos.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 4px 10px; font-size: 13px;")
        btn_add_photos.clicked.connect(self.on_add_property_photos)
        photo_header.addWidget(btn_add_photos)

        btn_clear_photos = QPushButton("전체 비우기")
        btn_clear_photos.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_photos.setStyleSheet("padding: 4px 10px; font-size: 13px;")
        btn_clear_photos.clicked.connect(self.on_clear_property_photos)
        photo_header.addWidget(btn_clear_photos)

        tab_prop_layout.addLayout(photo_header)

        # 사진 파일 목록 리스트 위젯
        self.list_photos = QListWidget()
        self.list_photos.setObjectName("PhotoList")
        self.list_photos.setFixedHeight(64)
        self.list_photos.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tab_prop_layout.addWidget(self.list_photos)

        self.chk_prop_local_search = QCheckBox("🌐 주변 최신 개발 호재 및 시세 실시간 검색 반영")
        self.chk_prop_local_search.setChecked(self.config.get("enable_local_search", False))
        self.chk_prop_local_search.setToolTip("매물 소재지 주변의 최신 교통망, 개발 호재, 시세를 실시간 검색하여 입지 분석에 반영합니다.")
        self.chk_prop_local_search.setStyleSheet("color: #475569; font-size: 13px; margin-top: 2px;")
        tab_prop_layout.addWidget(self.chk_prop_local_search)

        self.stacked_input.addWidget(tab_property)

        # ====================================================
        # 모드 2: 📰 인터넷 기사 찾아서 쓰기 (기존 기사/이슈 모드)
        # ====================================================
        tab_news = QWidget()
        tab_news_layout = QVBoxLayout(tab_news)
        tab_news_layout.setContentsMargins(0, 4, 0, 0)
        tab_news_layout.setSpacing(6)

        # 상단 가이드 & 오늘 작성 기준일 배지
        news_header = QHBoxLayout()
        lbl_news_guide = QLabel("💡 작성할 주제를 입력하거나, 아래 연합뉴스 속보를 선택하세요.")
        lbl_news_guide.setStyleSheet(MUTED_TEXT_STYLE)
        lbl_news_guide.setWordWrap(True)
        news_header.addWidget(lbl_news_guide, 1)

        today_str = datetime.now().strftime("%Y년 %m월 %d일")
        lbl_date_badge = QLabel(f"📅 {today_str}")
        lbl_date_badge.setStyleSheet(
            "background-color: #EFF6FF; color: #1D4ED8; font-weight: bold; "
            "font-size: 12px; padding: 3px 8px; border-radius: 10px; border: 1px solid #BFDBFE;"
        )
        lbl_date_badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        news_header.addWidget(lbl_date_badge, 0, Qt.AlignmentFlag.AlignTop)
        tab_news_layout.addLayout(news_header)

        # 연합뉴스 실시간 부동산 핫이슈 바 (원클릭 글감 선택)
        yonhap_frame = QFrame()
        yonhap_frame.setStyleSheet(
            "background-color: #F0FDF4; border: 1.5px solid #BBF7D0; border-radius: 8px; padding: 6px 8px;"
        )
        yonhap_layout = QVBoxLayout(yonhap_frame)
        yonhap_layout.setContentsMargins(4, 4, 4, 4)
        yonhap_layout.setSpacing(5)

        yonhap_title_bar = QHBoxLayout()
        lbl_yonhap_badge = QLabel("🔥 연합뉴스 실시간 속보 (원클릭 글감)")
        lbl_yonhap_badge.setStyleSheet("font-weight: bold; color: #166534; font-size: 13px;")
        yonhap_title_bar.addWidget(lbl_yonhap_badge)
        yonhap_title_bar.addStretch()

        self.btn_clear_yonhap = QPushButton("✕ 선택 취소")
        self.btn_clear_yonhap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_yonhap.setStyleSheet("padding: 2px 8px; font-size: 12px; background: #FFFFFF; color: #64748B; border: 1px solid #CBD5E1;")
        self.btn_clear_yonhap.setToolTip("선택한 연합뉴스 주제를 취소하고 입력창을 비웁니다.")
        self.btn_clear_yonhap.clicked.connect(self.on_clear_yonhap_news)
        yonhap_title_bar.addWidget(self.btn_clear_yonhap)

        self.btn_refresh_yonhap = QPushButton("🔄 새로고침")
        self.btn_refresh_yonhap.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh_yonhap.setStyleSheet("padding: 2px 8px; font-size: 12px; background: #FFFFFF; color: #166534; border: 1px solid #86EFAC;")
        self.btn_refresh_yonhap.clicked.connect(self.load_yonhap_news)
        yonhap_title_bar.addWidget(self.btn_refresh_yonhap)
        yonhap_layout.addLayout(yonhap_title_bar)

        self.combo_yonhap_news = QComboBox()
        self.combo_yonhap_news.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.combo_yonhap_news.setStyleSheet("font-size: 13px; color: #1E293B; background: #FFFFFF; padding: 4px 8px;")
        self.combo_yonhap_news.addItem("⏳ 연합뉴스 실시간 부동산 속보를 불러오는 중...")
        self.combo_yonhap_news.currentIndexChanged.connect(self.on_yonhap_news_selected)
        yonhap_layout.addWidget(self.combo_yonhap_news)

        tab_news_layout.addWidget(yonhap_frame)

        self.edit_news_topic = QTextEdit()
        cur_year = datetime.now().year
        self.edit_news_topic.setPlaceholderText(
            f"예시:\n"
            f"- {cur_year}년 신혼부부/다자녀 특별공급 청약 제도 개편 핵심 정리\n"
            f"- 최근 서울 및 수도권 아파트 실거래가 및 전세 시장 동향\n"
            f"- 우리 동네(OO동) 재건축 추진 현황 및 상가 입지 분석"
        )
        self.edit_news_topic.setFixedHeight(75)
        tab_news_layout.addWidget(self.edit_news_topic)

        # 자료 최신성 및 검색 제어 바 (줄바꿈 방지 2단 구성)
        freshness_layout = QVBoxLayout()
        freshness_layout.setSpacing(4)

        row1 = QHBoxLayout()
        lbl_freshness = QLabel("🔍 자료 최신성:")
        lbl_freshness.setStyleSheet("font-weight: bold; color: #334155; font-size: 13px;")
        row1.addWidget(lbl_freshness)

        self.combo_freshness = QComboBox()
        self.combo_freshness.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_freshness.addItems([
            "⚡ 최근 3개월 이내 최신 자료 (추천)",
            "🔥 초밀착 최신 (최근 1주일~1개월 보도)",
            f"📆 올해({cur_year}년) 최신 발표/정책",
            "🌐 기간 제한 없이 검색"
        ])
        current_freshness = self.config.get("search_freshness", "recent_3m")
        freshness_idx_map = {"recent_3m": 0, "latest": 1, "this_year": 2, "all": 3}
        self.combo_freshness.setCurrentIndex(freshness_idx_map.get(current_freshness, 0))
        row1.addWidget(self.combo_freshness)
        freshness_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.chk_source_date = QCheckBox("발표 시점/일자 본문 표기")
        self.chk_source_date.setChecked(self.config.get("include_source_date", True))
        self.chk_source_date.setToolTip("본문에 '2026년 최근 발표 기준', '최근 보도에 따르면' 등 최신 시점을 명시하여 신뢰도를 높입니다.")
        self.chk_source_date.setStyleSheet(MUTED_TEXT_STYLE)
        row2.addWidget(self.chk_source_date)

        lbl_news_freshness_notice = QLabel("※ 1~2년 전 과거 기사 엄격 배제")
        lbl_news_freshness_notice.setStyleSheet("color: #059669; font-size: 12px;")
        lbl_news_freshness_notice.setWordWrap(True)
        row2.addWidget(lbl_news_freshness_notice)
        row2.addStretch()
        freshness_layout.addLayout(row2)

        tab_news_layout.addLayout(freshness_layout)

        lbl_copyright_notice = QLabel("🛡️ [저작권 안심] 단순 기사 복사 없이 공인중개사의 독창적인 분석 및 실무 대응 전략(80% 이상)으로 안전하게 재창작됩니다.")
        lbl_copyright_notice.setStyleSheet("color: #2563EB; font-size: 12px; font-weight: 600; line-height: 1.4;")
        lbl_copyright_notice.setWordWrap(True)
        lbl_copyright_notice.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        tab_news_layout.addWidget(lbl_copyright_notice)

        self.stacked_input.addWidget(tab_news)

        # ====================================================
        # 모드 3: 📁 문서/자료 분석 모드 (PDF, HWP, DOCX 등)
        # ====================================================
        tab_file = QWidget()
        tab_file_layout = QVBoxLayout(tab_file)
        tab_file_layout.setContentsMargins(0, 4, 0, 0)
        tab_file_layout.setSpacing(6)

        lbl_file_guide = QLabel("📁 보도자료, 분양 공고문, HWP, PDF, 워드, 텍스트 파일을 분석하여 포스팅합니다.")
        lbl_file_guide.setStyleSheet(MUTED_TEXT_STYLE)
        lbl_file_guide.setWordWrap(True)
        tab_file_layout.addWidget(lbl_file_guide)

        file_pick_layout = QHBoxLayout()
        self.lbl_selected_file = QLabel("선택된 파일 없음")
        self.lbl_selected_file.setStyleSheet("color: #64748B; background: #F1F5F9; padding: 4px 8px; border-radius: 6px;")
        file_pick_layout.addWidget(self.lbl_selected_file, 1)

        btn_select_file = QPushButton("📂 문서 파일 선택")
        btn_select_file.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select_file.clicked.connect(self.on_select_doc_file)
        file_pick_layout.addWidget(btn_select_file)
        tab_file_layout.addLayout(file_pick_layout)

        self.edit_file_topic = QLineEdit()
        self.edit_file_topic.setPlaceholderText("강조하고 싶은 내용이나 추가 메모 (선택사항)")
        tab_file_layout.addWidget(self.edit_file_topic)
        tab_file_layout.addStretch()

        self.stacked_input.addWidget(tab_file)

        # 드롭다운 변경 시 스택 전환 연결
        self.combo_input_mode.currentIndexChanged.connect(self.stacked_input.setCurrentIndex)
        layout_step1.addWidget(self.stacked_input)
        layout.addWidget(card_step1)

        # ----------------------------------------------------
        # [2단계] 글 말투(톤앤매너) 고르기 카드 (2x2 그리드 컴팩트 배치)
        # ----------------------------------------------------
        card_step2 = QFrame()
        card_step2.setObjectName("CardFrame")
        layout_step2 = QVBoxLayout(card_step2)
        layout_step2.setContentsMargins(10, 8, 10, 8)
        layout_step2.setSpacing(6)

        header_step2 = QHBoxLayout()
        badge2 = QLabel("2단계")
        badge2.setObjectName("StepBadge")
        title2 = QLabel("글 말투 (톤앤매너) 고르기")
        title2.setObjectName("StepTitle")
        header_step2.addWidget(badge2)
        header_step2.addWidget(title2)
        header_step2.addStretch()

        # 이모티콘 밀도를 헤더 우측에 인라인 배치하여 세로 공간 절약
        lbl_density = QLabel("이모티콘:")
        lbl_density.setStyleSheet("font-size: 13px; color: #64748B;")
        header_step2.addWidget(lbl_density)
        self.combo_density = QComboBox()
        self.combo_density.addItems(["적당히 보기 좋게 (추천)", "풍성하고 활기차게", "최소한으로 깔끔하게"])
        self.combo_density.setStyleSheet("padding: 2px 6px; font-size: 13px;")
        header_step2.addWidget(self.combo_density)

        layout_step2.addLayout(header_step2)

        self.tone_group = QButtonGroup(self)
        self.radio_neighbor = QRadioButton("☕ 다정한 이웃 (해요체)")
        self.radio_neighbor.setToolTip("이웃 주민에게 이야기하듯 따뜻하고 편안한 해요체")
        self.radio_expert = QRadioButton("🏢 신뢰 전문가 (브리핑)")
        self.radio_expert.setToolTip("정확한 팩트와 수치, 정책 분석 중심의 품격 있는 브리핑체")
        self.radio_coach = QRadioButton("📈 부동산 코칭 (인사이트)")
        self.radio_coach.setToolTip("매수자/투자자 관점에서 기회와 주의점, 실전 인사이트를 짚어주는 멘토형")
        self.radio_summary = QRadioButton("⚡ 3분 요약 (카드뉴스)")
        self.radio_summary.setToolTip("바쁜 현대인을 위해 한눈에 쏙 들어오는 카드뉴스형 요점 요약")

        self.radio_neighbor.setChecked(True)
        self.tone_group.addButton(self.radio_neighbor, 0)
        self.tone_group.addButton(self.radio_expert, 1)
        self.tone_group.addButton(self.radio_coach, 2)
        self.tone_group.addButton(self.radio_summary, 3)

        tone_grid = QGridLayout()
        tone_grid.setHorizontalSpacing(10)
        tone_grid.setVerticalSpacing(4)
        tone_grid.addWidget(self.radio_neighbor, 0, 0)
        tone_grid.addWidget(self.radio_expert, 0, 1)
        tone_grid.addWidget(self.radio_coach, 1, 0)
        tone_grid.addWidget(self.radio_summary, 1, 1)
        tone_grid.setColumnStretch(0, 1)
        tone_grid.setColumnStretch(1, 1)
        layout_step2.addLayout(tone_grid)

        layout.addWidget(card_step2)
        layout.addStretch()

        scroll_area.setWidget(scroll_content)
        outer_layout.addWidget(scroll_area, 1)

        # ----------------------------------------------------
        # [3단계] 하단 고정 액션 카드 (화면 하단에 항상 고정 노출)
        # ----------------------------------------------------
        card_step3 = QFrame()
        card_step3.setObjectName("CardFrame")
        layout_step3 = QVBoxLayout(card_step3)
        layout_step3.setContentsMargins(10, 8, 10, 8)
        layout_step3.setSpacing(5)

        self.btn_generate = QPushButton("✨ 네이버 블로그 글 만들기 (클릭)")
        self.btn_generate.setObjectName("GenerateButton")
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.clicked.connect(self.on_start_generate)
        layout_step3.addWidget(self.btn_generate)

        # 진행 표시줄
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        layout_step3.addWidget(self.progress_bar)

        self.lbl_loading_status = QLabel("")
        self.lbl_loading_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_loading_status.setStyleSheet("color: #2563EB; font-weight: bold; font-size: 14px;")
        self.lbl_loading_status.setVisible(False)
        layout_step3.addWidget(self.lbl_loading_status)

        outer_layout.addWidget(card_step3, 0)

        return container

    def create_right_result_panel(self) -> QWidget:
        """우측 4단계 결과 미리보기 & 원클릭 복사 영역"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(8)

        card_result = QFrame()
        card_result.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card_result)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(8)

        # 상단 헤더 & 복사 액션 바
        action_header = QHBoxLayout()
        badge4 = QLabel("4단계")
        badge4.setObjectName("StepBadge")
        title4 = QLabel("결과 확인 & 네이버 블로그에 복사")
        title4.setObjectName("StepTitle")
        action_header.addWidget(badge4)
        action_header.addWidget(title4)
        action_header.addStretch()

        # 네이버 블로그 원클릭 복사 버튼 (초록색)
        self.btn_copy_naver = QPushButton("📋 네이버 블로그에 바로 붙여넣기 복사")
        self.btn_copy_naver.setObjectName("NaverCopyButton")
        self.btn_copy_naver.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_naver.clicked.connect(self.on_copy_for_naver)
        action_header.addWidget(self.btn_copy_naver)

        # 고화질 차트 이미지 복사 버튼 (파란색)
        self.btn_copy_chart = QPushButton("📊 차트 복사")
        self.btn_copy_chart.setObjectName("ChartCopyButton")
        self.btn_copy_chart.setToolTip("통계 및 핵심 요약 카드 인포그래픽 이미지를 복사합니다.")
        self.btn_copy_chart.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_chart.clicked.connect(self.on_copy_chart_image)
        action_header.addWidget(self.btn_copy_chart)

        # 정비구역 위치도/지적 약도 복사 버튼 (스카이 블루)
        self.btn_copy_zone_map = QPushButton("🗺️ 구역 지도 복사")
        self.btn_copy_zone_map.setObjectName("ZoneMapCopyButton")
        self.btn_copy_zone_map.setToolTip("해당 재개발 구역/매물 위치도 이미지를 복사하여 에디터에 사진으로 첨부합니다.")
        self.btn_copy_zone_map.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_zone_map.clicked.connect(self.on_copy_zone_map)
        action_header.addWidget(self.btn_copy_zone_map)

        # 국토교통부 토지이음 공식 지도 뷰어 바로가기 버튼 (청록색)
        self.btn_open_eum = QPushButton("🌐 토지이음")
        self.btn_open_eum.setObjectName("EumOpenButton")
        self.btn_open_eum.setToolTip("국토교통부 '토지이음(eum.go.kr)' 공식 정비구역 지도를 웹브라우저로 바로 엽니다.")
        self.btn_open_eum.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_eum.clicked.connect(self.on_open_eum)
        action_header.addWidget(self.btn_open_eum)

        btn_copy_plain = QPushButton("📄 텍스트")
        btn_copy_plain.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy_plain.clicked.connect(self.on_copy_plain_text)
        action_header.addWidget(btn_copy_plain)

        card_layout.addLayout(action_header)

        # 1. 추천 제목 선택 바
        title_box = QFrame()
        title_box.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 4px 8px;")
        title_box_layout = QVBoxLayout(title_box)
        title_box_layout.setSpacing(2)
        title_box_layout.addWidget(QLabel("💡 마음에 드는 제목을 클릭해보세요:"))

        self.combo_titles = QComboBox()
        self.combo_titles.setStyleSheet("font-weight: bold; color: #1E293B; font-size: 15px;")
        self.combo_titles.currentIndexChanged.connect(self.on_title_changed)
        title_box_layout.addWidget(self.combo_titles)
        card_layout.addWidget(title_box)

        # 블로그 발행 가이드 박스 (복사되지 않는 전용 안내 영역)
        self.guide_box = QFrame()
        self.guide_box.setObjectName("GuideBox")
        self.guide_box.setStyleSheet(
            "QFrame#GuideBox {"
            "  background-color: #F0FDF4; border: 1.5px solid #86EFAC; border-radius: 8px; padding: 4px 10px;"
            "}"
        )
        guide_layout = QHBoxLayout(self.guide_box)
        guide_layout.setContentsMargins(6, 4, 6, 4)
        guide_layout.setSpacing(8)

        self.lbl_guide_icon = QLabel("💡")
        self.lbl_guide_icon.setStyleSheet("font-size: 15px;")

        self.lbl_guide_text = QLabel(
            "<b>[블로그 발행 안내]</b> [📋 네이버 블로그 복사]로 본문을 붙여넣은 후, "
            "상단 <b>[📊 차트 복사]</b>와 <b>[🗺️ 구역 지도 복사]</b>를 눌러 본문 플레이스홀더 위치에 사진으로 첨부하세요."
        )
        self.lbl_guide_text.setStyleSheet("color: #166534; font-size: 13px; line-height: 1.4;")
        self.lbl_guide_text.setWordWrap(True)

        guide_layout.addWidget(self.lbl_guide_icon)
        guide_layout.addWidget(self.lbl_guide_text, 1)
        card_layout.addWidget(self.guide_box)

        # 2. 결과 탭 (📱 네이버 블로그 미리보기 / ✏️ 직접 수정하기)
        self.result_tab = QTabWidget()

        # 탭 1: HTML 미리보기 (실제 스마트에디터 스타일)
        self.preview_browser = QTextBrowser()
        self.preview_browser.setOpenExternalLinks(False)
        self.preview_browser.setHtml("""
        <div style='text-align: center; color: #94A3B8; padding: 100px 20px; font-size: 15px;'>
            <h3>👈 좌측에서 매물 사진이나 주제를 넣고<br>[✨ 네이버 블로그 글 만들기] 버튼을 눌러주세요!</h3>
            <p>생성된 글이 실제 네이버 블로그 화면처럼 여기에 깔끔하게 미리보기됩니다.</p>
        </div>
        """)
        self.result_tab.addTab(self.preview_browser, "📱 네이버 블로그 화면 미리보기")

        # 탭 2: 직접 수정하기 에디터
        self.edit_body = QTextEdit()
        self.edit_body.setPlaceholderText("생성된 글 내용이 여기에 표시되며, 자유롭게 직접 수정할 수 있습니다.")
        self.edit_body.textChanged.connect(self.on_editor_text_changed)
        self.result_tab.addTab(self.edit_body, "✏️ 본문 직접 수정하기")

        card_layout.addWidget(self.result_tab, 1)

        # 3. 해시태그 바
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("🏷️ 추천 해시태그:"))
        self.edit_tags = QLineEdit()
        self.edit_tags.setPlaceholderText("#부동산 #공인중개사 #매물소개 #월세 #전세 #매매")
        tag_layout.addWidget(self.edit_tags, 1)

        btn_copy_tags = QPushButton("태그 복사")
        btn_copy_tags.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy_tags.clicked.connect(self.on_copy_tags)
        tag_layout.addWidget(btn_copy_tags)

        card_layout.addLayout(tag_layout)
        layout.addWidget(card_result)

        return container

    def on_add_property_photos(self):
        """현장 사진 다중 선택 다이얼로그"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "현장 사진 여러 장 선택 (거실, 주방, 룸, 욕실 등)",
            "",
            "이미지 파일 (*.jpg *.jpeg *.png *.webp);;모든 파일 (*.*)"
        )
        if file_paths:
            for p in file_paths:
                if p not in self.property_photos:
                    self.property_photos.append(p)
            self._update_photo_list_ui()

    def on_clear_property_photos(self):
        """현장 사진 목록 비우기"""
        self.property_photos.clear()
        self._update_photo_list_ui()

    def _update_photo_list_ui(self):
        """사진 목록 위젯 및 카운트 라벨 갱신"""
        self.list_photos.clear()
        for idx, path in enumerate(self.property_photos, 1):
            fname = os.path.basename(path)
            size_kb = os.path.getsize(path) / 1024 if os.path.exists(path) else 0
            item = QListWidgetItem(f"📸 [사진 {idx}] {fname} ({size_kb:.0f} KB)")
            self.list_photos.addItem(item)

        count = len(self.property_photos)
        self.lbl_photo_count.setText(f"📷 등록된 현장 사진: {count}장 (순서대로 분석됨)")
        if count > 0:
            self.lbl_photo_count.setStyleSheet("font-weight: bold; color: #166534; font-size: 14px;")
        else:
            self.lbl_photo_count.setStyleSheet("font-weight: bold; color: #2563EB; font-size: 14px;")

    def on_select_doc_file(self):
        """문서/자료 첨부 파일 선택 다이얼로그"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "분석할 문서 자료 선택",
            "",
            "모든 지원 파일 (*.pdf *.docx *.hwpx *.hwp *.txt *.png *.jpg *.jpeg);;PDF 파일 (*.pdf);;한글 문서 (*.hwpx *.hwp);;워드 문서 (*.docx);;텍스트 (*.txt)"
        )
        if file_path:
            self.selected_doc_files = [file_path]
            filename = os.path.basename(file_path)
            self.lbl_selected_file.setText(f"📄 {filename}")
            self.lbl_selected_file.setStyleSheet("color: #1E293B; background: #DCFCE7; font-weight: bold; padding: 6px 10px; border-radius: 6px;")

    def get_selected_tone_key(self) -> str:
        idx = self.tone_group.checkedId()
        mapping = {0: "neighbor", 1: "expert", 2: "coach", 3: "summary"}
        return mapping.get(idx, "neighbor")

    def _get_property_input_payload(self):
        """매물 모드 입력값 검증 및 페이로드 생성"""
        deal_type = self.combo_deal_type.currentText()
        prop_type = self.combo_prop_type.currentText()
        location = self.edit_prop_location.text().strip()
        price = self.edit_prop_price.text().strip()
        area_structure = self.edit_prop_area.text().strip()
        features = self.edit_prop_features.text().strip()
        memo = self.edit_prop_memo.text().strip()

        if not location and not price and not self.property_photos:
            QMessageBox.warning(
                self,
                "매물 정보 입력 필요",
                "매물 위치/이름, 가격 조건 또는 현장 사진을 최소 1개 이상 입력/등록해주세요!"
            )
            self.edit_prop_location.setFocus()
            return None

        property_info = {
            "deal_type": deal_type,
            "property_type": prop_type,
            "location": location or "위치 문의 요망",
            "price": price or "가격 문의 요망",
            "area_structure": area_structure or "상세 면적/구조 문의 요망",
            "features": features,
            "memo": memo
        }
        self.config["enable_local_search"] = self.chk_prop_local_search.isChecked()
        return {
            "mode": "property",
            "topic": memo,
            "file_paths": list(self.property_photos),
            "property_info": property_info
        }

    def load_yonhap_news(self):
        """연합뉴스 경제 RSS에서 부동산 속보 비동기 로딩 시작"""
        if hasattr(self, "combo_yonhap_news"):
            self.combo_yonhap_news.blockSignals(True)
            self.combo_yonhap_news.clear()
            self.combo_yonhap_news.addItem("⏳ 연합뉴스 실시간 부동산 속보를 불러오는 중...")
            self.combo_yonhap_news.blockSignals(False)
        self.yonhap_thread = YonhapNewsLoadThread()
        self.yonhap_thread.news_loaded_signal.connect(self.on_yonhap_news_loaded)
        self.yonhap_thread.start()

    def on_yonhap_news_loaded(self, articles: list):
        """연합뉴스 속보 수집 완료 시 드롭다운 갱신"""
        self.yonhap_articles = articles
        if not hasattr(self, "combo_yonhap_news"):
            return
        self.combo_yonhap_news.blockSignals(True)
        self.combo_yonhap_news.clear()
        if articles:
            self.combo_yonhap_news.addItem("👇 [클릭] 오늘자 연합뉴스 부동산 핫이슈 글감 선택...")
            for art in articles:
                date_str = art.get("pub_date", "")
                title = art.get("title", "")
                prefix = f"[{date_str}] " if date_str else ""
                self.combo_yonhap_news.addItem(f"{prefix}{title}")
        else:
            self.combo_yonhap_news.addItem("최신 부동산 속보를 불러오지 못했습니다 (네트워크 확인)")
        self.combo_yonhap_news.blockSignals(False)

    def on_yonhap_news_selected(self, index: int):
        """연합뉴스 속보 항목 선택 시 글감 주제창에 자동 입력 (원클릭 세팅)"""
        if index <= 0 or not self.yonhap_articles:
            return
        art_idx = index - 1
        if 0 <= art_idx < len(self.yonhap_articles):
            art = self.yonhap_articles[art_idx]
            title = art.get("title", "")
            desc = art.get("description", "")
            date = art.get("pub_date", "")
            source = art.get("source", "연합뉴스")

            # 기사 단순 복사가 아닌 핵심 팩트 및 주제 브리핑 구조로 주입
            content = f"[{source} 속보] {title}"
            if desc:
                content += f"\n- 주요 보도 팩트: {desc}"
            if date:
                content += f"\n- 발표/보도 시점: {date}"
            self.edit_news_topic.setPlainText(content)

    def on_clear_yonhap_news(self):
        """선택된 연합뉴스 속보를 취소하고 주제 입력창 초기화"""
        if hasattr(self, "combo_yonhap_news"):
            self.combo_yonhap_news.blockSignals(True)
            self.combo_yonhap_news.setCurrentIndex(0)
            self.combo_yonhap_news.blockSignals(False)
        self.edit_news_topic.clear()
        self.edit_news_topic.setFocus()

    def _get_news_input_payload(self):
        """뉴스 기사 모드 입력값 검증 및 페이로드 생성"""
        topic = self.edit_news_topic.toPlainText().strip()
        if not topic:
            QMessageBox.warning(self, "주제 입력 필요", "작성하고 싶은 부동산 소식이나 주제를 간단히 입력해주세요!")
            self.edit_news_topic.setFocus()
            return None

        freshness_map = {0: "recent_3m", 1: "latest", 2: "this_year", 3: "all"}
        selected_freshness = freshness_map.get(self.combo_freshness.currentIndex(), "recent_3m")
        self.config["search_freshness"] = selected_freshness
        self.config["include_source_date"] = self.chk_source_date.isChecked()

        return {
            "mode": "news",
            "topic": topic,
            "file_paths": [],
            "property_info": None
        }

    def _get_file_input_payload(self):
        """문서 파일 모드 입력값 검증 및 페이로드 생성"""
        file_paths = list(self.selected_doc_files)
        if not file_paths:
            QMessageBox.warning(self, "파일 선택 필요", "분석할 문서 파일(PDF, HWP, DOCX 등)을 먼저 선택해주세요!")
            return None
        return {
            "mode": "file",
            "topic": self.edit_file_topic.text().strip(),
            "file_paths": file_paths,
            "property_info": None
        }

    def _get_loading_message(self, mode: str, photo_count: int) -> str:
        """모드별 진행 상태 메시지 반환"""
        if mode == "property":
            if self.config.get("enable_local_search", False):
                return "🏠 현장 사진과 주변 최신 개발 호재/시세를 실시간 검색하여 룸투어 글을 작성하고 있습니다..."
            if photo_count > 0:
                return f"🏠 현장 사진 {photo_count}장과 매물 정보를 정밀 분석하여 룸투어 글을 작성하고 있습니다..."
            return "🏠 매물 스펙을 바탕으로 네이버 블로그 추천 매물 포스팅을 작성하고 있습니다..."
        if mode == "news":
            return "🔍 최신 인터넷 기사를 실시간 검색하고 최신 정보를 분석하여 블로그 글을 작성하고 있습니다..."
        return "📄 첨부자료 내용을 정밀 분석하여 블로그 글을 작성하고 있습니다..."

    def on_start_generate(self):
        """글 생성 시작"""
        if not self.config.get("gemini_api_key", "").strip():
            self.open_settings_dialog()
            if not self.config.get("gemini_api_key", "").strip():
                QMessageBox.warning(self, "API 키 필요", "글을 생성하려면 Gemini API 키를 먼저 입력해야 합니다.")
                return

        current_mode_idx = self.combo_input_mode.currentIndex()
        if current_mode_idx == 0:
            payload = self._get_property_input_payload()
        elif current_mode_idx == 1:
            payload = self._get_news_input_payload()
        else:
            payload = self._get_file_input_payload()

        if not payload:
            return

        tone_key = self.get_selected_tone_key()
        density_idx = self.combo_density.currentIndex()
        density_map = {0: "normal", 1: "high", 2: "low"}
        self.config["emoji_density"] = density_map.get(density_idx, "normal")
        save_config(self.config)

        mode = payload["mode"]
        file_paths = payload["file_paths"]

        self.btn_generate.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_loading_status.setVisible(True)
        self.lbl_loading_status.setText(self._get_loading_message(mode, len(file_paths)))

        self.worker = BlogGenerationThread(
            service=self.gemini_service,
            mode=mode,
            topic=payload["topic"],
            file_paths=file_paths,
            property_info=payload["property_info"],
            tone_key=tone_key,
            config=self.config
        )
        self.worker.finished_signal.connect(self.on_generation_finished)
        self.worker.error_signal.connect(self.on_generation_error)
        self.worker.start()

    def on_generation_finished(self, result: dict):
        """글 생성 완료 처리"""
        self.btn_generate.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_loading_status.setVisible(False)
        self.current_result = result

        # 1. 제목 목록 갱신
        self.combo_titles.blockSignals(True)
        self.combo_titles.clear()
        for t in result["titles"]:
            clean_t = strip_leading_emojis(t).strip()
            self.combo_titles.addItem(f"📌 {clean_t}")
        self.combo_titles.blockSignals(False)

        # 2. 본문 에디터 반영
        self.edit_body.blockSignals(True)
        self.edit_body.setPlainText(result["body"])
        self.edit_body.blockSignals(False)

        # 3. 해시태그 반영
        self.edit_tags.setText(" ".join(result["tags"]))

        self._current_dashboard_data = result.get("dashboard_data")
        self._current_map_data = result.get("map_data")

        # 3.6. 상단 가이드 영역에 주제별 맞춤 발행 팁 업데이트 (복사되지 않는 전용 영역)
        if self._current_map_data and self._current_map_data.get("need_map"):
            map_q = self._current_map_data.get("map_query") or self._current_map_data.get("map_title", "")
            map_tip = f" 네이버 블로그 지도 첨부에서 <b>'{map_q}'</b>를 검색하여 등록하시면 상위 노출에 더욱 효과적입니다." if map_q and map_q != "없음" else ""
            self.lbl_guide_text.setText(
                "<b>[블로그 발행 안내]</b> [📋 네이버 블로그 복사]로 본문을 붙여넣은 후, "
                "상단 <b>[📊 차트 복사]</b> 및 <b>[🗺️ 구역 지도 복사]</b> 버튼을 눌러 원하는 위치에 [Ctrl+V]로 첨부하세요."
                + map_tip
            )
        else:
            self.lbl_guide_text.setText(
                "<b>[블로그 발행 안내]</b> [📋 네이버 블로그 복사]로 본문을 붙여넣은 후, "
                "상단 <b>[📊 차트 복사]</b> 버튼을 눌러 고화질 요약 카드를 본문 원하는 위치에 [Ctrl+V]로 첨부하세요. (거시 정책 주제로 지도는 자동 생략되었습니다.)"
            )

        # 4. 차트 및 구역 지도 비주얼 생성 및 바인딩
        self.generate_preview_visuals(force_refresh=True)

        # 5. 스마트에디터 HTML 미리보기 업데이트
        self.update_preview()

        # 결과 탭으로 포커스
        self.result_tab.setCurrentIndex(0)

        QMessageBox.information(self, "작성 완료! 🎉", "네이버 블로그 글이 멋지게 완성되었습니다!\n'네이버 블로그에 바로 붙여넣기 복사' 버튼을 눌러 블로그에 붙여넣어보세요.")

    def on_generation_error(self, error_msg: str):
        """생성 오류 처리 및 원인별 친절한 해결 가이드 제공"""
        self.btn_generate.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_loading_status.setVisible(False)

        err_lower = error_msg.lower()
        if "429" in err_lower or "resource_exhausted" in err_lower or "quota" in err_lower or "rate_limit" in err_lower:
            guide = (
                "⚠️ [Google Gemini API 사용량/할당량(Quota) 초과 안내]\n"
                "Google Gemini 무료 티어의 분당 요청 한도(RPM) 또는 일일 사용량에 도달했습니다.\n\n"
                "해결 방법:\n"
                "1. 1~2분 정도 잠시 기다린 후 다시 생성 버튼을 눌러보세요.\n"
                "2. 상단 우측 [⚙️ 환경 설정]에서 사용 모델을 'gemini-3.5-flash-lite' 또는 'gemini-3.1-flash-lite'로 변경해보세요.\n"
                "3. Google AI Studio (https://aistudio.google.com/)에서 새 API 키를 발급받아 교체하시면 즉시 정상 이용이 가능합니다."
            )
        elif "401" in err_lower or "unauthenticated" in err_lower or "access_token" in err_lower:
            guide = (
                "⚠️ [API 키 인증 오류 안내]\n"
                "입력하신 Gemini API 키 인증에 실패했습니다.\n\n"
                "해결 방법:\n"
                "1. 상단 우측 [⚙️ 환경 설정]을 클릭하세요.\n"
                "2. Google AI Studio (https://aistudio.google.com/)에서 발급받은 올바른 Gemini API 키(AIzaSy... 형식)를 입력하고 저장해주세요."
            )
        elif "404" in err_lower or "not_found" in err_lower or "no longer available" in err_lower:
            guide = (
                "⚠️ [AI 모델 지원 종료 안내]\n"
                "요청하신 모델 버전이 Google에서 만료되었습니다.\n\n"
                "해결 방법:\n"
                "1. 상단 우측 [⚙️ 환경 설정]을 클릭하세요.\n"
                "2. 사용 모델을 'gemini-3.6-flash (기본 추천)' 또는 'gemini-3.5-flash'로 변경해주세요."
            )
        else:
            guide = "※ 인터넷 연결이 정상인지 확인 후 다시 시도해주세요."

        QMessageBox.critical(
            self,
            "생성 중 오류 발생",
            f"글을 생성하는 동안 문제가 발생했습니다:\n\n{error_msg}\n\n{guide}"
        )

    def _create_current_chart(self) -> QImage:
        """현재 본문 및 AI 자동 수집 지표 기반 인포그래픽 대시보드 이미지 생성"""
        body_text = self.edit_body.toPlainText().strip()
        if not body_text:
            return None
        current_title = strip_leading_emojis(self.combo_titles.currentText()).strip() or "부동산 핵심 체크포인트"
        office_name = self.config.get("office_name", "").strip()

        # 1. AI가 포스팅 생성 시 실시간 자동 수집/추출한 핵심 대시보드 데이터 최우선 활용
        if self._current_dashboard_data:
            zone_data = dict(self._current_dashboard_data)
            zone_name = zone_data.get("target_name") or self._get_current_zone_or_location()
            category_label = zone_data.get("category", "부동산 핵심 지표 분석")
            return render_infographic_card(
                current_title,
                items=[],
                office_name=office_name,
                card_category=category_label,
                zone_name=zone_name,
                zone_data=zone_data
            )

        # 2. AI 데이터가 없는 경우 (직접 텍스트 편집 또는 내장 DB 매칭)
        zone_query = self._get_current_zone_or_location()
        zone_data = get_zone_data(zone_query) if zone_query else None

        mode = "property" if self.stacked_input.currentIndex() == 0 else "news"
        prop_info = None
        if mode == "property":
            prop_info = {
                "deal_type": self.combo_deal_type.currentText(),
                "property_type": self.combo_prop_type.currentText(),
                "location": self.edit_prop_location.text().strip(),
                "price": self.edit_prop_price.text().strip(),
                "area_structure": self.edit_prop_area.text().strip(),
                "features": self.edit_prop_features.text().strip(),
            }

        items = extract_summary_items(body_text, mode=mode, property_info=prop_info)
        category_label = "매물 핵심 Check Point" if mode == "property" else "부동산 정책/이슈 핵심 요약"
        return render_infographic_card(
            current_title,
            items=items,
            office_name=office_name,
            card_category=category_label,
            zone_name=zone_query,
            zone_data=zone_data,
            property_info=prop_info
        )

    def _create_current_zone_map(self) -> QImage:
        """현재 구역/소재지 기반 정비구역 위치도 이미지 생성"""
        office_name = self.config.get("office_name", "").strip()

        # 1. AI 분석 결과에서 지도가 불필요하다고 판단한 경우(거시 정책, 금리, 규제 등) 지도 생성 생략
        if self._current_map_data:
            if not self._current_map_data.get("need_map", True):
                return None
            map_query = self._current_map_data.get("map_query")
            map_title = self._current_map_data.get("map_title")
            if map_query:
                img = generate_zone_map_image(map_query, office_name=office_name, display_title=map_title)
                if img:
                    return img

        # 2. 직접 입력 또는 기존 키워드 기반 탐색
        zone_query = self._get_current_zone_or_location()
        if not zone_query:
            return None
        return generate_zone_map_image(zone_query, office_name=office_name)

    def generate_preview_visuals(self, force_refresh: bool = False):
        """차트 및 구역 지도 이미지를 생성하여 QTextBrowser 리소스에 바인딩"""
        body_text = self.edit_body.toPlainText().strip()
        if not body_text:
            return

        if self._current_chart_img is None or force_refresh:
            self._current_chart_img = self._create_current_chart()
        if self._current_chart_img and not self._current_chart_img.isNull():
            self.preview_browser.document().addResource(
                QTextDocument.ResourceType.ImageResource.value,
                QUrl("chart_preview.png"),
                self._current_chart_img
            )

        if self._current_zone_map_img is None or force_refresh:
            self._current_zone_map_img = self._create_current_zone_map()
        if self._current_zone_map_img and not self._current_zone_map_img.isNull():
            self.preview_browser.document().addResource(
                QTextDocument.ResourceType.ImageResource.value,
                QUrl("zone_map_preview.png"),
                self._current_zone_map_img
            )

    def on_title_changed(self, index: int):
        """제목 선택 변경 시 미리보기 및 비주얼 업데이트"""
        if self._current_chart_img:
            self._current_chart_img = self._create_current_chart()
            if self._current_chart_img:
                self.preview_browser.document().addResource(
                    QTextDocument.ResourceType.ImageResource.value,
                    QUrl("chart_preview.png"),
                    self._current_chart_img
                )
        self.update_preview()

    def on_editor_text_changed(self):
        """에디터 내용 수정 시 실시간 미리보기 동기화"""
        self.update_preview()

    def update_preview(self):
        """스마트에디터 ONE 스타일 HTML 미리보기 갱신"""
        current_title = strip_leading_emojis(self.combo_titles.currentText()).strip()
        if not current_title:
            current_title = "공인중개사 추천 매물 브리핑"
        body_text = self.edit_body.toPlainText()
        tags = [t for t in self.edit_tags.text().split() if t.strip()]

        if body_text.strip() and (self._current_chart_img is None or self._current_zone_map_img is None):
            self.generate_preview_visuals()

        has_chart = self._current_chart_img is not None and not self._current_chart_img.isNull()
        has_zone_map = self._current_zone_map_img is not None and not self._current_zone_map_img.isNull()

        preview_html = generate_blog_preview_html(
            current_title, body_text, tags,
            has_chart=has_chart, has_zone_map=has_zone_map
        )
        self.preview_browser.setHtml(preview_html)

    def on_copy_for_naver(self):
        """
        네이버 스마트에디터 ONE에 맞춘 리치텍스트/HTML + 플레인 텍스트 클립보드 복사
        (플레이스홀더를 제외한 블로그 무관 안내문구 자동 정제)
        """
        current_title = strip_leading_emojis(self.combo_titles.currentText()).strip()
        body_text = clean_body_instructions(self.edit_body.toPlainText())
        tags_text = self.edit_tags.text()

        if not body_text:
            QMessageBox.warning(self, "알림", "복사할 내용이 없습니다. 먼저 글을 생성해주세요.")
            return

        is_card_news = is_card_news_text(body_text)

        if is_card_news:
            body_html = render_card_news_blocks(
                body_text,
                has_chart=bool(self._current_chart_img),
                has_zone_map=bool(self._current_zone_map_img),
                for_clipboard=True
            )
        else:
            import markdown
            # 스마트에디터에 깔끔하게 붙여넣어지는 심플 HTML 구성
            body_html = markdown.markdown(body_text, extensions=['extra', 'nl2br', 'tables'])

            # 스마트에디터 ONE 표(Table) 맞춤형 인라인 스타일 보강 (깨짐 방지 및 세련된 테두리/헤더)
            body_html = body_html.replace('<table>', '<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; background-color: #FFFFFF; border: 1px solid #CBD5E1;">')
            body_html = body_html.replace('<th>', '<th style="background-color: #F1F5F9; color: #1E293B; font-weight: bold; padding: 10px 14px; border: 1px solid #CBD5E1; text-align: center;">')
            body_html = body_html.replace('<td>', '<td style="padding: 10px 14px; border: 1px solid #CBD5E1; color: #334155;">')
        
        full_html = f"""
        <div style="font-family: 'Malgun Gothic', '맑은 고딕', sans-serif; line-height: 1.85; font-size: 15px; color: #222222;">
            <h2 style="font-size: 22px; font-weight: bold; color: #111111; margin-bottom: 20px;">{current_title}</h2>
            {body_html}
            <br><br>
            <p style="color: #666666; font-size: 13px;">{tags_text}</p>
        </div>
        """

        full_plain = f"[{current_title}]\n\n{body_text}\n\n{tags_text}"

        mime = QMimeData()
        mime.setHtml(full_html)
        mime.setText(full_plain)

        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime, QClipboard.Mode.Clipboard)

        msg = (
            "네이버 블로그 카드뉴스 맞춤 서식(슬라이드형 카드 글상자 포함)으로 복사되었습니다! ⚡\n\n"
            "네이버 블로그 스마트에디터 화면에서 [Ctrl + V] 로 붙여넣으시면 각 슬라이드가 깔끔한 카드 박스 서식으로 들어갑니다."
            if is_card_news else
            "네이버 블로그 맞춤 서식(표/서식 포함)으로 복사되었습니다!\n\n"
            "네이버 블로그 스마트에디터 화면에서 [Ctrl + V] 로 붙여넣으시면 제목, 본문, 비교표 서식이 그대로 들어갑니다."
        )

        QMessageBox.information(
            self,
            "복사 완료! 📋",
            msg
        )

    def on_copy_chart_image(self):
        """본문 내용과 통계/스펙을 기반으로 고해상도 인포그래픽 카드 이미지를 생성하여 클립보드에 복사"""
        img = self._current_chart_img or self._create_current_chart()
        if img is None or img.isNull():
            QMessageBox.warning(self, "알림", "복사할 내용이 없습니다. 먼저 블로그 글을 생성해주세요.")
            return
        self._current_chart_img = img

        if copy_chart_to_clipboard(img):
            QMessageBox.information(
                self,
                "차트 복사 완료! 📊",
                "고화질 인포그래픽 차트 이미지가 클립보드에 복사되었습니다!\n\n"
                "네이버 블로그 스마트에디터에서 이미지를 넣고 싶은 위치에 커서를 두고 [Ctrl + V] 로 붙여넣으시면 고해상도 사진으로 바로 첨부됩니다."
            )
        else:
            QMessageBox.warning(self, "오류", "차트 이미지를 생성하지 못했습니다.")

    def on_copy_plain_text(self):
        """일반 텍스트 복사 (플레이스홀더 제외 안내문구 자동 정제)"""
        current_title = strip_leading_emojis(self.combo_titles.currentText()).strip()
        body_text = clean_body_instructions(self.edit_body.toPlainText())
        tags_text = self.edit_tags.text()

        if not body_text:
            QMessageBox.warning(self, "알림", "복사할 내용이 없습니다.")
            return

        full_plain = f"[{current_title}]\n\n{body_text}\n\n{tags_text}"
        QApplication.clipboard().setText(full_plain)
        QMessageBox.information(self, "복사 완료", "일반 텍스트가 클립보드에 복사되었습니다.")

    def on_copy_tags(self):
        """해시태그만 복사"""
        tags_text = self.edit_tags.text().strip()
        if not tags_text:
            QMessageBox.warning(self, "알림", "복사할 해시태그가 없습니다.")
            return
        QApplication.clipboard().setText(tags_text)
        QMessageBox.information(self, "복사 완료", "해시태그가 클립보드에 복사되었습니다.")

    def _get_mode_location_candidate(self, mode_idx: int) -> str:
        """현재 UI 입력 모드에 따른 위치/주제 텍스트 후보 반환"""
        if mode_idx == 0:
            return self.edit_prop_location.text().strip()
        if mode_idx == 1:
            return self.edit_news_topic.toPlainText().strip()
        if mode_idx == 2:
            return self.edit_file_topic.text().strip()
        return ""

    def _get_current_zone_or_location(self) -> str:
        """현재 입력 모드나 AI 메타데이터에서 구역명 또는 소재지 위치 추출"""
        if self._current_map_data and self._current_map_data.get("map_query"):
            return self._current_map_data["map_query"]

        if self._current_dashboard_data and self._current_dashboard_data.get("target_name"):
            found = extract_zone_keyword(self._current_dashboard_data["target_name"])
            if found:
                return found

        mode_idx = self.stacked_input.currentIndex()
        cand = self._get_mode_location_candidate(mode_idx)
        if mode_idx == 0 and cand:
            return cand
        if cand:
            found = extract_zone_keyword(cand)
            if found:
                return found

        title = self.combo_titles.currentText()
        return extract_zone_keyword(title) if title else ""



    def on_copy_zone_map(self):
        """정비구역 위치도/지적 약도 이미지를 생성하여 클립보드에 복사"""
        img = self._current_zone_map_img or self._create_current_zone_map()
        if img is None or img.isNull():
            QMessageBox.information(
                self,
                "지도 복사 안내 🗺️",
                "이 포스팅은 거시 경제/금융 정책/세제 등 특정 지리적 위치가 없는 주제입니다.\n\n"
                "대신 핵심 통계와 로드맵이 담긴 상단 [📊 차트 복사] 버튼을 활용해보세요!"
            )
            return
        self._current_zone_map_img = img

        zone_query = self._get_current_zone_or_location() or "정비구역"
        if copy_zone_map_to_clipboard(img):
            QMessageBox.information(
                self,
                "구역 지도 복사 완료! 🗺️",
                f"[{zone_query}] 정비구역 위치도 이미지가 클립보드에 복사되었습니다!\n\n"
                "네이버 블로그 스마트에디터에서 지도를 넣고 싶은 위치에 커서를 두고 [Ctrl + V]를 누르시면 고해상도 구역 지도가 사진으로 바로 첨부됩니다."
            )
        else:
            QMessageBox.warning(self, "오류", "구역 지도 이미지를 생성하지 못했습니다.")

    def on_open_eum(self):
        """국토교통부 토지이음(eum.go.kr) 공식 정비구역 지도 뷰어 팝업 오픈"""
        zone_query = self._get_current_zone_or_location()
        open_eum_viewer(zone_query)
        QMessageBox.information(
            self,
            "토지이음 공식 지도 연결 🌐",
            f"국토교통부 '토지이음(eum.go.kr)' 공식 정비구역 지도 뷰어가 웹브라우저로 열렸습니다!\n\n"
            f"※ 검색어 '{zone_query}'가 클립보드에 자동 복사되었으니, 토지이음 검색창에서 [Ctrl + V] 로 붙여넣어 해당 구역의 법정 정비구역선(빨간선)을 바로 확인하실 수 있습니다."
        )

