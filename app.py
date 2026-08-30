"""
공인중개사 네이버 블로그 글 생성 프로그램 실행 진입점 (app.py)
"""

import sys
import os

# 고해상도 모니터 DPI 스케일링 설정
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

# pyrefly: ignore [missing-import]
from PyQt6.QtWidgets import QApplication, QSplashScreen
# pyrefly: ignore [missing-import]
from PyQt6.QtCore import Qt, QRectF
# pyrefly: ignore [missing-import]
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPainterPath, QLinearGradient


FONT_FAMILY = "Malgun Gothic"


def _create_splash_pixmap() -> QPixmap:
    """즉시 렌더링되는 프리미엄 스플래시 화면 이미지 생성 (460x220)"""
    width, height = 460, 220
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 둥근 사각형 배경 (세련된 블루 그라데이션)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, width, height), 16, 16)
    
    grad = QLinearGradient(0, 0, width, height)
    grad.setColorAt(0.0, QColor("#1E3A8A"))   # Deep Royal Blue
    grad.setColorAt(1.0, QColor("#2563EB"))   # Vivid Blue
    painter.fillPath(path, grad)

    # 외곽선
    painter.setPen(QColor("#60A5FA"))
    painter.drawPath(path)

    # 브랜드 타이틀
    painter.setPen(QColor("#93C5FD"))
    font_brand = QFont(FONT_FAMILY, 11, QFont.Weight.DemiBold)
    painter.setFont(font_brand)
    painter.drawText(30, 50, "🏢 신우 공인중개사 전용")

    # 메인 헤드라인
    painter.setPen(QColor("#FFFFFF"))
    font_title = QFont(FONT_FAMILY, 18, QFont.Weight.Bold)
    painter.setFont(font_title)
    painter.drawText(30, 85, "AI 네이버 블로그 글 생성기")

    # 서브 텍스트
    painter.setPen(QColor("#E2E8F0"))
    font_sub = QFont(FONT_FAMILY, 10)
    painter.setFont(font_sub)
    painter.drawText(30, 115, "현장 사진 매물 포스팅 · 최신 이슈 브리핑 · 원클릭 복사")

    # 하단 로딩 진행 안내 카드
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(0, 0, 0, 40))
    painter.drawRoundedRect(QRectF(25, 150, width - 50, 45), 8, 8)

    painter.setPen(QColor("#FEF08A"))  # 밝은 옐로우 텍스트
    font_loading = QFont(FONT_FAMILY, 10, QFont.Weight.Bold)
    painter.setFont(font_loading)
    painter.drawText(QRectF(25, 150, width - 50, 45), Qt.AlignmentFlag.AlignCenter, "⚡ 프로그램을 신속하게 준비하고 있습니다...")

    painter.end()
    return pixmap


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

    # 1. 스플래시 화면 즉시 표시 (0.05초)
    splash = QSplashScreen(_create_splash_pixmap(), Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
    splash.show()
    app.processEvents()

    # 2. 메인 윈도우 지연 로딩 및 표시
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    # 3. 스플래시 화면 닫기 및 메인 윈도우 포커스
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
