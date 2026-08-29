"""
공인중개사 네이버 블로그 글 생성기 메인 윈도우 (PyQt6 기반)
- 초보자도 쉽게 사용하는 1-2-3-4 단계식 직관적 워크플로우
- 🏠 현장 사진 다중 첨부 기반 매물 소개 (매매/전세/월세/분양)
- 📰 최신 인터넷 기사 검색 기반 브리핑
- 📁 보도자료 및 문서(PDF, HWP, DOCX 등) 분석
- 네이버 블로그 스마트에디터 스타일 실시간 미리보기 & 원클릭 복사
"""

import os
import sys
# pyrefly: ignore [missing-import]
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QRadioButton, QButtonGroup,
    QTabWidget, QFileDialog, QMessageBox, QFrame, QSplitter,
    QDialog, QCheckBox, QComboBox, QTextBrowser, QApplication, QProgressBar,
    QListWidget, QListWidgetItem, QAbstractItemView
)
# pyrefly: ignore [missing-import]
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData
# pyrefly: ignore [missing-import]
from PyQt6.QtGui import QFont, QIcon, QClipboard

from config import load_config, save_config
from prompts.blog_templates import TONE_PRESETS
from services.gemini_service import GeminiBlogService
from ui.styles import MAIN_STYLESHEET, generate_blog_preview_html

DEFAULT_MODEL_NAME = "gemini-3.5-flash"
PRO_MODEL_NAME = "gemini-3.5-pro"
FLASH_36_MODEL_NAME = "gemini-3.6-flash"
FLASH_20_MODEL_NAME = "gemini-2.0-flash"


class BlogGenerationThread(QThread):
    """Gemini API 호출을 비동기로 처리하는 백그라운드 스레드"""
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)

    def __init__(
        self,
        service: GeminiBlogService,
        mode: str,
        topic: str = "",
        file_paths: list = None,
        property_info: dict = None,
        tone_key: str = "neighbor",
        config: dict = None
    ):
        super().__init__()
        self.service = service
        self.mode = mode
        self.topic = topic
        self.file_paths = file_paths or []
        self.property_info = property_info
        self.tone_key = tone_key
        self.config = config

    def run(self):
        try:
            result = self.service.generate_blog_post(
                mode=self.mode,
                topic=self.topic,
                file_paths=self.file_paths,
                property_info=self.property_info,
                tone_key=self.tone_key,
                config=self.config
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))


