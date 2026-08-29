"""
공인중개사 네이버 블로그 글 생성 프로그램 실행 진입점 (app.py)
"""

import sys
import os

# 고해상도 모니터 DPI 스케일링 설정
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

# pyrefly: ignore [missing-import]
from PyQt6.QtWidgets import QApplication
# pyrefly: ignore [missing-import]
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow

def main():
    # 고해상도 지원 속성 활성화
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("공인중개사 네이버 블로그 생성기")
    app.setOrganizationName("SinwooRealEstateAI")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
