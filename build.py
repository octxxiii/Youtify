import os
import platform
import shutil
import subprocess
import sys

def build_executable():
    # Windows에서 한글 출력을 위한 인코딩 설정
    if platform.system() == 'Windows':
        sys.stdout.reconfigure(encoding='utf-8')
    
    system = platform.system()
    
    # 운영체제 확인
    if system not in ['Windows', 'Darwin']:
        raise Exception(f"지원하지 않는 운영체제입니다: {system}")
    
    # ffmpeg 파일 확인
    ffmpeg_name = 'ffmpeg.exe' if system == 'Windows' else 'ffmpeg'
    if not os.path.exists(ffmpeg_name):
        raise Exception(f"현재 디렉토리에 {ffmpeg_name} 파일이 없습니다.")
    
    print(f"{system}용 실행 파일을 빌드합니다...")
    
    # PyInstaller 명령어 구성
    cmd = [
        'pyinstaller',
        '--windowed',
        '--icon=st2.icns',
        '--add-binary', f'{ffmpeg_name}:.',
        '--name', 'Youtify',
        'youtify.py'
    ]
    
    # 빌드 실행
    subprocess.run(cmd)
    
    print(f"\n빌드가 완료되었습니다.")
    print(f"실행 파일 위치: dist/Youtify/Youtify{'exe' if system == 'Windows' else ''}")

if __name__ == '__main__':
    build_executable() 