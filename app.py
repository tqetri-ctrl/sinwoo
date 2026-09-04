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

FONT_NAME = "Malgun Gothic"

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

    # 즉각적인 시각적 피드백을 제공하는 로딩 스플래시 화면
    splash = None
    try:
        # pyrefly: ignore [missing-import]
        from PyQt6.QtWidgets import QSplashScreen
        # pyrefly: ignore [missing-import]
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
        pixmap = QPixmap(420, 200)
        pixmap.fill(QColor("#1E293B"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setPen(QColor("#FFFFFF"))
        font_title = QFont(FONT_NAME, 15, QFont.Weight.Bold)
        painter.setFont(font_title)
        painter.drawText(28, 65, "🏢 신우 공인중개사")

        font_sub = QFont(FONT_NAME, 12)
        painter.setPen(QColor("#60A5FA"))
        painter.setFont(font_sub)
        painter.drawText(28, 100, "AI 네이버 블로그 글 생성기")

        font_loading = QFont(FONT_NAME, 10)
        painter.setPen(QColor("#94A3B8"))
        painter.setFont(font_loading)
        painter.drawText(28, 155, "최신 서식 및 시스템을 준비하고 있습니다...")
        painter.end()

        splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()
    except Exception:
        splash = None

    window = MainWindow()
    if splash:
        splash.finish(window)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
