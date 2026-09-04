import os
import json
import sys

def get_app_dir():
    """실행 파일(.exe) 또는 스크립트가 위치한 디렉토리 경로 반환 (포터블 지원)"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 등으로 패키징된 실행 파일 환경
        return os.path.dirname(sys.executable)
    else:
        # 일반 파이썬 스크립트 실행 환경
        return os.path.dirname(os.path.abspath(__file__))

def get_config_path():
    """설정 파일(blog_maker_config.json) 경로 탐색 및 반환"""
    app_dir = get_app_dir()
    direct_path = os.path.join(app_dir, "blog_maker_config.json")
    if os.path.exists(direct_path):
        return direct_path

    # dist 하위 폴더에서 실행된 경우 상위(프로젝트 루트) 탐색
    parent_dir = os.path.dirname(app_dir)
    parent_path = os.path.join(parent_dir, "blog_maker_config.json")
    if os.path.exists(parent_path):
        return parent_path

    grandparent_dir = os.path.dirname(parent_dir)
    grandparent_path = os.path.join(grandparent_dir, "blog_maker_config.json")
    if os.path.exists(grandparent_path):
        return grandparent_path

    # 작업 디렉토리(CWD) 확인
    cwd_path = os.path.join(os.getcwd(), "blog_maker_config.json")
    if os.path.exists(cwd_path):
        return cwd_path

    return direct_path

CONFIG_FILE_PATH = get_config_path()

DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "selected_model": "gemini-3.6-flash",
    "default_tone": "neighbor",  # neighbor, expert, coach, summary
    "emoji_density": "normal",   # high, normal, low
    "office_name": "",           # 공인중개사 사무소 이름 (예: 신우 공인중개사사무소)
    "agent_name": "",            # 대표/담당자 이름
    "office_phone": "",          # 연락처
    "office_location": "",       # 사무소 위치/주소
    "custom_signature": "",      # 글 하단에 들어갈 맞춤 서명 문구
    "include_office_info": True,
    "search_freshness": "recent_3m", # latest (최신 1개월), recent_3m (최근 3개월), this_year (올해), all (제한없음)
    "include_source_date": True,  # 글 본문에 발표 시점/최신 일자 명시 여부
    "enable_local_search": False, # 매물 소개 시 주변 최신 호재 실시간 검색 연동 여부
    "theme": "clean_light"
}

def load_config():
    """설정 파일 로드 (없으면 기본값 생성)"""
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                # 이전 2.5 또는 지원 중단/구형 모델이 저장되어 있으면 최신 추천 모델로 자동 마이그레이션
                cur_model = config.get("selected_model", "")
                if not cur_model or "2.5" in cur_model or "1.5" in cur_model:
                    config["selected_model"] = "gemini-3.6-flash"
                    save_config(config)
                return config
        except Exception as e:
            print(f"설정 파일 로드 오류: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config_dict):
    """설정 파일 저장"""
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"설정 파일 저장 오류: {e}")
        return False
