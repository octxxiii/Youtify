import os
import shutil
import sys
import requests
import platform  # 운영체제 확인을 위해 추가
from PyQt5.QtGui import QPixmap, QIcon, QDesktopServices, QMovie
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWebChannel import QWebChannel
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineProfile
except ImportError:
    print("PyQtWebEngine이 설치되지 않았습니다. pip install PyQtWebEngine을 실행해주세요.")
    sys.exit(1)
from PyQt5.QtWidgets import (QApplication, QDialog, QPushButton, QVBoxLayout, QLineEdit, QLabel, QProgressBar,
                             QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QFileDialog,
                             QTextEdit, QComboBox, QAbstractItemView, QHBoxLayout, QSplitter, QWidget, QMessageBox,
                             QSlider)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, pyqtSlot, QObject, QTimer, QUrl, QSize, QDateTime
import yt_dlp
import resources_rc
import re

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        # PyInstaller로 패키징된 경우
        return os.path.join(sys._MEIPASS, 'ffmpeg.exe' if platform.system() == 'Windows' else 'ffmpeg')
    else:
        # 개발 환경
        if platform.system() == 'Darwin':
            return '/opt/homebrew/bin/ffmpeg'
        else:
            return 'C:\\ffmpeg\\bin\\ffmpeg.exe'

# 운영체제별 설정
SYSTEM = platform.system()
if SYSTEM == 'Darwin':  # macOS
    CACHE_DIR = os.path.expanduser('~/Library/Caches/Nobody')
elif SYSTEM == 'Windows':
    CACHE_DIR = os.path.join(os.environ['LOCALAPPDATA'], 'Nobody')
else:
    CACHE_DIR = os.path.expanduser('~/.cache/Nobody')

