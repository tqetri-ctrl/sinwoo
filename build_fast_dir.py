"""
Windows 초고속 구동 폴더형 실행 패키지 빌드 스크립트 (--onedir)
압축 해제 과정이 전혀 없어 0.5초 만에 즉시 실행됩니다.
"""

import os
import subprocess
import sys
import shutil

DIVIDER = "=" * 50

def build_fast_directory():
    print(DIVIDER)
    print(" [Start] Building High-Speed Portable Folder (--onedir)")
    print(DIVIDER)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    app_script = os.path.join(base_dir, "app.py")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",             # 압축 해제 없이 즉시 실행되는 폴더형 빌드
        "--windowed",           # 콘솔창 숨김 (GUI 모드)
        "--name", "공인중개사_블로그_생성기_고속실행",
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
        "--exclude-module", "tkinter",
        "--exclude-module", "unittest",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "IPython",
        "--exclude-module", "test",
        app_script
    ]

    print("Running command:", " ".join(cmd))
    result = subprocess.run(cmd)

    if result.returncode == 0:
        dist_dir = os.path.join(base_dir, 'dist', '공인중개사_블로그_생성기_고속실행')
        exe_path = os.path.join(dist_dir, '공인중개사_블로그_생성기_고속실행.exe')
        print(DIVIDER)
        print(" [Success] High-Speed Folder package created successfully!")
        print(f" Folder Location: {dist_dir}")
        print(f" Executable File: {exe_path}")
        print(" ⚡ 실행 팁: dist 폴더 내의 실행 파일 바로가기를 만들거나 폴더 전체를 배포하세요.")
        print(DIVIDER)
    else:
        print("\n[Error] Build failed.")

if __name__ == "__main__":
    build_fast_directory()
