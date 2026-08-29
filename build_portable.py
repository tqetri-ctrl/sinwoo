"""
Windows 무설치 단일 실행 파일(.exe) 단독 포터블 빌드 스크립트 (--onefile)
"""

import os
import subprocess
import sys
import shutil

DIVIDER = "=" * 50

def build_single_exe():
    print(DIVIDER)
    print(" [Start] Building Standalone Portable Single .exe")
    print(DIVIDER)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_script = os.path.join(base_dir, "app.py")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",            # 단 하나의 독립 실행 파일 .exe 생성
        "--windowed",           # 콘솔창 숨김 (GUI 모드)
        "--name", "공인중개사_블로그_생성기",
        "--clean",
        "--add-data", f"{os.path.join(base_dir, 'prompts')};prompts",
        "--add-data", f"{os.path.join(base_dir, 'ui')};ui",
        "--add-data", f"{os.path.join(base_dir, 'services')};services",
        "--hidden-import", "PyQt6",
        "--hidden-import", "google.genai",
        "--hidden-import", "google.generativeai",
        "--hidden-import", "pypdf",
        "--hidden-import", "docx",
        "--hidden-import", "markdown",
        "--hidden-import", "bs4",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        app_script
    ]

    print("Running command:", " ".join(cmd))
    result = subprocess.run(cmd)

    if result.returncode == 0:
        dist_exe = os.path.join(base_dir, 'dist', '공인중개사_블로그_생성기.exe')
        target_exe = os.path.join(base_dir, '공인중개사_블로그_생성기.exe')
        
        # 루트 디렉토리에 복사
        if os.path.exists(dist_exe):
            try:
                shutil.copy2(dist_exe, target_exe)
            except Exception as e:
                print(f"Direct copy notice: {e}")
            print(DIVIDER)
            print(" [Success] Standalone Portable .exe created successfully!")
            print(f" Output: {target_exe}")
            print(DIVIDER)
    else:
        print("\n[Error] Build failed.")

if __name__ == "__main__":
    build_single_exe()