themes = {
    "Dark Theme": """
        QDialog { background-color: #2D2D2D; }
        QPushButton { background-color: #333333; color: #FFFFFF; border: 2px solid #555555; border-radius: 5px; padding: 5px; }
        QPushButton:hover { background-color: #555555; }
        QPushButton:pressed { background-color: #444444; }
        QComboBox { background-color: #333333; color: #FFFFFF; border: 2px solid #555555; border-radius: 5px; padding: 3px; }
        QComboBox QAbstractItemView { background: #2D2D2D; selection-background-color: #3D3D3D; color: #FFFFFF; }
        QLineEdit, QTextEdit { background-color: #333333; color: #FFFFFF; border: 2px solid #555555; }
        QTableWidget { background-color: #2D2D2D; color: #FFFFFF; border: none; }
        QTableWidget::item { background-color: #333333; color: #FFFFFF; border: 1px solid #2D2D2D; }
        QLabel { color: #FFFFFF; }
        QHeaderView::section { background-color: #333333; color: #FFFFFF; padding: 4px; border: 1px solid #2D2D2D; }
        QProgressBar { border: 2px solid #333333; border-radius: 5px; background-color: #2D2D2D; text-align: center; }
        QProgressBar::chunk { background-color: #555555; }
    """,
    "Monokai": """
        QDialog { background-color: #272822; }
        QPushButton { background-color: #75715E; color: #F8F8F2; border: 1px solid #75715E; border-radius: 4px; padding: 5px; margin: 2px; }
        QPushButton:hover { background-color: #F92672; color: #F8F8F2; }
        QPushButton:pressed { background-color: #66D9EF; color: #272822; }
        QComboBox { background-color: #75715E; color: #F8F8F2; border-radius: 4px; padding: 3px; margin: 2px; }
        QComboBox QAbstractItemView { background: #272822; selection-background-color: #A6E22E; color: #F8F8F2; }
        QLineEdit { background-color: #272822; color: #F8F8F2; border: 1px solid #75715E; border-radius: 4px; padding: 3px; }
        QTextEdit { background-color: #272822; color: #F8F8F2; border: 1px solid #75715E; border-radius: 4px; padding: 3px; }
        QTableWidget { background-color: #272822; color: #F8F8F2; border: none; }
        QTableWidget::item { background-color: #3E3D32; color: #F8F8F2; border: 1px solid #3E3D32; }
        QLabel { color: #F8F8F2; }
        QHeaderView::section { background-color: #75715E; color: #F8F8F2; padding: 4px; border: 1px solid #75715E; }
        QProgressBar { border: 2px solid #75715E; border-radius: 5px; background-color: #272822; text-align: center; }
        QProgressBar::chunk { background-color: #A6E22E; }
    """,
    "Refined Elegance": """
        QDialog { background-color: #E4E4DE; }
        QPushButton { background-color: #C4C5BA; color: #1B1B1B; border-radius: 5px; padding: 5px; }
        QPushButton:hover { background-color: #595f39; }
        QComboBox { background-color: #C4C5BA; color: #1B1B1B; border-radius: 5px; padding: 5px; }
        QComboBox QAbstractItemView { background: #C4C5BA; selection-background-color: #595f39; }
        QLineEdit, QTextEdit { background-color: #FFFFFF; color: #1B1B1B; }
        QTableWidget { background-color: #E4E4DE; border: none; }
        QTableWidget::item { background-color: #C4C5BA; color: #1B1B1B; border: 1px solid #E4E4DE; font-weight: bold;}
        QLabel { color: #1B1B1B; }
        QHeaderView::section { background-color: #C4C5BA; color: #1B1B1B; padding: 4px; border: 1px solid #E4E4DE; font-weight: bold; }
        QProgressBar { border: 2px solid #C4C5BA; border-radius: 5px; background-color: #E4E4DE; text-align: center; }
        QProgressBar::chunk { background-color: #595f39; }
    """,
    "Enchanted Nature": """
        QDialog { background-color: #354E56; }
        QPushButton, QComboBox { background-color: #0F2143; color: #8B6212; border-radius: 5px; padding: 5px; }
        QComboBox QAbstractItemView { background: #0F2143; selection-background-color: #43572E; }
        QPushButton:hover { background-color: #43572E; }
        QLineEdit, QTextEdit, QTableWidget { background-color: #FFFFFF; color: #8B6212; }
        QTableWidget { background-color: #354E56; border: none; }
        QTableWidget::item { background-color: #0F2143; color: #8B6212; border: 1px solid #354E56; font-weight: bold;}
        QLabel { color: #8B6212; }
        QHeaderView::section { background-color: #0F2143; color: #8B6212; padding: 4px; border: 1px solid #354E56; font-weight: bold; }
        QProgressBar { border: 2px solid #0F2143; border-radius: 5px; background-color: #354E56; text-align: center; }
        QProgressBar::chunk { background-color: #43572E; }
    """,
    "Serene Coastline": """
        QDialog { background-color: #D1E8E2; }
        QPushButton { background-color: #19747E; color: #A9D6E5; border-radius: 5px; padding: 5px; }
        QPushButton:hover { background-color: #E2E2E2; }
        QComboBox { background-color: #19747E; color: #A9D6E5; border-radius: 5px; padding: 5px; }
        QComboBox QAbstractItemView { background: #19747E; selection-background-color: #E2E2E2; }
        QLineEdit, QTextEdit { background-color: #FFFFFF; color: #A9D6E5; }
        QTableWidget { background-color: #D1E8E2; border: none; }
        QTableWidget::item { background-color: #19747E; color: #A9D6E5; border: 1px solid #D1E8E2; font-weight: bold; }
        QLabel { color: #A9D6E5; }
        QHeaderView::section { background-color: #19747E; color: #A9D6E5; padding: 4px; border: 1px solid #D1E8E2; font-weight: bold; }
        QProgressBar { border: 2px solid #19747E; border-radius: 5px; background-color: #D1E8E2; text-align: center; }
        QProgressBar::chunk { background-color: #E2E2E2; }
    """,
    "Sunset Glow": """
        QDialog { background-color: #FFE8D6; }
        QPushButton { background-color: #FF9F1C; color: white; border-radius: 5px; padding: 5px; }
        QPushButton:hover { background-color: #FFBF69; }
        QComboBox { background-color: #FF9F1C; color: white; border-radius: 5px; padding: 5px; }
        QComboBox QAbstractItemView { background: #FF9F1C; selection-background-color: #FFBF69; }
        QLineEdit, QTextEdit { background-color: #FFFFFF; color: white; }
        QTableWidget { background-color: #FFE8D6; border: none; }
        QTableWidget::item { background-color: #FF9F1C; color: white; border: 1px solid #FFE8D6; font-weight: bold; }
        QLabel { color: #CB997E; }
        QHeaderView::section { background-color: #FF9F1C; color: white; padding: 4px; border: 1px solid #FFE8D6; font-weight: bold; }
        QProgressBar { border: 2px solid #FF9F1C; border-radius: 5px; background-color: #FFE8D6; text-align: center; }
        QProgressBar::chunk { background-color: #FFBF69; }
    """,
    "Monochromatic Blues": """
        QDialog { background-color: #CAF0F8; }
        QPushButton { background-color: #023E8A; color: #90E0EF; border-radius: 5px; padding: 5px; }
        QPushButton:hover { background-color: #0077B6; }
        QComboBox { background-color: #023E8A; color: #90E0EF; border-radius: 5px; padding: 5px; }
        QComboBox QAbstractItemView { background: #023E8A; selection-background-color: #0077B6; }
        QLineEdit, QTextEdit { background-color: #FFFFFF; color: #90E0EF; }
        QTableWidget { background-color: #CAF0F8; border: none; }
        QTableWidget::item { background-color: #023E8A; color: #90E0EF; border: 1px solid #CAF0F8; font-weight: bold; }
        QLabel { color: #023E8A; }
        QHeaderView::section { background-color: #023E8A; color: #90E0EF; padding: 4px; border: 1px solid #CAF0F8; font-weight: bold; }
        QProgressBar { border: 2px solid #023E8A; border-radius: 5px; background-color: #CAF0F8; text-align: center; }
        QProgressBar::chunk { background-color: #0077B6; }
    """,
    "Forest Whispers": """
        QDialog { background-color: #E9C46A; }
        QPushButton { background-color: #2B9348; color: #80B918; border-radius: 5px; padding: 5px; }
        QPushButton:hover { background-color: #55A630; }
        QComboBox { background-color: #2B9348; color: #80B918; border-radius: 5px; padding: 5px; }
        QComboBox QAbstractItemView { background: #2B9348; selection-background-color: #55A630; }
        QLineEdit, QTextEdit { background-color: #FFFFFF; color: #80B918; }
        QTableWidget { background-color: #E9C46A; border: none; }
        QTableWidget::item { background-color: #2B9348; color: #80B918; border: 1px solid #E9C46A; font-weight: bold; }
        QLabel { color: #2B9348; }
        QHeaderView::section { background-color: #2B9348; color: #80B918; padding: 4px; border: 1px solid #E9C46A; font-weight: bold; }
        QProgressBar { border: 2px solid #2B9348; border-radius: 5px; background-color: #E9C46A; text-align: center; }
        QProgressBar::chunk { background-color: #55A630; }
    """,
    "Classic Neutrals": """
        QDialog { background-color: #F0EFEB; }
        QPushButton { background-color: #283618; color: #D4D4D4; border-radius: 5px; padding: 5px; }
        QPushButton:hover { background-color: #B7B7A4; }
        QComboBox { background-color: #283618; color: #D4D4D4; border-radius: 5px; padding: 5px; }
        QComboBox QAbstractItemView { background: #283618; selection-background-color: #B7B7A4; }
        QLineEdit, QTextEdit { background-color: #FFFFFF; color: #D4D4D4; }
        QTableWidget { background-color: #F0EFEB; border: none; }
        QTableWidget::item { background-color: #283618; color: #D4D4D4; border: 1px solid #F0EFEB; font-weight: bold; }
        QLabel { color: #283618; }
        QHeaderView::section { background-color: #283618; color: #D4D4D4; padding: 4px; border: 1px solid #F0EFEB; font-weight: bold; }
        QProgressBar { border: 2px solid #283618; border-radius: 5px; background-color: #F0EFEB; text-align: center; }
        QProgressBar::chunk { background-color: #B7B7A4; }
    """,
    "Vintage Charm": """
        QDialog { background-color: #F4F1DE; }
        QPushButton { background-color: #E07A5F; color: #3D405B; border-radius: 5px; padding: 5px; }
        QPushButton:hover { background-color: #81B29A; }
        QComboBox { background-color: #E07A5F; color: #3D405B; border-radius: 5px; padding: 5px; }
        QComboBox QAbstractItemView { background: #E07A5F; selection-background-color: #81B29A; }
        QLineEdit, QTextEdit { background-color: #FFFFFF; color: #3D405B; }
        QTableWidget { background-color: #F4F1DE; border: none; }
        QTableWidget::item { background-color: #E07A5F; color: #3D405B; border: 1px solid #F4F1DE; font-weight: bold; }
        QLabel { color: #3D405B; }
        QHeaderView::section { background-color: #E07A5F; color: #3D405B; padding: 4px; border: 1px solid #F4F1DE; font-weight: bold; }
        QProgressBar { border: 2px solid #E07A5F; border-radius: 5px; background-color: #F4F1DE; text-align: center; }
        QProgressBar::chunk { background-color: #81B29A; }
    """,
    "Dreamy Pastels": """
        QDialog { background-color: #FFD6A5; }
        QPushButton { background-color: #FFADAD; color: #FDFFB6; border-radius: 5px; padding: 5px; }
        QPushButton:hover { background-color: #CAFFBF; }
        QComboBox { background-color: #FFADAD; color: #FDFFB6; border-radius: 5px; padding: 5px; }
        QComboBox QAbstractItemView { background: #FFADAD; selection-background-color: #CAFFBF; }
        QLineEdit, QTextEdit { background-color: #FFFFFF; color: #FDFFB6; }
        QTableWidget { background-color: #FFD6A5; border: none; }
        QTableWidget::item { background-color: #FFADAD; color: #FDFFB6; border: 1px solid #FFD6A5; font-weight: bold; }
        QLabel { color: #FFADAD; }
        QHeaderView::section { background-color: #FFADAD; color: #FDFFB6; padding: 4px; border: 1px solid #FFD6A5; font-weight: bold; }
        QProgressBar { border: 2px solid #FFADAD; border-radius: 5px; background-color: #FFD6A5; text-align: center; }
        QProgressBar::chunk { background-color: #CAFFBF; }
    """,
    "Urban Chic": """
        QDialog { background-color: #ECECEC; }
        QPushButton { background-color: #2C2C54; color: #AAABB8; border-radius: 5px; padding: 5px; }
        QPushButton:hover { background-color: #474787; }
        QComboBox { background-color: #2C2C54; color: #AAABB8; border-radius: 5px; padding: 5px; }
        QComboBox QAbstractItemView { background: #2C2C54; selection-background-color: #474787; }
        QLineEdit, QTextEdit { background-color: #FFFFFF; color: #AAABB8; }
        QTableWidget { background-color: #ECECEC; border: none; }
        QTableWidget::item { background-color: #2C2C54; color: #AAABB8; border: 1px solid #ECECEC; font-weight: bold; }
        QLabel { color: #2C2C54; }
        QHeaderView::section { background-color: #2C2C54; color: #AAABB8; padding: 4px; border: 1px solid #ECECEC; font-weight: bold; }
        QProgressBar { border: 2px solid #2C2C54; border-radius: 5px; background-color: #ECECEC; text-align: center; }
        QProgressBar::chunk { background-color: #474787; }
    """
}


