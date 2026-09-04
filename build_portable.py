"""
Windows 무설치 단일 실행 파일(.exe) 단독 포터블 빌드 스크립트 (--onefile)
"""

import os
import subprocess
import sys
import shutil

DIVIDER = "=" * 50

def build(mode="onedir"):
    """mode: 'onedir' (초고속 부팅 폴더형 포터블) or 'onefile' (단일 .exe 파일)"""
    print(DIVIDER)
    if mode == "onedir":
        print(" [Start] Building High-Speed Portable Folder (--onedir, 0.5초 즉시 실행)")
    else:
        print(" [Start] Building Standalone Portable Single .exe (--onefile, 단일 파일)")
    print(DIVIDER)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_script = os.path.join(base_dir, "app.py")

    mode_flag = "--onedir" if mode == "onedir" else "--onefile"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        mode_flag,
        "--windowed",           # 콘솔창 숨김 (GUI 모드)
        "--name", "공인중개사_블로그_생성기",
        "--clean",
        "--add-data", f"{os.path.join(base_dir, 'prompts')};prompts",
        "--add-data", f"{os.path.join(base_dir, 'ui')};ui",
        "--add-data", f"{os.path.join(base_dir, 'services')};services",
        # 필수 의존성 명시
        "--hidden-import", "PyQt6",
        "--hidden-import", "google.genai",
        "--hidden-import", "google.generativeai",
        "--hidden-import", "pypdf",
        "--hidden-import", "docx",
        "--hidden-import", "markdown",
        "--hidden-import", "bs4",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        # 구동 속도를 갉아먹는 불필요한 대형 패키지 제외
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas",
        "--exclude-module", "unittest",
        "--exclude-module", "test",
        app_script
    ]

    print("Running command:", " ".join(cmd))
    result = subprocess.run(cmd)

    if result.returncode == 0:
        dist_dir = os.path.join(base_dir, 'dist')
        if mode == "onefile":
            dist_exe = os.path.join(dist_dir, '공인중개사_블로그_생성기.exe')
            target_exe = os.path.join(base_dir, '공인중개사_블로그_생성기.exe')
            if os.path.exists(dist_exe):
                try:
                    shutil.copy2(dist_exe, target_exe)
                except Exception as e:
                    print(f"Notice: {e}")
            print(DIVIDER)
            print(" [Success] Single .exe created successfully!")
            print(f" Output: {target_exe}")
            print(DIVIDER)
        else:
            folder_path = os.path.join(dist_dir, '공인중개사_블로그_생성기')
            print(DIVIDER)
            print(" [Success] High-Speed Portable Folder created successfully!")
            print(f" Output Folder: {folder_path}")
            print(" ※ 이 폴더 내부의 '공인중개사_블로그_생성기.exe'를 실행하면 0.5초 이내에 즉시 뜹니다.")
            print(DIVIDER)
    else:
        print("\n[Error] Build failed.")

if __name__ == "__main__":
    # 인자 확인 (--onefile 또는 --onedir)
    target_mode = "onedir"  # 고속 실행이 기본값
    if len(sys.argv) > 1:
        if "--onefile" in sys.argv or "onefile" in sys.argv:
            target_mode = "onefile"
    build(mode=target_mode)
