import os
import sys
import requests
from PyQt5.QtGui import QPixmap, QMovie, QIcon
from PyQt5.QtWidgets import (QApplication, QDialog, QPushButton, QVBoxLayout, QLineEdit, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QCheckBox, QFileDialog,
                             QTextEdit, QComboBox, QAbstractItemView, QHBoxLayout)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, pyqtSlot, QObject, QTimer
import yt_dlp
from concurrent.futures import ThreadPoolExecutor



# Helper function to check URL validity
def is_valid_url(url):
    # This function should be expanded to validate URLs effectively.
    return url.startswith("http")


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
        self.cb.setStyleSheet("QCheckBox { margin-left: 10px; margin-right: 6px; }")  # Adjust the margins for alignment

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


class VideoDownloader(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Happy Hacking")  # Set the window title here
        self.search_url = QLineEdit()
        self.search_button = QPushButton("불러오기")
        self.download_button = QPushButton('내려받기')
        self.search_button.clicked.connect(self.on_search)
        self.searched_urls = set()  # Attribute to store searched URLs
        self.video_info_list = []  # List to store video information (title, url)
        self.initUI()

    def initUI(self):
        # Initialize all widgets first
        self.search_url = QLineEdit(self)
        self.search_button = QPushButton('불러오기', self)
        self.video_table = QTableWidget(self)
        self.download_button = QPushButton('내려받기', self)
        self.clear_table_button = QPushButton('테이블 지우기', self)  # "Clear Table" button
        self.rainbow_cat_label = QLabel(self)
        rainbow_cat_movie = QMovie("rainbow_cat.gif")  # Replace "rainbow_cat.gif" with the actual file path
        self.rainbow_cat_label.setMovie(rainbow_cat_movie)
        rainbow_cat_movie.start()
        self.rainbow_cat_label.setMaximumSize(20, 20)
        self.rainbow_cat_label.setScaledContents(True)

        # Setup video table
        self.video_table.setColumnCount(3)  # Reduce column count to exclude URL column
        self.video_table.setHorizontalHeaderLabels(['', 'Thumbnail', 'Title'])  # Exclude URL from header labels
        self.header = CheckBoxHeader()
        self.video_table.setHorizontalHeader(self.header)
        self.header.cb.clicked.connect(self.header.selectAll)
        header = self.video_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.video_table.horizontalHeader().setVisible(True)
        self.video_table.verticalHeader().setVisible(False)
        self.video_table.setSelectionMode(QAbstractItemView.NoSelection)  # Disable row selection
        self.video_table.setStyleSheet(
            """
            QTableWidget {
                border: 0px;
                background-color: #000;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 0px solid #d6d6d6;
            }
            QHeaderView::section {
                border: 0px;
                background-color: #000;
            }
            """
        )

        # Setup actions
        self.search_button.clicked.connect(self.on_search)
        self.download_button.clicked.connect(self.on_download)
        self.clear_table_button.clicked.connect(self.on_clear_table)  # Connect the button to its slot

        # Create layout and add widgets in proper order
        layout = QVBoxLayout()

        # Create a horizontal layout for the search widgets
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_url)  # Add the search URL input field first
        search_layout.addWidget(self.search_button)  # Add the search button next

        # Add the search layout to the main layout
        layout.addLayout(search_layout)

        layout.addWidget(self.video_table)

        # Create a horizontal layout for the control widgets
        control_layout = QHBoxLayout()

        # Add the Rainbow Cat label to the control layout
        control_layout.addWidget(self.rainbow_cat_label)
        control_layout.addWidget(self.clear_table_button)  # Add the Clear Table button to the layout

        # Add stretch to push the download button to the right
        control_layout.addStretch()

        # Add the download button to the control layout
        control_layout.addWidget(self.download_button)

        # Add the control layout to the main layout
        layout.addLayout(control_layout)

        # Set the main layout for the dialog
        self.setLayout(layout)

        self.center_on_screen()
        self.setStyleSheet("background-color: #000;")

        self.resize(500, 500)

    def center_on_screen(self):
        # Get the main screen's geometry
        screen_geometry = QApplication.desktop().screenGeometry()

        # Calculate the center point
        center_point = screen_geometry.center()

        # Set the center point of the dialog
        self.move(center_point - self.rect().center())

    def search_duplicate_urls(self, url):
        for row in range(self.video_table.rowCount()):
            video_url = self.video_table.item(row, 3).text()  # Assuming URLs are in the fourth column
            if video_url == url:
                return True  # Found a duplicate URL
        return False  # No duplicate URL found

    @pyqtSlot()
    def on_search(self):
        url = self.search_url.text().strip()
        if url in self.searched_urls:
            QMessageBox.warning(self, "중복된 URL", "이 URL은 이미 검색되었습니다.")
            return
        self.searched_urls.add(url)

        with ThreadPoolExecutor() as executor:
            future = executor.submit(self.perform_search, url)

    def perform_search(self, url):
        searcher = Searcher(url)
        searcher.updated_list.connect(self.update_video_list)
        searcher.run()  # Running in the current thread

    def search_finished(self, future):
        # Extract the result from the future
        result = future.result()

        # Handle the result as needed
        if result is not None:
            # Do something with the result
            pass

    @pyqtSlot(str, str)
    def list_update(self, title, thumbnail_url):
        row_position = self.video_table.rowCount()
        self.video_table.insertRow(row_position)

        checkbox = QTableWidgetItem()
        checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        checkbox.setCheckState(Qt.Unchecked)
        self.video_table.setItem(row_position, 0, checkbox)

        title_item = QTableWidgetItem(title)
        title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)  # Disable editing
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
    def on_clear_table(self):
        self.video_table.setRowCount(0)  # Remove all rows from the table
        self.searched_urls.clear()  # Optionally clear the set of searched URLs if you want
    @pyqtSlot()
    def on_download(self):
        selected_videos = []
        for row in range(self.video_table.rowCount()):
            if self.video_table.item(row, 0).checkState() == Qt.Checked:
                selected_videos.append(self.video_info_list[row])

        if not selected_videos:
            QMessageBox.warning(self, "선택 없음", "다운로드할 비디오를 선택해주세요.")
            return

        download_directory = self.select_download_directory()
        if not download_directory:
            QMessageBox.warning(self, "다운로드 취소됨", "다운로드 디렉토리를 선택하지 않았습니다.")
            return

        download_threads = []

        for title, url in selected_videos:
            file_path = os.path.join(download_directory, f"{title}.m4a")
            if os.path.exists(file_path):
                reply = QMessageBox.question(self, '파일이 이미 존재합니다',
                                             f"'{title}.m4a'라는 파일이 이미 다운로드 디렉토리에 있습니다. "
                                             "덮어쓰시겠습니까?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    continue

            downloader_thread = Downloader([(title, url)], download_directory)
            downloader_thread.start()
            download_threads.append(downloader_thread)

        for thread in download_threads:
            thread.wait()

    def get_selected_videos(self):
        return {index.row() for index in self.video_table.selectedIndexes() if index.column() == 0}

    @pyqtSlot(str, str, str)
    def update_video_list(self, title, thumbnail_url, video_url):
        # Add the video information (title, url) to the list
        self.video_info_list.append((title, video_url))

        # Update the table as before
        row_position = self.video_table.rowCount()
        self.video_table.insertRow(row_position)

        chkBoxItem = QTableWidgetItem()
        chkBoxItem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        chkBoxItem.setCheckState(Qt.Unchecked)
        self.video_table.setItem(row_position, 0, chkBoxItem)

        if thumbnail_url:
            response = requests.get(thumbnail_url)
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            thumbnail_item = QTableWidgetItem()
            thumbnail_item.setData(Qt.DecorationRole, pixmap.scaled(50, 50, Qt.KeepAspectRatio))
            self.video_table.setItem(row_position, 1, thumbnail_item)

        self.video_table.setItem(row_position, 2, QTableWidgetItem(title))
        self.video_table.setItem(row_position, 3, QTableWidgetItem(video_url))

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
    updated_list = pyqtSignal(str, str, str)  # Ensure you have the correct signal signature

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            try:
                result = ydl.extract_info(self.url, download=False)
                for index, video in enumerate(result.get('entries', [result]), start=1):
                    if video:
                        self.updated_list.emit(video.get('title', 'No title'), video.get('thumbnail', ''),
                                               video.get('webpage_url', 'No URL'))
            except yt_dlp.utils.ExtractorError as e:
                main_thread_signal_emitter.emit_warning(str(e))
            except Exception as e:
                main_thread_signal_emitter.emit_warning(f'예기치 않은 오류가 발생했습니다: {str(e)}')

    def estimate_total_count(self, result):
        if 'entries' in result:
            # If it's a playlist, estimate the total count based on the number of entries
            return len(result['entries'])
        else:
            # If it's a single video, return 1 as the total count
            return 1


class Downloader(QThread):

    def __init__(self, videos, download_directory):
        super().__init__()
        self.videos = videos
        self.download_directory = download_directory
        self.total_size = 0
        self.downloaded_size = 0

    def run(self):
        for title, url in self.videos:
            download_options = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.download_directory, f"{title}.%(ext)s"),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }],
            }

            with yt_dlp.YoutubeDL(download_options) as ydl:
                info = ydl.extract_info(url, download=False)
                if 'filesize' in info:
                    self.total_size += info['filesize']

        for index, (title, url) in enumerate(self.videos):
            download_options = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.download_directory, f"{title}.%(ext)s"),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }],
            }

            try:
                with yt_dlp.YoutubeDL(download_options) as ydl:
                    ydl.download([url])
            except Exception as e:
                self.download_failed.emit(f"Failed to download {title}: {str(e)}")
                continue  # Continue with the next video

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('HHKB.ico'))
    ex = VideoDownloader()
    ex.show()
    sys.exit(app.exec_())