class SettingsDialog(QDialog):
    dialogClosed = pyqtSignal()

    def __init__(self, parent=None, nobody_cache=None):
        super(SettingsDialog, self).__init__(parent)
        self.setModal(True)  # This makes the dialog modal
        self.setAttribute(Qt.WA_DeleteOnClose)  # Ensures it closes with the application
        self.Nobody = nobody_cache  # Receive the parameter here
        self.setWindowTitle('Creator')
        self.layout = QVBoxLayout()
        self.setupUI()

        executable_path = os.path.abspath(sys.argv[0])
        executable_dir = os.path.dirname(executable_path)
        self.cacheDirectory = os.path.join(executable_dir, 'Caches')

        # Define the URL and the descriptive text with HTML for line breaks
        self.predefinedURL = "https://soundcloud.com/octxxiii"
        predefinedText = """
            <p style=\"text-align: center;\">
            <h1>Youtify Ver. 1.0</h1>
            Youtube/Music Converter & Player
            </p>
            <br>
            <p>
            <h3>사용방법</h3>
            <ol>
            1. 브라우저에서 원하는 영상 또는 플레이리스트를 선택<br>
            2. CopyURL 버튼 클릭 또는 URL 입력 후 검색 버튼 클릭<br>
            3. Table에 추가된 영상의 옵션(포맷 등) 선택 후 다운로드<br>
            </ol>
            <h3>최근 업데이트 내역</h3>
            <ul>
            <li>2025-05-08: 최소화 버튼 비활성화 문제 해결, 다운로드/삭제 버튼 사이즈 통일, 안내문 최신화</li>
            <li>2024-04-08: 전체 선택 삭제 후 체크 해제 오류 수정, 브라우저 타이틀 표시, 비디오/오디오 컨트롤 패널 추가</li>
            <li>2024-04-05: 클립보드 복사 에러 수정, 새로고침/사운드클라우드 버튼 추가</li>
            <li>2024-04-01: 브라우저/다운로드 창 각각 숨기기, 유튜브/뮤직 홈 버튼 추가</li>
            <li>2024-03-28: 브라우저 show&hide, nav, url copy, 테마 가시성 증가, black/monokai 테마 추가</li>
            <li>2024-03-27: 중복 url 검색 방지, url 삭제 후 재검색 가능</li>
            <li>2024-03-26: 썸네일/제목/포맷 가시화, 체크박스 선택 다운로드, 경로 지정, 제목 수정 다운로드 등</li>
            </ul>
            <h2>
            Creator: OctXXIII<br>
            Distribution date: 2024-04-01
            </h2>
        """

        self.textArea = QTextEdit()
        self.textArea.setHtml(predefinedText)  # Use setHtml to apply HTML formatting
        self.textArea.setReadOnly(True)
        self.textArea.setContentsMargins(0, 0, 0, 0)

        self.actionButton = QPushButton('Visit Created by Link', self)
        self.actionButton.clicked.connect(self.performAction)

        self.clearCacheButton = QPushButton('', self)
        self.clearCacheButton.clicked.connect(self.clearCache)

        self.layout.addWidget(self.textArea)
        self.layout.addWidget(self.actionButton)
        self.layout.addWidget(self.clearCacheButton)  # Add the new button to the layout

        self.setLayout(self.layout)
        self.setFixedSize(400, 300)

        self.updateCacheSize()

    def closeEvent(self, event):
        """ Reimplement the close event to emit the dialogClosed signal """
        self.dialogClosed.emit()  # Emit the signal when the dialog is about to close
        super().closeEvent(event)  # Proceed with the default close event

    def setupUI(self):
        cache_path = os.path.expanduser(f"~/Library/Caches/Nobody")

    def performAction(self):
        # Implement the action to open the URL in a web browser
        QDesktopServices.openUrl(QUrl(self.predefinedURL))
        self.close()

    def updateCacheSize(self):
        cache_size_mb = self.getDirectorySize(self.cacheDirectory) / (1024 * 1024)  # Convert bytes to MB
        self.clearCacheButton.setText(f"Clear Cache: {cache_size_mb:.2f}MB")

    def getDirectorySize(self, directory):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    def clearCache(self):
        # Clear the cache of the default web engine profile
        QWebEngineProfile.defaultProfile().clearHttpCache()

        # Optionally remove all files in the cache directory manually
        for filename in os.listdir(self.cacheDirectory):
            file_path = os.path.join(self.cacheDirectory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

        # Assuming self.browser is defined in this class or accessible via a class attribute
        if hasattr(self, 'browser'):
            self.browser.reload()

        self.updateCacheSize()  # Update the displayed cache size


class CheckBoxHeader(QHeaderView):
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setSectionResizeMode(QHeaderView.Fixed)
        self.setDefaultAlignment(Qt.AlignCenter)
        self.setCheckBox()

    def setCheckBox(self):
        self.cb = QCheckBox(self)
        self.cb.setChecked(False)
        self.sectionResized.connect(self.resizeCheckBox)
        self.cb.clicked.connect(self.selectAll)
        self.cb.setStyleSheet("QCheckBox { margin-left: 6px; margin-right: 6px; }")  # Adjust the margins for alignment

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resizeCheckBox()

    def resizeCheckBox(self):
        rect = self.sectionViewportPosition(0)
        self.cb.setGeometry(rect, 0, self.sectionSize(0), self.height())
        self.parent().setColumnWidth(0, self.cb.sizeHint().width())  # Set column width to checkbox width

    def selectAll(self):
        check_state = self.cb.isChecked()
        for row in range(self.parent().rowCount()):
            item = self.parent().item(row, 0)  # Assuming checkboxes are in the first column
            if item and isinstance(item, QTableWidgetItem):
                item.setCheckState(Qt.Checked if check_state else Qt.Unchecked)

    def updateState(self):
        all_checked = self.parent().rowCount() > 0
        for row in range(self.parent().rowCount()):
            item = self.parent().item(row, 0)
            if item is None or item.checkState() != Qt.Checked:
                all_checked = False
                break

        self.cb.setChecked(all_checked)


class VideoHandler(QObject):
    @pyqtSlot(float)
    def handleVideoDuration(self, duration):
        print("Video duration:", duration)


class VideoDownloader(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settingsDialog = None
        self.Nobody = "~/Library/Caches/Nobody"  # Define here
        # 최소화 버튼 활성화
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        # 실행 파일이 있는 폴더를 기반으로 캐시 디렉토리 설정
        executable_path = os.path.abspath(sys.argv[0])
        executable_dir = os.path.dirname(executable_path)
        self.cacheDirectory = os.path.join(executable_dir, 'Caches')

        # 지정된 경로에 폴더가 없으면 폴더 생성
        if not os.path.exists(self.cacheDirectory):
            os.makedirs(self.cacheDirectory)

        # 캐시 및 기타 설정 구성
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentStoragePath(self.cacheDirectory)
        profile.setHttpCacheType(QWebEngineProfile.NoCache)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)

        settings = profile.settings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)

        self.setWindowTitle("Youtify")
        self.player = QMediaPlayer(self)
        self.video_info_list = []

        self.videoDuration = 0
        self.currentTime = 0
        self.originalTitle = ""  # Initialize the title attribute
        self.isPlaying = False  # Initialize the attribute to False

        self.initUI()

        self.scrollTimer = QTimer(self)
        self.scrollTimer.timeout.connect(self.scrollTitle)
        self.scrollTimer.start(300)  # Scroll title every 300 ms

        self.predefinedURL = "https://soundcloud.com/octxxiii"

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.on_search()
        elif event.key() == Qt.Key_Escape:
            self.lower()
        else:
            super().keyPressEvent(event)  # Handle other key events normally

    def get_video_info(url):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'noplaylist': True,
            'forcetitle': True,
            'skip_download': True,  # We're not downloading the video
            'extract_flat': True,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # or 'mkv' if needed
            }],
            'ffmpeg_location': get_ffmpeg_path(),  # 동적으로 ffmpeg 경로 설정
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            if 'entries' in result:
                # Can handle a playlist or a list of videos, takes the first video
                video = result['entries'][0]
            else:
                # Just a single video
                video = result

            return {
                'duration': video.get('duration'),
                'title': video.get('title'),
                'url': video.get('webpage_url'),
            }

    def initUI(self):
        # Left Layout: Web Browser View and Navigation Buttons
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.youtube.com"))
        self.homePageUrl = QUrl("https://www.youtube.com")
        self.musicPageUrl = QUrl("https://music.youtube.com")
        self.SCPageUrl = QUrl("https://m.soundcloud.com/")

        self.toggleDownButton = QPushButton("💥", self)
        self.toggleDownButton.clicked.connect(self.toggleBrowser)
        self.toggleDownButton.setFixedSize(30, 30)

        # Navigation Buttons
        self.backButton = QPushButton('👈')
        self.backButton.clicked.connect(self.browser.back)
        self.refreshButton = QPushButton('🔄')
        self.refreshButton.setFixedSize(30, 30)
        self.refreshButton.clicked.connect(self.browser.reload)
        self.homeButton = QPushButton()
        self.homeButton.setFixedSize(30, 30)
        self.homeButton.setIcon(QIcon(':/homeIcon'))
        self.homeButton.clicked.connect(lambda: self.browser.setUrl(self.homePageUrl))
        self.musicButton = QPushButton()
        self.musicButton.setFixedSize(30, 30)
        self.musicButton.setIcon(QIcon(':/musicIcon'))
        self.musicButton.clicked.connect(lambda: self.browser.setUrl(self.musicPageUrl))
        self.SCButton = QPushButton()
        self.SCButton.setFixedSize(30, 30)
        self.SCButton.setIcon(QIcon(':/soundCloudIcon'))
        self.SCButton.clicked.connect(lambda: self.browser.setUrl(self.SCPageUrl))
        self.forwardButton = QPushButton('👉')
        self.forwardButton.clicked.connect(self.browser.forward)

        # Navigation Layout
        self.navLayout = QHBoxLayout()
        self.navLayout.addWidget(self.backButton)
        self.navLayout.addWidget(self.forwardButton)
        self.navLayout.addWidget(self.refreshButton)
        self.navLayout.addWidget(self.homeButton)  # Adding the home button between back and forward
        self.navLayout.addWidget(self.musicButton)
        # self.navLayout.addWidget(self.SCButton)
        self.navLayout.addWidget(self.toggleDownButton)

        # Left Widget for Browser and Navigation
        self.browWidget = QWidget()
        self.leftLayout = QVBoxLayout(self.browWidget)
        self.leftLayout.addLayout(self.navLayout)
        self.leftLayout.addWidget(self.browser)

        # Right Layout: Existing UI Elements
        self.setupRightLayout()

        fixedWidth = 450
        self.downLayoutWidget.setFixedWidth(fixedWidth)

        # Splitter for dividing the layout into left and right sections
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.browWidget)  # Adding left widget to the splitter
        self.splitter.addWidget(self.downLayoutWidget)

        # Prevent the right widget from resizing by fixing its maximum size
        self.downLayoutWidget.setMaximumSize(QSize(fixedWidth, 16777215))

        # Main Layout
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.addWidget(self.splitter)
        self.setLayout(mainLayout)

        # Adjust initial split sizes
        self.splitter.setSizes([500, 300])
        self.browser.setMinimumSize(500, 300)
        self.browser.setZoomFactor(0.8)

        self.browser.loadFinished.connect(self.updateButtonStates)

    def setupRightLayout(self):
        # Create a widget for the right side layout
        self.downLayoutWidget = QWidget()
        self.downLayoutWidget.setContentsMargins(0, 0, 0, 0)
        self.downLayoutWidget.setFixedSize(450, 560)
        self.rightLayout = QVBoxLayout(self.downLayoutWidget)

        # Initialize all widgets for the right side layout\
        self.theme_selector = QComboBox()
        self.theme_selector.setFixedSize(356, 30)
        self.browHideButton = QPushButton('🦕')
        self.browHideButton.setFixedSize(30, 30)
        self.browHideButton.clicked.connect(self.toggleBrowWidgetVisibility)
        self.createrButton = QPushButton('💬')
        self.createrButton.setFixedSize(30, 30)
        self.createrButton.clicked.connect(self.openSettingsDialog)
        self.copyUrlButton = QPushButton('📋')
        self.copyUrlButton.setFixedSize(30, 30)
        self.search_url = QLineEdit()
        self.search_url.setStyleSheet("""
            QLineEdit {
                border: 2px solid #555555;  /* Adjust border color as needed */
                border-radius: 5px;  /* Adjust for more or less rounding */
                padding: 0px;
                background-color: #2D2D2D;  /* Adjust background color as needed */
                color: #ffffff;  /* Adjust text color as needed */
            }
        """)
        self.search_url.setFixedSize(356, 30)
        self.search_url.setClearButtonEnabled(True)
        self.search_button = QPushButton('🔍')
        self.search_button.setFixedSize(30, 30)
        self.download_list = QPushButton('📍')
        self.download_list.setFixedSize(100, 30)
        self.later_list = QPushButton('📌')
        self.later_list.setFixedSize(100, 30)
        self.video_table = QTableWidget()
        self.download_button = QPushButton('📥')
        # self.download_button.setFixedSize(200, 30)
        self.delete_button = QPushButton('❌')
        # self.delete_button.setFixedSize(200, 30)
        
        # rainbow_cat.gif를 표시할 QLabel 추가
        self.cat_label = QLabel(self)
        self.cat_movie = QMovie('rainbow_cat.gif')
        self.cat_movie.setScaledSize(QSize(20, 20))
        self.cat_label.setMovie(self.cat_movie)
        self.cat_label.setFixedSize(20, 20)
        self.cat_movie.start()  # 애니메이션 시작
        
        self.status_label = QLabel('Ready')
        self.progress_bar = QProgressBar()

        # 플레이어 컨트롤 버튼
        self.back_button = QPushButton("⏮", self)
        self.back_button.clicked.connect(self.play_back)
        self.play_button = QPushButton("▶", self)
        self.play_button.clicked.connect(self.play)
        self.next_button = QPushButton("⏭", self)
        self.next_button.clicked.connect(self.play_next)
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Align text to the left and vertically center
        self.title_label.setStyleSheet("""
                QLabel {
                    color: white;
                    border: 2px solid #555;
                    border-radius: 5px;
                    background-color: #333;
                    padding: 4px 4px 4px 4px;
                }
            """)
        self.title_label.setWordWrap(False)

        self.theme_selector.addItems(themes.keys())
        self.theme_selector.currentIndexChanged.connect(self.applySelectedTheme)
        self.search_button.clicked.connect(self.on_search)
        self.copyUrlButton.clicked.connect(self.copyUrlToClipboard)
        self.download_button.clicked.connect(self.on_download)
        self.delete_button.clicked.connect(self.on_delete_selected)

        self.setupVideoTable()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.toggle_loading_animation)
        self.direction = 1

        settingsLayout = QHBoxLayout()
        settingsLayout.setContentsMargins(0, 0, 0, 0)  # Set the margins to 0
        settingsLayout.setSpacing(5)  # Set the spacing between widgets
        settingsLayout.addWidget(self.browHideButton)
        settingsLayout.addWidget(self.theme_selector)
        settingsLayout.addWidget(self.createrButton)

        titleLayout = QHBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)
        titleLayout.addWidget(self.title_label)

        playerLayout = QHBoxLayout()
        playerLayout.setContentsMargins(0, 0, 0, 0)
        playerLayout.setSpacing(5)
        playerLayout.addWidget(self.back_button)
        playerLayout.addWidget(self.play_button)
        playerLayout.addWidget(self.next_button)

        # self.positionSlider = QSlider(Qt.Horizontal, self)
        # self.positionSlider.setRange(0, 100)
        # self.durationLabel = QLabel("00:00 / 00:00", self)
        # self.setupMediaControls()
        #
        # positionLayout = QHBoxLayout()
        # positionLayout.setContentsMargins(0, 0, 0, 0)
        # positionLayout.setSpacing(5)
        # positionLayout.addWidget(self.positionSlider)
        # positionLayout.addWidget(self.durationLabel)

        # Group related widgets
        searchLayout = QHBoxLayout()
        searchLayout.setContentsMargins(0, 0, 0, 0)  # Set the margins to 0
        searchLayout.setSpacing(5)  # Set the spacing between widgets
        searchLayout.addWidget(self.copyUrlButton)
        searchLayout.addWidget(self.search_url)
        searchLayout.addWidget(self.search_button)
        # searchLayout.addStretch(1)  # This will push everything to the left

        listLayout = QHBoxLayout()

        statusLayout = QHBoxLayout()
        statusLayout.addWidget(self.progress_bar)
        statusLayout.addWidget(self.status_label)

        actionLayout = QHBoxLayout()
        actionLayout.addWidget(self.download_button)
        actionLayout.addWidget(self.delete_button)
        actionLayout.addWidget(self.cat_label)  # cat_label을 레이아웃에 추가

        # Add grouped layouts to the main right layout
        self.rightLayout.addLayout(settingsLayout)
        self.rightLayout.addLayout(titleLayout)
        self.rightLayout.addLayout(playerLayout)
        # self.rightLayout.addLayout(positionLayout)
        self.rightLayout.addLayout(searchLayout)
        self.rightLayout.addWidget(self.video_table)
        self.rightLayout.addLayout(statusLayout)
        self.rightLayout.addLayout(actionLayout)
        # self.rightLayout.addLayout(settingsLayout)

        self.browser.titleChanged.connect(self.updateTitle)
        self.resetTimer = QTimer(self)  # Timer for delaying the reset of media controls
        self.resetTimer.setSingleShot(True)  # Ensure the timer only triggers once per timeout
        self.resetTimer.timeout.connect(self.performResetMediaControls)  # Connect timeout signal to the reset method
        self.browser.urlChanged.connect(self.checkAndTriggerReset)

        self.applySelectedTheme()  # Apply the default theme

    def checkAndTriggerReset(self, url):
        """Check the URL and trigger the reset with a delay if it is the YouTube homepage."""
        if url.toString() == "https://www.youtube.com/":
            self.resetTimer.start(1000)  # Start the timer with a delay of 1000 milliseconds (1 second)

    def performResetMediaControls(self):
        """Reset the media controls."""
        self.play_button.setText("▶")  # Reset to play icon

    # def setupMediaControls(self):
    #     # Timer to update the position slider and duration label
    #     self.updateTimer = QTimer(self)
    #     self.updateTimer.timeout.connect(self.updateMediaStatus)
    #     self.updateTimer.start(1000)  # Update every second
    #
    #     # Connect the slider's valueChanged signal to the seekVideo method
    #     self.positionSlider.valueChanged.connect(self.seekVideo)
    #     self.positionSlider.sliderReleased.connect(
    #         self.onSliderRelease)  # Ensure seeking only occurs after user interaction

    def updateMediaStatus(self):
        """Check the media status and update controls."""
        jsCode = """
        (function() {
            var video = document.querySelector('video');
            if (video) {
                return {
                    playing: !video.paused && !video.ended && video.readyState > 2,
                    currentTime: video.currentTime,
                    duration: video.duration
                };
            }
            return null;
        })();
        """
        self.browser.page().runJavaScript(jsCode, self.onMediaStatusReceived)

    @pyqtSlot(object)
    def onMediaStatusReceived(self, result):
        if result:
            # Update the slider and duration label
            current_time = result.get('currentTime', 0)
            duration = result.get('duration', 0)
            if duration > 0:
                self.positionSlider.setValue(int((current_time / duration) * 100))
                self.update_duration_label(current_time, duration)

            # Manage scrolling based on playback state
            if result.get('playing', False):
                if not self.isPlaying:
                    self.isPlaying = True
                    self.startScrolling()  # Start scrolling if the video is playing
            else:
                if self.isPlaying:
                    self.isPlaying = False
                    self.stopScrolling()  # Stop scrolling if the video is not playing
        else:
            # print("No valid video found or video not ready.")
            self.stopScrolling()  # Ensure scrolling is stopped if video isn't ready

    def startScrolling(self):
        """Start the scroll timer."""
        if not self.scrollTimer.isActive():
            self.scrollTimer.start(300)

    def stopScrolling(self):
        """Stop the scroll timer."""
        if self.scrollTimer.isActive():
            self.scrollTimer.stop()

    def updateUISliderAndLabel(self, current_time, duration):
        if duration > 0:
            self.positionSlider.setValue(int((current_time / duration) * 100))
            self.update_duration_label(current_time, duration)
        else:
            print("No valid video or duration available.")

    def seekVideo(self):
        value = self.positionSlider.value()
        # Convert slider value to media time
        jsCode = f"""
        (function() {{
            var video = document.querySelector('video');
            if (video) {{
                var seekTime = video.duration * ({value} / 100);
                video.currentTime = seekTime;
            }}
        }})();
        """
        self.browser.page().runJavaScript(jsCode)

    # def onSliderRelease(self):
    #     # Calls seekVideo only when the user releases the slider
    #     self.seekVideo()
    #
    # def update_duration_label(self, current_time, duration):
    #     self.durationLabel.setText(f"{self.format_time(current_time)} / {self.format_time(duration)}")

    # def format_time(self, seconds):
    #     hours = int(seconds // 3600)
    #     minutes = int((seconds % 3600) // 60)
    #     seconds = int(seconds % 60)
    #     if hours > 0:
    #         return f"{hours:02}:{minutes:02}:{seconds:02}"
    #     else:
    #         return f"{minutes:02}:{seconds:02}"

    def scrollTitle(self):
        """Scrolls the video title if it is longer than the display area."""
        if not self.originalTitle:  # Check if the title is not set
            return  # Skip scrolling if there's no title

        displayLength = 50  # Adjust based on your display needs
        titleLength = len(self.originalTitle)

        # Update the title display based on current scroll position
        if titleLength > displayLength:
            # Logic to scroll the title smoothly
            scrolledTitle = self.originalTitle[self.scrollPosition:] + '   ' + self.originalTitle
            self.title_label.setText(scrolledTitle[:displayLength])
            self.scrollPosition = (self.scrollPosition + 1) % titleLength
        else:
            self.title_label.setText(self.originalTitle)
            self.scrollTimer.stop()  # Stop the timer if no scrolling is needed

    def updateTitle(self, newTitle):
        """Updates the title displayed on the UI."""
        self.originalTitle = newTitle
        self.scrollPosition = 0  # Reset scroll position with new title
        if len(newTitle) > 50:  # Assuming 20 is the max visible chars
            if not self.scrollTimer.isActive():
                self.scrollTimer.start(300)
        else:
            self.scrollTimer.stop()
        self.title_label.setText(newTitle)  # Set title immediately without scrolling

        # 재생 상태 확인 및 버튼 업데이트
        self.checkPlaybackState()

    def checkPlaybackState(self):
        jsCode = """
        (function() {
            var video = document.querySelector('video');
            if (video) {
                return video.paused ? 'paused' : 'playing';
            }
            return 'unknown';
        })();
        """
        self.browser.page().runJavaScript(jsCode, self.updatePlayButtonIcon)

    def startScrolling(self):
        # Only start the timer if the title needs scrolling
        if len(self.originalTitle) * 50 > self.title_label.width():
            self.scrollTimer.start(300)  # Adjust scrolling speed as needed

    def checkNeedForScrolling(self):
        # Determine if the title's length exceeds the label's display capacity
        if len(self.originalTitle) * 50 > self.title_label.width():
            self.scrollTimer.start(300)  # Restart scrolling with a delay
        else:
            self.title_label.setText(self.originalTitle)

    def updateButtonStates(self):
        current_url = self.browser.url().toString()
        is_youtube_music = "music.youtube.com" in current_url

        # 모든 버튼을 항상 표시
        self.play_button.show()
        self.next_button.show()
        self.back_button.show()

        # YouTube Music에서는 컨트롤이 작동하지 않는다는 메시지만 표시
        if is_youtube_music:
            self.title_label.setText("YouTube Music에서는 컨트롤이 작동하지 않습니다.")
        else:
            self.title_label.setText("")

    def play_back(self):
        jsCode = """
        (function() {
            const host = window.location.host;
            if (host.includes('music.youtube.com')) {
                var prevBtn = document.querySelector('button.previous-button');
                if (prevBtn && !prevBtn.disabled) prevBtn.click();
            } else if (host.includes('soundcloud.com')) {
                var prevBtn = document.querySelector('.playControls__prev');
                if (prevBtn) prevBtn.click();
            } else if (host.includes('youtube.com')) {
                window.history.back();
            }
        })();
        """
        self.browser.page().runJavaScript(jsCode)

    def play(self):
        jsCode = """
        (function() {
            const host = window.location.host;
            if (host.includes('music.youtube.com')) {
                var playBtn = document.querySelector('button.play-pause-button');
                if (playBtn && !playBtn.disabled) {
                    playBtn.click();
                    // 버튼의 aria-label이 '일시정지'면 재생중, '재생'이면 멈춤
                    var label = playBtn.getAttribute('aria-label') || playBtn.title || '';
                    if (label.includes('일시정지') || label.toLowerCase().includes('pause')) {
                        return 'playing';
                    } else {
                        return 'paused';
                    }
                }
            } else if (host.includes('youtube.com')) {
                var video = document.querySelector('video');
                if (video) {
                    if (video.paused) {
                        video.play();
                        return 'playing';
                    } else {
                        video.pause();
                        return 'paused';
                    }
                }
            } else if (host.includes('soundcloud.com')) {
                var playBtn = document.querySelector('.playControls__play');
                if (playBtn) {
                    playBtn.click();
                    return playBtn.classList.contains('playing') ? 'playing' : 'paused';
                }
            }
            return 'unknown';
        })();
        """
        self.browser.page().runJavaScript(jsCode, self.updatePlayButtonIcon)

    @pyqtSlot(str)
    def updatePlayButtonIcon(self, state):
        if state == 'playing':
            self.play_button.setText("⏸")  # Update to pause icon
        elif state == 'paused':
            self.play_button.setText("▶")  # Update to play icon
        else:
            # Optionally handle 'unknown' state or other states if necessary
            pass

    def play_next(self):
        # JavaScript 코드로 다음 영상으로 이동하고 재생 여부 확인
        jsCode = """
        (function() {
            const host = window.location.host;
            if (host.includes('youtube.com')) {
                document.querySelector('.ytp-next-button')?.click();
                var video = document.querySelector('video');
                if (video) {
                    // Delay to ensure the video state is updated after the next button is clicked
                    setTimeout(function() {
                        if (!video.paused) {
                            video.play();
                            return 'playing';
                        } else {
                            return 'paused';
                        }
                    }, 100); // Adjust delay as needed to match loading times
                }
            } else if (host.includes('soundcloud.com')) {
                document.querySelector('.skipControl__next')?.click();
                // Assuming SoundCloud plays automatically, return 'playing'
                return 'playing';
            }
            return 'unknown';
        })();
        """
        # JavaScript 실행 후 반환된 재생 상태에 따라 버튼 아이콘 업데이트
        self.browser.page().runJavaScript(jsCode, self.updatePlayButtonIcon)

    def setupVideoTable(self):
        self.video_table.setColumnCount(4)  # Adjust the count as necessary
        self.video_table.setHorizontalHeaderLabels(['', 'Thumbnail', 'Title', 'Format'])
        self.header = CheckBoxHeader()
        self.video_table.setHorizontalHeader(self.header)
        self.header.cb.clicked.connect(self.header.selectAll)
        header = self.video_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.video_table.horizontalHeader().setVisible(True)
        self.video_table.verticalHeader().setVisible(False)
        self.video_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.video_table.setShowGrid(False)  # This line is corrected
        self.video_table.setColumnWidth(0, 100)
        self.video_table.setColumnWidth(1, 150)
        self.video_table.setColumnWidth(2, 300)
        self.video_table.setColumnWidth(3, 180)

    def copyUrlToClipboard(self):
        currentUrl = self.browser.url().toString()
        print(f"Current URL: {currentUrl}")  # Debug print
        clipboard = QApplication.clipboard()
        clipboard.setText(currentUrl)
        self.search_url.setText(currentUrl)
        self.search_url.clear()
        self.search_url.setText(currentUrl)
        self.on_search()

    def navigateToLink(self):
        # Handle the predefined URL here. This could involve opening the URL in a web browser,
        # or performing another action based on the URL.
        print(f"Navigate to: {self.predefinedURL}")
        # Example: Open the URL in a web browser
        QDesktopServices.openUrl(QUrl(self.predefinedURL))

    def openSettingsDialog(self):
        if not self.settingsDialog:
            self.settingsDialog = SettingsDialog(
                self)  # Ensure the dialog has a parent specified for proper object lifetime management
            self.settingsDialog.dialogClosed.connect(self.refreshBrowser)
            self.settingsDialog.finished.connect(self.onSettingsDialogClosed)
            self.settingsDialog.show()
        else:
            self.settingsDialog.raise_()  # Brings the dialog to the front if already open

    def onSettingsDialogClosed(self):
        self.settingsDialog.deleteLater()
        self.settingsDialog = None  # Clear the reference after the dialog is closed

    def refreshBrowser(self):
        """ Method to refresh the browser when the settings dialog is closed """
        if hasattr(self, 'browser') and self.browser is not None:
            self.browser.reload()
        else:
            print("Browser attribute is not set or is None")

    def toggleBrowser(self):
        if self.downLayoutWidget.isVisible():
            self.downLayoutWidget.hide()
            self.toggleDownButton.setText("😜")
            self.adjustMainLayoutSize()
        else:
            self.downLayoutWidget.show()
            self.toggleDownButton.setText("💥")
            self.resetMainLayoutSize()

    def toggleBrowWidgetVisibility(self):
        if self.browWidget.isVisible():
            self.browWidget.hide()
            self.browHideButton.setText('💥')  # Example icon when visible
            self.adjustMainLayoutSize()

        else:
            self.browWidget.show()
            self.browHideButton.setText('🦕')  # Example icon when hidden
            self.resetMainLayoutSize()

    def adjustMainLayoutSize(self):
        if not self.browWidget.isVisible():
            # 윈도우가 축소되지 않도록 최소 크기 설정
            self.setMinimumSize(450, 560)

            # 오른쪽 위젯을 맞추기 위해 메인 윈도우 크기 조정
            # 참고: 원하는 다른 동작이 있다면 조정할 수 있습니다.
            self.resize(450, 560)

            # downLayoutWidget에 선호하는 최소 크기가 있는지 확인합니다.
            self.downLayoutWidget.setMinimumSize(450, 560)

            # browWidget의 최소 크기를 조정하여 완전한 축소가 가능하도록 합니다.
            self.browWidget.setMinimumSize(0, 0)
        else:
            # browWidget이 다시 표시되면 윈도우가 확장되도록 합니다.
            # 전체 윈도우에 합리적인 최소 크기를 설정합니다.
            self.setMinimumSize(980, 560)

            # 두 위젯을 수용하기 위해 메인 윈도우 크기 조정
            # 필요에 따라 숨기기 전의 이전 크기를 저장하고 복원할 수 있습니다.
            self.resize(980, 560)

            # 두 위젯의 최소 크기를 복원합니다.
            self.browWidget.setMinimumSize(500, 560)  # 컨텐츠에 맞게 필요에 따라 조정합니다.
            self.downLayoutWidget.setMinimumSize(450, 560)

    def resetMainLayoutSize(self):
        # When making the browser visible again, adjust the layout to accommodate both widgets.
        self.setMinimumSize(1100, 560)
        self.browWidget.setMinimumSize(500, 560)
        self.downLayoutWidget.setMinimumSize(450, 560)

        # Adjust splitter sizes to distribute space according to your preference.
        self.splitter.setSizes([500, 450])

    def applySelectedTheme(self):
        theme_name = self.theme_selector.currentText()
        if theme_name in themes:
            self.setStyleSheet(themes[theme_name])

    def center_on_screen(self):
        # Get the main screen's geometry
        screen_geometry = QApplication.desktop().screenGeometry()

        # Calculate the center point
        center_point = screen_geometry.center()

        # Set the center point of the dialog
        self.move(center_point - self.rect().center())

    def search_duplicate_urls(self, url):
        return any(url == video_info[1] for video_info in self.video_info_list)

    def toggle_loading_animation(self):
        current_value = self.progress_bar.value()
        max_value = self.progress_bar.maximum()
        min_value = self.progress_bar.minimum()

        if current_value >= max_value or current_value <= min_value:
            self.direction *= -1
            self.animation_timer.stop()  # Stop the animation when loading is complete
        else:
            new_value = current_value + self.direction * 5
            self.progress_bar.setValue(new_value)

    def add_video_info(self, title, url):
        # Check if the URL is already in the list
        if not any(url == existing_url for _, existing_url in self.video_info_list):
            self.video_info_list.append((title, url))
            # Update the UI accordingly, e.g., adding a row to the table

    def is_duplicate_url(self, url):
        return any(url == existing_url for _, existing_url in self.video_info_list)

    def delete_selected_videos(self):
        # This assumes you have a method to determine which videos are selected for deletion
        selected_indexes = self.get_selected_video_indexes()
        self.video_info_list = [info for idx, info in enumerate(self.video_info_list) if idx not in selected_indexes]
        # Refresh the UI to reflect the changes

    @pyqtSlot()
    def on_search(self):
        url = self.search_url.text().strip()

        if self.is_duplicate_url(url):
            self.status_label.setText("이 비디오는 이미 목록에 추가되었습니다.")
            return

        self.search_button.setEnabled(False)
        self.animation_timer.start(50)
        self.set_status('로딩 중...')
        self.progress_bar.setRange(0, 0)  # Set to indeterminate mode

        self.search_thread = Searcher(url)
        self.search_thread.updated_list.connect(self.update_video_list)
        self.search_thread.finished.connect(self.search_finished)
        self.search_thread.finished.connect(self.enable_search_button)
        self.search_thread.finished.connect(self.check_results)  # Connect to a new slot to check for results
        self.search_thread.start()

    def check_results(self):
        # Assuming self.video_info_list is updated with search results
        if not self.video_info_list:
            self.status_label.setText("검색 결과가 없습니다.")

    def enable_search_button(self):
        self.search_button.setEnabled(True)
        self.progress_bar.setRange(0, 100)  # Reset the progress bar range

    def set_status(self, message):
        self.status_label.setText(message)

    @pyqtSlot(str, str)
    def list_update(self, title, thumbnail_url):
        row_position = self.video_table.rowCount()
        self.video_table.insertRow(row_position)

        checkbox = QTableWidgetItem()
        checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        checkbox.setCheckState(Qt.Unchecked)
        checkbox.stateChanged.connect(lambda: self.header.updateState())

        self.video_table.setItem(row_position, 0, checkbox)

        title_item = QTableWidgetItem(title)
        title_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)  # Allow editing
        self.video_table.setItem(row_position, 2, title_item)

        if thumbnail_url:
            response = requests.get(thumbnail_url)
            pixmap = QPixmap()
            if pixmap.loadFromData(response.content):
                pixmap_resized = pixmap.scaled(30, 30, Qt.KeepAspectRatio)
                thumbnail_item = QTableWidgetItem()
                thumbnail_item.setData(Qt.DecorationRole, pixmap_resized)
                self.video_table.setItem(row_position, 1, thumbnail_item)

    def select_download_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "다운로드 디렉토리 선택", os.path.expanduser("~"))
        return dir_path if dir_path else None

    @pyqtSlot()
    def on_download(self):
        selected_videos = []
        invalid_selection = False

        for row in range(self.video_table.rowCount()):
            checkbox = self.video_table.item(row, 0)
            if (checkbox and checkbox.checkState() == Qt.Checked) or not checkbox:
                # Fetch the modified title from the table
                title_item = self.video_table.item(row, 2)  # Get the title item
                modified_title = title_item.text() if title_item else "Untitled"
                video_url = self.video_info_list[row][1]
                format_combo_box = self.video_table.cellWidget(row, 3)
                selected_format_detail = format_combo_box.currentText() if format_combo_box else None

                if selected_format_detail in ["AUDIO", "VIDEO", "No available formats"]:
                    invalid_selection = True
                    break

                format_id = selected_format_detail.split(' - ')[0] if selected_format_detail else 'best'
                selected_videos.append((modified_title, video_url, format_id))

        if invalid_selection:
            self.status_label.setText("각 비디오에 대해 특정 포맷을 선택해 주세요.")
            return

        if selected_videos:
            self.start_download(selected_videos)
        else:
            self.status_label.setText("다운로드할 비디오를 최소 하나 이상 선택해 주세요.")

    @pyqtSlot()
    def on_delete_selected(self):
        # Initialize a variable to check if at least one checkbox remains checked
        at_least_one_checked = False

        for row in reversed(range(self.video_table.rowCount())):
            checkbox_item = self.video_table.item(row, 0)  # Assuming checkboxes are in the first column.
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                # Remove from video_info_list
                if row < len(self.video_info_list):
                    self.video_info_list.pop(row)
                # Remove from table
                self.video_table.removeRow(row)
                self.header.updateState()
                self.status_label.setText("삭제 완료.")
            else:
                at_least_one_checked = True

    def start_download(self, selected_videos):
        # This method should initiate the download process for the selected videos.
        # Ensure you have the Downloader class properly defined to accept the videos and download directory.

        download_directory = self.select_download_directory()
        if not download_directory:
            self.status_label.setText("유효한 다운로드 디렉토리를 선택해 주세요.")
            return

        # Initialize and start the Downloader thread
        self.downloader_thread = Downloader(selected_videos, download_directory)
        self.downloader_thread.download_failed.connect(self.download_failed)
        self.downloader_thread.updated_status.connect(self.set_status)
        self.downloader_thread.updated_progress.connect(self.update_progress_bar)
        self.downloader_thread.start()

    def download_finished(self):
        self.status_label.setText('다운로드 완료.')
        QMessageBox.information(self, '다운로드 완료', '모든 파일이 성공적으로 다운로드되었습니다.')

    def download_failed(self, message):
        self.set_status(f"다운로드 실패: {message}")
        QMessageBox.warning(self, '다운로드 실패', f'다운로드 중 오류가 발생했습니다:\n{message}')

    def get_selected_videos(self):
        return {index.row() for index in self.video_table.selectedIndexes() if index.column() == 0}

    @pyqtSlot(str, str, str, list)
    def update_video_list(self, title, thumbnail_url, video_url, formats):
        row_position = self.video_table.rowCount()
        self.video_table.insertRow(row_position)
        self.video_info_list.append((title, video_url))

        # Checkbox
        chkBoxItem = QTableWidgetItem()
        chkBoxItem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        chkBoxItem.setCheckState(Qt.Unchecked)
        self.video_table.setItem(row_position, 0, chkBoxItem)

        # Thumbnail
        if thumbnail_url:
            response = requests.get(thumbnail_url)
            pixmap = QPixmap()
            if pixmap.loadFromData(response.content):
                thumbnail_item = QTableWidgetItem()
                thumbnail_item.setData(Qt.DecorationRole, pixmap.scaled(50, 50, Qt.KeepAspectRatio))
                thumbnail_item.setFlags(Qt.ItemIsEnabled)  # Disable editing but allow selection
                self.video_table.setItem(row_position, 1, thumbnail_item)

        # Title
        self.video_table.setItem(row_position, 2, QTableWidgetItem(title))

        # Format combo box with categorized and ordered formats
        format_combo = QComboBox()

        # Separating audio and video formats
        audio_formats = [f for f in formats if 'm4a' in f.lower()]  # Assuming 'm4a' is considered audio
        video_formats = [f for f in formats if
                         f not in audio_formats and 'mp4' in f.lower()]  # Assuming 'mp4' is considered video

        # Adding AUDIO label if there are audio formats
        if audio_formats:
            format_combo.addItem("AUDIO")
            for format_detail in audio_formats:
                format_combo.addItem(format_detail)

        # Adding VIDEO label if there are video formats
        if video_formats:
            # if audio_formats:  # Add a separator if there are also audio formats
            #     format_combo.addItem("-----------")
            format_combo.addItem("VIDEO")
            for format_detail in video_formats:
                format_combo.addItem(format_detail)

        # Set the default format if available
        if format_combo.count() > 0:
            format_combo.setCurrentIndex(1)  # Default to the first actual format after the AUDIO label
        else:
            format_combo.addItem("No available formats")

        self.video_table.setCellWidget(row_position, 3, format_combo)
        # self.video_table.setEditTriggers(QTableWidget.NoEditTriggers)

    def search_finished(self):
        self.set_status('검색 완료.')
        self.progress_bar.setRange(0, 100)  # Reset the progress bar range
        self.progress_bar.setValue(100)  # Set completion value

    def set_status(self, message):
        self.status_label.setText(message)
        # 로그를 파일에도 기록
        with open('download_log.txt', 'a', encoding='utf-8') as f:
            timestamp = QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
            f.write(f'[{timestamp}] {message}\n')

    @pyqtSlot(float)
    def update_progress_bar(self, progress):
        self.progress_bar.setValue(int(progress))

    def status_update(self, message):
        self.status_label.setText(message)

    def progress_update(self, progress):
        self.progress_bar.setValue(progress)


