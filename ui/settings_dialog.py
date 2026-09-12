"""
프로그램 간편 설정 다이얼로그 모듈 (ui/settings_dialog.py)
- API 키, 모델 선택, 중개사무소 서명 정보, 네이버 뉴스 검색 API 설정
"""

# pyrefly: ignore [missing-import]
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFrame,
    QCheckBox, QComboBox
)

from config import save_config

DEFAULT_MODEL_NAME = "gemini-3.6-flash"
FLASH_35_MODEL_NAME = "gemini-3.5-flash"
FLASH_35_LITE_MODEL_NAME = "gemini-3.5-flash-lite"
FLASH_31_LITE_MODEL_NAME = "gemini-3.1-flash-lite"

CARD_HEADER_STYLE = "font-weight: bold; font-size: 16px; color: #1E293B;"


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
        lbl_api_title.setStyleSheet(CARD_HEADER_STYLE)
        api_layout.addWidget(lbl_api_title)

        lbl_api_desc = QLabel("무료로 발급받은 Gemini API 키를 입력하세요. (한 번 입력하면 자동 저장됩니다)")
        lbl_api_desc.setStyleSheet("color: #64748B; font-size: 14px;")
        lbl_api_desc.setWordWrap(True)
        api_layout.addWidget(lbl_api_desc)

        self.edit_api_key = QLineEdit()
        self.edit_api_key.setPlaceholderText("AIzaSy... 형식의 API 키를 붙여넣으세요")
        self.edit_api_key.setText(self.config.get("gemini_api_key", ""))
        self.edit_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.edit_api_key)

        # 모델 선택 (공식 안정 모델 4종)
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("사용 모델:"))
        self.combo_model = QComboBox()
        self.combo_model.addItems([
            f"{DEFAULT_MODEL_NAME} (기본 추천: 최신 3.6 Flash / 안정)",
            f"{FLASH_35_MODEL_NAME} (3.5 Flash 지능형 / 안정)",
            f"{FLASH_35_LITE_MODEL_NAME} (3.5 Flash-Lite 고속·효율 / 안정)",
            f"{FLASH_31_LITE_MODEL_NAME} (3.1 Flash-Lite 비용 최적화 / 안정)"
        ])
        selected_model = self.config.get("selected_model", DEFAULT_MODEL_NAME)
        if "3.5-flash-lite" in selected_model:
            self.combo_model.setCurrentIndex(2)
        elif "3.5" in selected_model:
            self.combo_model.setCurrentIndex(1)
        elif "3.1" in selected_model:
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
        lbl_office_title.setStyleSheet(CARD_HEADER_STYLE)
        office_layout.addWidget(lbl_office_title)

        self.chk_include_office = QCheckBox("블로그 글 끝에 우리 부동산 사무소 정보를 항상 넣기")
        self.chk_include_office.setChecked(self.config.get("include_office_info", True))
        office_layout.addWidget(self.chk_include_office)

        form_grid = QGridLayout()
        form_grid.setSpacing(8)

        form_grid.addWidget(QLabel("사무소 상호:"), 0, 0)
        self.edit_office_name = QLineEdit()
        self.edit_office_name.setPlaceholderText("예: 공인중개사사무소 상호명")
        self.edit_office_name.setText(self.config.get("office_name", ""))
        form_grid.addWidget(self.edit_office_name, 0, 1)

        form_grid.addWidget(QLabel("대표자 성명:"), 1, 0)
        self.edit_agent_name = QLineEdit()
        self.edit_agent_name.setPlaceholderText("예: 대표 공인중개사 성명")
        self.edit_agent_name.setText(self.config.get("agent_name", ""))
        form_grid.addWidget(self.edit_agent_name, 1, 1)

        form_grid.addWidget(QLabel("연락처/전화:"), 2, 0)
        self.edit_office_phone = QLineEdit()
        self.edit_office_phone.setPlaceholderText("예: 02-1234-5678 / 010-1234-5678")
        self.edit_office_phone.setText(self.config.get("office_phone", ""))
        form_grid.addWidget(self.edit_office_phone, 2, 1)

        form_grid.addWidget(QLabel("사무소 위치:"), 3, 0)
        self.edit_office_location = QLineEdit()
        self.edit_office_location.setPlaceholderText("예: 서울특별시 강남구 테헤란로 123 (도로명/지번 주소)")
        self.edit_office_location.setText(self.config.get("office_location", ""))
        form_grid.addWidget(self.edit_office_location, 3, 1)

        office_layout.addLayout(form_grid)
        layout.addWidget(office_group)

        # 3. 실시간 뉴스 검색 API 섹션 (하이브리드 지원)
        naver_group = QFrame()
        naver_group.setObjectName("CardFrame")
        naver_layout = QVBoxLayout(naver_group)

        lbl_naver_title = QLabel("🟢 실시간 뉴스 검색 (하이브리드 지원)")
        lbl_naver_title.setStyleSheet(CARD_HEADER_STYLE)
        naver_layout.addWidget(lbl_naver_title)

        lbl_naver_desc = QLabel(
            "기본적으로 **무료 실시간 뉴스 검색(키 불필요)**이 자동 작동합니다.\n"
            "네이버 공식 뉴스 검색 API(일 25,000건 무료)를 이용하시려면 아래에 입력하세요. (선택 사항)"
        )
        lbl_naver_desc.setStyleSheet("color: #64748B; font-size: 13px;")
        lbl_naver_desc.setWordWrap(True)
        naver_layout.addWidget(lbl_naver_desc)

        naver_grid = QGridLayout()
        naver_grid.setSpacing(8)
        naver_grid.addWidget(QLabel("Naver Client ID:"), 0, 0)
        self.edit_naver_id = QLineEdit()
        self.edit_naver_id.setPlaceholderText("네이버 Client ID (비워두면 무료 오픈 검색 사용)")
        self.edit_naver_id.setText(self.config.get("naver_client_id", ""))
        naver_grid.addWidget(self.edit_naver_id, 0, 1)

        naver_grid.addWidget(QLabel("Naver Secret:"), 1, 0)
        self.edit_naver_secret = QLineEdit()
        self.edit_naver_secret.setPlaceholderText("네이버 Client Secret")
        self.edit_naver_secret.setText(self.config.get("naver_client_secret", ""))
        self.edit_naver_secret.setEchoMode(QLineEdit.EchoMode.Password)
        naver_grid.addWidget(self.edit_naver_secret, 1, 1)

        naver_layout.addLayout(naver_grid)
        layout.addWidget(naver_group)

        # 4. 저장 및 닫기 버튼
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
            self.config["selected_model"] = FLASH_35_MODEL_NAME
        elif idx == 2:
            self.config["selected_model"] = FLASH_35_LITE_MODEL_NAME
        elif idx == 3:
            self.config["selected_model"] = FLASH_31_LITE_MODEL_NAME
        else:
            self.config["selected_model"] = DEFAULT_MODEL_NAME
        self.config["include_office_info"] = self.chk_include_office.isChecked()
        self.config["office_name"] = self.edit_office_name.text().strip()
        self.config["agent_name"] = self.edit_agent_name.text().strip()
        self.config["office_phone"] = self.edit_office_phone.text().strip()
        self.config["office_location"] = self.edit_office_location.text().strip()
        self.config["naver_client_id"] = self.edit_naver_id.text().strip()
        self.config["naver_client_secret"] = self.edit_naver_secret.text().strip()

        save_config(self.config)
        self.accept()