class SettingsDialog(QDialog):
    """간편 설정 창 (API 키 & 중개사무소 정보)"""
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ 프로그램 설정 (API 키 및 사무소 정보)")
        self.setFixedWidth(540)
        self.config = config or {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 1. API 키 섹션
        api_group = QFrame()
        api_group.setObjectName("CardFrame")
        api_layout = QVBoxLayout(api_group)
        
        lbl_api_title = QLabel("🔑 Google Gemini API 키")
        lbl_api_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #1E293B;")
        api_layout.addWidget(lbl_api_title)

        lbl_api_desc = QLabel("무료로 발급받은 Gemini API 키를 입력하세요. (한 번 입력하면 자동 저장됩니다)")
        lbl_api_desc.setStyleSheet("color: #64748B; font-size: 12px;")
        lbl_api_desc.setWordWrap(True)
        api_layout.addWidget(lbl_api_desc)

        self.edit_api_key = QLineEdit()
        self.edit_api_key.setPlaceholderText("AIzaSy... 형식의 API 키를 붙여넣으세요")
        self.edit_api_key.setText(self.config.get("gemini_api_key", ""))
        self.edit_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.edit_api_key)

        # 모델 선택
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("사용 모델:"))
        self.combo_model = QComboBox()
        self.combo_model.addItems([
            f"{DEFAULT_MODEL_NAME} (기본 추천: 3.5 Flash)",
            f"{PRO_MODEL_NAME} (3.5 Pro 정밀 분석)",
            f"{FLASH_36_MODEL_NAME} (최신 3.6 Flash)",
            f"{FLASH_20_MODEL_NAME} (2.0 Flash)"
        ])
        selected_model = self.config.get("selected_model", DEFAULT_MODEL_NAME)
        if "3.5-pro" in selected_model:
            self.combo_model.setCurrentIndex(1)
        elif "3.6" in selected_model:
            self.combo_model.setCurrentIndex(2)
        elif "2.0" in selected_model:
            self.combo_model.setCurrentIndex(3)
        else:
            self.combo_model.setCurrentIndex(0)
        model_layout.addWidget(self.combo_model)
        api_layout.addLayout(model_layout)

        layout.addWidget(api_group)

        # 2. 공인중개사 사무소 서명 정보
        office_group = QFrame()
        office_group.setObjectName("CardFrame")
        office_layout = QVBoxLayout(office_group)

        lbl_office_title = QLabel("🏢 공인중개사 정보 (글 하단에 자동 추가)")
        lbl_office_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #1E293B;")
        office_layout.addWidget(lbl_office_title)

        self.chk_include_office = QCheckBox("블로그 글 끝에 우리 부동산 사무소 정보를 항상 넣기")
        self.chk_include_office.setChecked(self.config.get("include_office_info", True))
        office_layout.addWidget(self.chk_include_office)

        form_grid = QGridLayout()
        form_grid.setSpacing(8)

        form_grid.addWidget(QLabel("사무소 상호:"), 0, 0)
        self.edit_office_name = QLineEdit()
        self.edit_office_name.setPlaceholderText("예: 신우 공인중개사사무소")
        self.edit_office_name.setText(self.config.get("office_name", ""))
        form_grid.addWidget(self.edit_office_name, 0, 1)

        form_grid.addWidget(QLabel("대표자 성명:"), 1, 0)
        self.edit_agent_name = QLineEdit()
        self.edit_agent_name.setPlaceholderText("예: 대표 공인중개사 홍길동")
        self.edit_agent_name.setText(self.config.get("agent_name", ""))
        form_grid.addWidget(self.edit_agent_name, 1, 1)

        form_grid.addWidget(QLabel("연락처/전화:"), 2, 0)
        self.edit_office_phone = QLineEdit()
        self.edit_office_phone.setPlaceholderText("예: 02-1234-5678 / 010-1234-5678")
        self.edit_office_phone.setText(self.config.get("office_phone", ""))
        form_grid.addWidget(self.edit_office_phone, 2, 1)

        form_grid.addWidget(QLabel("사무소 위치:"), 3, 0)
        self.edit_office_location = QLineEdit()
        self.edit_office_location.setPlaceholderText("예: 서울시 강남구 테헤란로 123 (OO역 3번 출구)")
        self.edit_office_location.setText(self.config.get("office_location", ""))
        form_grid.addWidget(self.edit_office_location, 3, 1)

        office_layout.addLayout(form_grid)
        layout.addWidget(office_group)

        # 3. 저장 및 닫기 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("취소")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("💾 저장하기")
        btn_save.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 8px 20px;")
        btn_save.clicked.connect(self.save_and_close)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def save_and_close(self):
        self.config["gemini_api_key"] = self.edit_api_key.text().strip()
        idx = self.combo_model.currentIndex()
        if idx == 1:
            self.config["selected_model"] = PRO_MODEL_NAME
        elif idx == 2:
            self.config["selected_model"] = FLASH_36_MODEL_NAME
        elif idx == 3:
            self.config["selected_model"] = FLASH_20_MODEL_NAME
        else:
            self.config["selected_model"] = DEFAULT_MODEL_NAME
        self.config["include_office_info"] = self.chk_include_office.isChecked()
        self.config["office_name"] = self.edit_office_name.text().strip()
        self.config["agent_name"] = self.edit_agent_name.text().strip()
        self.config["office_phone"] = self.edit_office_phone.text().strip()
        self.config["office_location"] = self.edit_office_location.text().strip()
        
        save_config(self.config)
        self.accept()


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

        self.init_window()
        self.init_ui()
        self.update_api_status_badge()

    def init_window(self):
        self.setWindowTitle("신우 공인중개사 | AI 네이버 블로그 글 생성기")
        self.resize(1320, 890)
        self.setStyleSheet(MAIN_STYLESHEET)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 상단 헤더 바
        header = self.create_header()
        main_layout.addWidget(header)

        # 본문 스플리터 (좌: 입력 및 옵션 48%, 우: 결과 및 미리보기 52%)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setContentsMargins(16, 16, 16, 16)
        splitter.setHandleWidth(10)

        # 좌측: 1-2-3단계 입력 영역
        left_panel = self.create_left_input_panel()
        splitter.addWidget(left_panel)

        # 우측: 4단계 결과 미리보기 & 복사 영역
        right_panel = self.create_right_result_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([560, 740])
        main_layout.addWidget(splitter)

    def create_header(self) -> QWidget:
        """상단 헤더 카드 (로고, 상태, 간편 설정 버튼)"""
        header = QFrame()
        header.setObjectName("HeaderCard")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 12, 20, 12)

        # 좌측 타이틀
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        lbl_title = QLabel('🏢 <span style="color: #1D4ED8; font-weight: 800; font-size: 19px;">신우 공인중개사</span> <span style="color: #CBD5E1; font-weight: 300; font-size: 16px;">|</span> <span style="color: #0F172A; font-weight: 700; font-size: 18px;">AI 네이버 블로그 글 생성기</span>')
        lbl_title.setObjectName("AppTitle")
        lbl_subtitle = QLabel("신우 공인중개사 전용 · 현장 사진 매물 소개부터 부동산 정책/이슈 브리핑까지 원클릭 자동 생성")
        lbl_subtitle.setObjectName("AppSubtitle")
        title_layout.addWidget(lbl_title)
        title_layout.addWidget(lbl_subtitle)
        layout.addLayout(title_layout)

        layout.addStretch()

        # 우측 상태 및 설정 버튼
        self.lbl_api_status = QLabel("🟢 API 연결 완료")
        self.lbl_api_status.setStyleSheet("font-weight: bold; font-size: 12px; padding: 6px 12px; border-radius: 12px; background: #DCFCE7; color: #166534;")
        layout.addWidget(self.lbl_api_status)

        btn_settings = QPushButton("⚙️ 환경 설정 (API 키)")
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_settings.clicked.connect(self.open_settings_dialog)
        layout.addWidget(btn_settings)

        return header

    def update_api_status_badge(self):
        key = self.config.get("gemini_api_key", "").strip()
        if key:
            self.lbl_api_status.setText("🟢 API 키 등록됨")
            self.lbl_api_status.setStyleSheet("font-weight: bold; font-size: 12px; padding: 6px 12px; border-radius: 12px; background: #DCFCE7; color: #166534;")
        else:
            self.lbl_api_status.setText("🟡 API 키 필요 (클릭)")
            self.lbl_api_status.setStyleSheet("font-weight: bold; font-size: 12px; padding: 6px 12px; border-radius: 12px; background: #FEF3C7; color: #92400E; cursor: pointer;")

    def open_settings_dialog(self):
        dlg = SettingsDialog(self, self.config)
        if dlg.exec():
            self.config = load_config()
            self.gemini_service.set_api_key(self.config.get("gemini_api_key", ""))
            self.gemini_service.set_model(self.config.get("selected_model", DEFAULT_MODEL_NAME))
            self.update_api_status_badge()
            QMessageBox.information(self, "완료", "설정이 성공적으로 저장되었습니다.")

    def create_left_input_panel(self) -> QWidget:
        """좌측 1-2-3단계 입력 영역"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(14)

        # ----------------------------------------------------
        # [1단계] 글감 넣기 카드 (3개 탭)
        # ----------------------------------------------------
        card_step1 = QFrame()
        card_step1.setObjectName("CardFrame")
        layout_step1 = QVBoxLayout(card_step1)
        layout_step1.setSpacing(10)

        header_step1 = QHBoxLayout()
        badge1 = QLabel("1단계")
        badge1.setObjectName("StepBadge")
        title1 = QLabel("글감 넣기 (매물 사진 / 뉴스 / 자료 문서)")
        title1.setObjectName("StepTitle")
        header_step1.addWidget(badge1)
        header_step1.addWidget(title1)
        header_step1.addStretch()
        layout_step1.addLayout(header_step1)

        # 3개 탭 위젯
        self.input_tab = QTabWidget()

        # ====================================================
        # 탭 1: 🏠 현장 사진 매물 소개 (신규 전문 매물 탭)
        # ====================================================
        tab_property = QWidget()
        tab_prop_layout = QVBoxLayout(tab_property)
        tab_prop_layout.setContentsMargins(12, 12, 12, 12)
        tab_prop_layout.setSpacing(8)

        # 1) 거래 유형 및 매물 종류 선택
        prop_top_layout = QHBoxLayout()
        prop_top_layout.addWidget(QLabel("거래 형태:"))
        self.combo_deal_type = QComboBox()
        self.combo_deal_type.addItems(["월세 (보증금/월세)", "전세", "매매", "단기임대", "분양/임대", "기타"])
        prop_top_layout.addWidget(self.combo_deal_type)

        prop_top_layout.addWidget(QLabel("매물 종류:"))
        self.combo_prop_type = QComboBox()
        self.combo_prop_type.addItems(["아파트", "오피스텔", "빌라/다세대", "원룸/투룸", "상가/사무실", "단독/다가구", "토지/공장/창고", "기타"])
        prop_top_layout.addWidget(self.combo_prop_type)
        tab_prop_layout.addLayout(prop_top_layout)

        # 2) 매물 기본 정보 입력 그리드
        prop_grid = QGridLayout()
        prop_grid.setSpacing(6)

        prop_grid.addWidget(QLabel("매물 위치/이름:"), 0, 0)
        self.edit_prop_location = QLineEdit()
        self.edit_prop_location.setPlaceholderText("예: 역삼동 신축 오피스텔 (역삼역 도보 3분)")
        prop_grid.addWidget(self.edit_prop_location, 0, 1)

        prop_grid.addWidget(QLabel("가격 조건:"), 1, 0)
        self.edit_prop_price = QLineEdit()
        self.edit_prop_price.setPlaceholderText("예: 보증금 3,000만원 / 월세 150만원 (또는 매매 12억)")
        prop_grid.addWidget(self.edit_prop_price, 1, 1)

        prop_grid.addWidget(QLabel("면적/구조/층수:"), 2, 0)
        self.edit_prop_area = QLineEdit()
        self.edit_prop_area.setPlaceholderText("예: 전용 59㎡(18평) / 방2 화1 / 15층 중 8층 (남향)")
        prop_grid.addWidget(self.edit_prop_area, 2, 1)

        prop_grid.addWidget(QLabel("특장점/옵션:"), 3, 0)
        self.edit_prop_features = QLineEdit()
        self.edit_prop_features.setPlaceholderText("예: 올수리 첫입주, 시스템에어컨/냉장고 풀옵션, 주차가능, 채광굿")
        prop_grid.addWidget(self.edit_prop_features, 3, 1)

        prop_grid.addWidget(QLabel("추가 전달사항:"), 4, 0)
        self.edit_prop_memo = QLineEdit()
        self.edit_prop_memo.setPlaceholderText("예: 즉시입주 협의가능, 신혼부부나 직장인에게 강추")
        prop_grid.addWidget(self.edit_prop_memo, 4, 1)

        tab_prop_layout.addLayout(prop_grid)

        # 3) 현장 사진 다중 첨부 영역
        photo_header = QHBoxLayout()
        self.lbl_photo_count = QLabel("📷 등록된 현장 사진: 0장 (여러 장 선택 가능)")
        self.lbl_photo_count.setStyleSheet("font-weight: bold; color: #2563EB; font-size: 12px;")
        photo_header.addWidget(self.lbl_photo_count)
        photo_header.addStretch()

        btn_add_photos = QPushButton("📸 사진 추가")
        btn_add_photos.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_photos.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold;")
        btn_add_photos.clicked.connect(self.on_add_property_photos)
        photo_header.addWidget(btn_add_photos)

        btn_clear_photos = QPushButton("전체 비우기")
        btn_clear_photos.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_photos.clicked.connect(self.on_clear_property_photos)
        photo_header.addWidget(btn_clear_photos)

        tab_prop_layout.addLayout(photo_header)

        # 사진 파일 목록 리스트 위젯
        self.list_photos = QListWidget()
        self.list_photos.setObjectName("PhotoList")
        self.list_photos.setFixedHeight(75)
        self.list_photos.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tab_prop_layout.addWidget(self.list_photos)

        self.input_tab.addTab(tab_property, "🏠 현장 사진 매물 소개")

        # ====================================================
        # 탭 2: 📰 인터넷 기사 찾아서 쓰기 (기존 기사/이슈 모드)
        # ====================================================
        tab_news = QWidget()
        tab_news_layout = QVBoxLayout(tab_news)
        tab_news_layout.setContentsMargins(12, 12, 12, 12)
        tab_news_layout.setSpacing(6)

        lbl_news_guide = QLabel("💡 작성하고 싶은 부동산 소식/주제를 적어주세요. 인터넷 최신 기사를 알아서 검색해 분석합니다.")
        lbl_news_guide.setStyleSheet("color: #475569; font-size: 12px;")
        lbl_news_guide.setWordWrap(True)
        tab_news_layout.addWidget(lbl_news_guide)

        self.edit_news_topic = QTextEdit()
        self.edit_news_topic.setPlaceholderText("예시:\n- 2026년 신혼부부/다자녀 특별공급 청약 제도 개편 핵심 정리\n- 최근 서울 및 수도권 아파트 실거래가 및 전세 시장 동향\n- 우리 동네(OO동) 재건축 추진 현황 및 상가 입지 분석")
        self.edit_news_topic.setFixedHeight(120)
        tab_news_layout.addWidget(self.edit_news_topic)
        self.input_tab.addTab(tab_news, "📰 부동산 뉴스/정보")

        # ====================================================
        # 탭 3: 📁 문서/자료 분석 모드 (PDF, HWP, DOCX 등)
        # ====================================================
        tab_file = QWidget()
        tab_file_layout = QVBoxLayout(tab_file)
        tab_file_layout.setContentsMargins(12, 12, 12, 12)
        tab_file_layout.setSpacing(6)

        lbl_file_guide = QLabel("📁 보도자료, 분양 공고문, HWP, PDF, 워드, 텍스트 파일을 분석하여 포스팅합니다.")
        lbl_file_guide.setStyleSheet("color: #475569; font-size: 12px;")
        tab_file_layout.addWidget(lbl_file_guide)

        file_pick_layout = QHBoxLayout()
        self.lbl_selected_file = QLabel("선택된 파일 없음")
        self.lbl_selected_file.setStyleSheet("color: #64748B; background: #F1F5F9; padding: 6px 10px; border-radius: 6px;")
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
        self.input_tab.addTab(tab_file, "📁 문서/자료 분석")

        layout_step1.addWidget(self.input_tab)
        layout.addWidget(card_step1)

        # ----------------------------------------------------
        # [2단계] 글 말투(톤앤매너) 고르기 카드
        # ----------------------------------------------------
        card_step2 = QFrame()
        card_step2.setObjectName("CardFrame")
        layout_step2 = QVBoxLayout(card_step2)
        layout_step2.setSpacing(6)

        header_step2 = QHBoxLayout()
        badge2 = QLabel("2단계")
        badge2.setObjectName("StepBadge")
        title2 = QLabel("글 말투 (톤앤매너) 고르기")
        title2.setObjectName("StepTitle")
        header_step2.addWidget(badge2)
        header_step2.addWidget(title2)
        header_step2.addStretch()
        layout_step2.addLayout(header_step2)

        self.tone_group = QButtonGroup(self)
        self.radio_neighbor = QRadioButton("☕ 다정하고 친절한 이웃 말투 (따뜻한 해요체, 편안한 룸투어)")
        self.radio_expert = QRadioButton("🏢 신뢰감 넘치는 부동산 전문가 말투 (명확한 스펙/입지 브리핑)")
        self.radio_coach = QRadioButton("📈 스마트한 부동산 투자 코칭 말투 (매수/임대 실전 인사이트)")
        self.radio_summary = QRadioButton("⚡ 3분 핵심 요약 카드뉴스형 말투 (한눈에 쏙 들어오는 요점 정리)")

        self.radio_neighbor.setChecked(True)
        self.tone_group.addButton(self.radio_neighbor, 0)
        self.tone_group.addButton(self.radio_expert, 1)
        self.tone_group.addButton(self.radio_coach, 2)
        self.tone_group.addButton(self.radio_summary, 3)

        layout_step2.addWidget(self.radio_neighbor)
        layout_step2.addWidget(self.radio_expert)
        layout_step2.addWidget(self.radio_coach)
        layout_step2.addWidget(self.radio_summary)

        # 이모티콘 밀도 옵션
        density_layout = QHBoxLayout()
        density_layout.addWidget(QLabel("이모티콘 사용:"))
        self.combo_density = QComboBox()
        self.combo_density.addItems(["적당히 보기 좋게 (추천)", "풍성하고 활기차게", "최소한으로 깔끔하게"])
        density_layout.addWidget(self.combo_density)
        density_layout.addStretch()
        layout_step2.addLayout(density_layout)

        layout.addWidget(card_step2)

        # ----------------------------------------------------
        # [3단계] 블로그 글 만들기 버튼 카드
        # ----------------------------------------------------
        self.btn_generate = QPushButton("✨ 네이버 블로그 글 만들기 (클릭)")
        self.btn_generate.setObjectName("GenerateButton")
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.clicked.connect(self.on_start_generate)
        layout.addWidget(self.btn_generate)

        # 진행 표시줄
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.lbl_loading_status = QLabel("")
        self.lbl_loading_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_loading_status.setStyleSheet("color: #2563EB; font-weight: bold; font-size: 13px;")
        self.lbl_loading_status.setVisible(False)
        layout.addWidget(self.lbl_loading_status)

        layout.addStretch()
        return container

    def create_right_result_panel(self) -> QWidget:
        """우측 4단계 결과 미리보기 & 원클릭 복사 영역"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(12)

        card_result = QFrame()
        card_result.setObjectName("CardFrame")
        card_layout = QVBoxLayout(card_result)
        card_layout.setSpacing(12)

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

        btn_copy_plain = QPushButton("📄 텍스트 복사")
        btn_copy_plain.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copy_plain.clicked.connect(self.on_copy_plain_text)
        action_header.addWidget(btn_copy_plain)

        card_layout.addLayout(action_header)

        # 1. 추천 제목 선택 바
        title_box = QFrame()
        title_box.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px;")
        title_box_layout = QVBoxLayout(title_box)
        title_box_layout.setSpacing(4)
        title_box_layout.addWidget(QLabel("💡 마음에 드는 제목을 클릭해보세요:"))

        self.combo_titles = QComboBox()
        self.combo_titles.setStyleSheet("font-weight: bold; color: #1E293B; font-size: 14px;")
        self.combo_titles.currentIndexChanged.connect(self.on_title_changed)
        title_box_layout.addWidget(self.combo_titles)
        card_layout.addWidget(title_box)

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
            self.lbl_photo_count.setStyleSheet("font-weight: bold; color: #166534; font-size: 12px;")
        else:
            self.lbl_photo_count.setStyleSheet("font-weight: bold; color: #2563EB; font-size: 12px;")

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
        return {
            "mode": "property",
            "topic": memo,
            "file_paths": list(self.property_photos),
            "property_info": property_info
        }

    def _get_news_input_payload(self):
        """뉴스 기사 모드 입력값 검증 및 페이로드 생성"""
        topic = self.edit_news_topic.toPlainText().strip()
        if not topic:
            QMessageBox.warning(self, "주제 입력 필요", "작성하고 싶은 부동산 소식이나 주제를 간단히 입력해주세요!")
            self.edit_news_topic.setFocus()
            return None
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
            if photo_count > 0:
                return f"🏠 현장 사진 {photo_count}장과 매물 정보를 정밀 분석하여 룸투어 글을 작성하고 있습니다..."
            return "🏠 매물 스펙을 바탕으로 네이버 블로그 추천 매물 포스팅을 작성하고 있습니다..."
        if mode == "news":
            return "🔍 최신 인터넷 기사를 검색하고 전문 블로그 글을 작성하고 있습니다..."
        return "📄 첨부자료 내용을 정밀 분석하여 블로그 글을 작성하고 있습니다..."

    def on_start_generate(self):
        """글 생성 시작"""
        if not self.config.get("gemini_api_key", "").strip():
            self.open_settings_dialog()
            if not self.config.get("gemini_api_key", "").strip():
                QMessageBox.warning(self, "API 키 필요", "글을 생성하려면 Gemini API 키를 먼저 입력해야 합니다.")
                return

        current_tab_idx = self.input_tab.currentIndex()
        if current_tab_idx == 0:
            payload = self._get_property_input_payload()
        elif current_tab_idx == 1:
            payload = self._get_news_input_payload()
        else:
            payload = self._get_file_input_payload()

        if not payload:
            return

        tone_key = self.get_selected_tone_key()
        density_idx = self.combo_density.currentIndex()
        density_map = {0: "normal", 1: "high", 2: "low"}
        self.config["emoji_density"] = density_map.get(density_idx, "normal")

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
            self.combo_titles.addItem(f"📌 {t}")
        self.combo_titles.blockSignals(False)

        # 2. 본문 에디터 반영
        self.edit_body.blockSignals(True)
        self.edit_body.setPlainText(result["body"])
        self.edit_body.blockSignals(False)

        # 3. 해시태그 반영
        self.edit_tags.setText(" ".join(result["tags"]))

        # 4. 스마트에디터 HTML 미리보기 업데이트
        self.update_preview()

        # 결과 탭으로 포커스
        self.result_tab.setCurrentIndex(0)

        QMessageBox.information(self, "작성 완료! 🎉", "네이버 블로그 글이 멋지게 완성되었습니다!\n'네이버 블로그에 바로 붙여넣기 복사' 버튼을 눌러 블로그에 붙여넣어보세요.")

    def on_generation_error(self, error_msg: str):
        """생성 오류 처리"""
        self.btn_generate.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_loading_status.setVisible(False)
        
        QMessageBox.critical(
            self,
            "생성 중 오류 발생",
            f"글을 생성하는 동안 문제가 발생했습니다:\n\n{error_msg}\n\n※ API 키가 올바른지, 인터넷 연결이 정상인지 확인해주세요."
        )

    def on_title_changed(self, index: int):
        """제목 선택 변경 시 미리보기 업데이트"""
        self.update_preview()

    def on_editor_text_changed(self):
        """에디터 내용 수정 시 실시간 미리보기 동기화"""
        self.update_preview()

    def update_preview(self):
        """스마트에디터 ONE 스타일 HTML 미리보기 갱신"""
        current_title = self.combo_titles.currentText().replace("📌 ", "").strip()
        if not current_title:
            current_title = "공인중개사 추천 매물 브리핑"
        body_text = self.edit_body.toPlainText()
        tags = [t for t in self.edit_tags.text().split() if t.strip()]

        preview_html = generate_blog_preview_html(current_title, body_text, tags)
        self.preview_browser.setHtml(preview_html)

    def on_copy_for_naver(self):
        """
        네이버 스마트에디터 ONE에 맞춘 리치텍스트/HTML + 플레인 텍스트 클립보드 복사
        """
        current_title = self.combo_titles.currentText().replace("📌 ", "").strip()
        body_text = self.edit_body.toPlainText()
        tags_text = self.edit_tags.text()

        if not body_text:
            QMessageBox.warning(self, "알림", "복사할 내용이 없습니다. 먼저 글을 생성해주세요.")
            return

        import markdown
        # 스마트에디터에 깔끔하게 붙여넣어지는 심플 HTML 구성
        body_html = markdown.markdown(body_text, extensions=['extra', 'nl2br', 'tables'])
        
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

        QMessageBox.information(
            self,
            "복사 완료! 📋",
            "네이버 블로그 맞춤 서식으로 복사되었습니다!\n\n네이버 블로그 스마트에디터 화면에서 [Ctrl + V] 로 붙여넣으시면 제목과 본문 서식이 그대로 들어갑니다."
        )

    def on_copy_plain_text(self):
        """일반 텍스트 복사"""
        current_title = self.combo_titles.currentText().replace("📌 ", "").strip()
        body_text = self.edit_body.toPlainText()
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