class MainThreadSignalEmitter(QObject):
    # Signal to emit warning messages
    warning_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def emit_warning(self, message):
        # Emit warning message signal
        self.warning_message.emit(message)


main_thread_signal_emitter = MainThreadSignalEmitter()


class Searcher(QThread):
    updated_list = pyqtSignal(str, str, str, list)  # The last parameter is a list of format strings.
    search_progress = pyqtSignal(int, int)  # Signal with two arguments: current progress and total count

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            try:
                result = ydl.extract_info(self.url, download=False)
                videos = result.get('entries', [result])

                for video in videos:
                    formats = video.get('formats', [])
                    format_list = []
                    for f in formats:
                        if f['ext'] != 'webm':  # 'webm' 포맷 제외
                            filesize = f.get('filesize')
                            if filesize and filesize > 0:
                                ext = f['ext']
                                if f.get('vcodec') != 'none':  # This is a video format
                                    quality = f.get('resolution') or f"{f.get('height')}p"
                                    type_label = 'Video'
                                else:  # This is an audio format
                                    quality = f"{round(f.get('abr', 0))}kbps" if f.get('abr') else ""
                                    type_label = 'Audio'
                                filesize_mb = f"{filesize // 1024 // 1024}MB"
                                format_detail = (type_label, f"{ext} - {quality} - {filesize_mb}", filesize)
                                format_list.append(format_detail)

                    # Sort the list: audio formats first, then by filesize in descending order
                    format_list.sort(key=lambda x: (-x[2], x[0] == 'Video'))

                    # Convert tuple back to string for display, omitting filesize used for sorting
                    format_list = [f"{f[1]}" for f in format_list]

                    self.updated_list.emit(
                        video.get('title', 'No title'),
                        video.get('thumbnail', ''),
                        video.get('webpage_url', ''),
                        format_list
                    )
            except Exception as e:
                main_thread_signal_emitter.emit_warning(f'An unexpected error occurred: {str(e)}')

    def estimate_total_count(self, result):
        if 'entries' in result:
            # If it's a playlist, estimate the total count based on the number of entries
            return len(result['entries'])
        else:
            # If it's a single video, return 1 as the total count
            return 1


