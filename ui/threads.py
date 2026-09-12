"""
백그라운드 비동기 워커 스레드 모듈 (ui/threads.py)
- YonhapNewsLoadThread: 연합뉴스 경제/부동산 RSS 비동기 수집
- BlogGenerationThread: Gemini AI 블로그 글 비동기 생성
"""

# pyrefly: ignore [missing-import]
from PyQt6.QtCore import QThread, pyqtSignal

from services.gemini_service import GeminiBlogService
from services.news_search_service import fetch_yonhap_realestate_news


class YonhapNewsLoadThread(QThread):
    """연합뉴스 경제 RSS에서 부동산 속보 피드를 백그라운드 비동기로 수집하는 스레드"""
    news_loaded_signal = pyqtSignal(list)

    def run(self):
        try:
            articles = fetch_yonhap_realestate_news(max_results=12)
            self.news_loaded_signal.emit(articles)
        except Exception:
            self.news_loaded_signal.emit([])


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