class Downloader(QThread):
    updated_status = pyqtSignal(str)
    download_failed = pyqtSignal(str)
    updated_progress = pyqtSignal(float)  # Signal to update progress bar

    def __init__(self, videos, download_directory):
        super().__init__()
        self.videos = videos
        self.download_directory = download_directory

    def run(self):
        for title, url, format_id in self.videos:
            # Use the passed title directly, ensuring it's used for the filename
            safe_title = title.replace("/", "_").replace("\\", "_")
            download_options = {
                'format': format_id,
                'outtmpl': os.path.join(self.download_directory, f"{safe_title}.%(ext)s"),
                'progress_hooks': [self.progress_hook],
            }

            with yt_dlp.YoutubeDL(download_options) as ydl:
                try:
                    ydl.download([url])
                except Exception as e:
                    self.download_failed.emit(f"Failed to download {title}: {str(e)}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent_str = remove_ansi_escape(d['_percent_str'])
            percent_complete = float(percent_str.replace('%', ''))
            # ...
        elif d['status'] == 'finished':
            title = os.path.splitext(os.path.basename(d['filename']))[0]
            if len(title) > 14:
                title = title[:14] + "..."
            self.updated_status.emit(f"다운로드 완료: {title}")
        # ... 기타 상태 처리 ...


def remove_ansi_escape(text):
    ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('st2.icns'))
    # Enable hardware acceleration
    QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebGLEnabled, True)
    QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled,
                                                     True)  # Corrected attribute name
    # QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebSecurityEnabled, False)

    mainWindow = VideoDownloader()
    mainWindow.show()
    view = QWebEngineView()
    sys.exit(app.exec_())

# pyinstaller --windowed --icon=st2.icns --additional-hooks-dir=hooks Nobody3.py