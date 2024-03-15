import os
import sys
import requests
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QDialog, QPushButton, QVBoxLayout, QLineEdit, QLabel, QProgressBar,
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QCheckBox, QFileDialog,
                             QTextEdit, QComboBox, QAbstractItemView, QHBoxLayout)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, pyqtSlot, QObject, QTimer
import yt_dlp


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
        self.FORMAT_COLUMN_INDEX = 3  # Now accessible as self.FORMAT_COLUMN_INDEX
        self.setWindowTitle("유튜브 원하세요??")  # Set the window title here
        self.search_url = QLineEdit()
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.on_search)
        self.searched_urls = set()  # Attribute to store searched URLs
        self.video_info_list = []  # List to store video information (title, url)
        self.initUI()

    def initUI(self):
        # Initialize all widgets first
        self.search_url = QLineEdit(self)
        self.search_button = QPushButton('Search', self)
        self.video_table = QTableWidget(self)
        self.download_button = QPushButton('Download', self)
        self.status_label = QLabel('Status: Idle', self)
        self.progress_bar = QProgressBar(self)

        # Setup video table
        self.video_table.setColumnCount(4)  # Adjust the number of columns as necessary
        self.video_table.setHorizontalHeaderLabels(
            ['', 'Thumbnail', 'Title', 'Format'])  # Adding 'Format' as a column header
        FORMAT_COLUMN_INDEX = 3

        self.header = CheckBoxHeader()
        self.video_table.setHorizontalHeader(self.header)
        self.header.cb.clicked.connect(self.header.selectAll)
        header = self.video_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.video_table.horizontalHeader().setVisible(True)
        self.video_table.verticalHeader().setVisible(False)
        self.video_table.setStyleSheet(
            """
            QTableWidget {
                border: 0px;
                background-color: #000;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #d6d6d6;
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

        # Create layout and add widgets in proper order
        layout = QVBoxLayout()

        # Create a horizontal layout for the search widgets
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_url)  # Add the search URL input field first
        search_layout.addWidget(self.search_button)  # Add the search button next

        # Add the search layout to the main layout
        layout.addLayout(search_layout)

        # Create a horizontal layout for the progress bar, status label, and download button
        control_layout = QHBoxLayout()

        # Add the progress bar and status label to the control layout
        control_layout.addWidget(self.progress_bar)
        control_layout.addWidget(self.status_label)

        # Add stretch to push the download button to the right
        control_layout.addStretch()

        # Add the download button to the control layout
        control_layout.addWidget(self.download_button)

        # Add the video table to the main layout
        layout.addWidget(self.video_table)

        # Add the control layout to the main layout
        layout.addLayout(control_layout)

        # Set the main layout for the dialog
        self.setLayout(layout)

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.toggle_loading_animation)
        self.direction = 1

        self.center_on_screen()
        # self.search_thread.search_progress.connect(lambda current, total: print(f"Loading... {current}/{total}"))

    def center_on_screen(self):
        # Get the main screen's geometry
        screen_geometry = QApplication.desktop().screenGeometry()

        # Calculate the center point
        center_point = screen_geometry.center()

        # Set the center point of the dialog
        self.move(center_point - self.rect().center())

    def update_search_progress(self, current, total):
        # This slot is invoked by the signal emitted by the searcher thread.
        self.status_label.setText(f"Loading... {current}/{total}")
        self.progress_bar.setValue(int((current / total) * 100))

    def search_duplicate_urls(self, url):
        for row in range(self.video_table.rowCount()):
            video_url = self.video_table.item(row, 3).text()  # Assuming URLs are in the fourth column
            if video_url == url:
                return True  # Found a duplicate URL
        return False  # No duplicate URL found

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

    def on_search(self):
        url = self.search_url.text().strip()
        if not is_valid_url(url):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL.")
            return
        if url in self.searched_urls:
            QMessageBox.warning(self, "Duplicate URL", "This URL has already been searched.")
            return

        self.searched_urls.add(url)
        self.search_button.setEnabled(False)
        self.status_label.setText('Searching...')
        self.progress_bar.setRange(0, 0)  # Indeterminate mode

        # Create the search_thread here
        self.search_thread = Searcher(url)
        # Connect the search_progress signal here, after the search_thread has been created
        self.search_thread.search_progress.connect(self.update_search_progress)
        self.search_thread.updated_list.connect(self.update_video_list)
        self.search_thread.finished.connect(self.search_finished)
        # Start the thread
        self.search_thread.start()

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
        self.video_table.setItem(row_position, 0, checkbox)

        title_item = QTableWidgetItem(title)
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
        for row in range(self.video_table.rowCount()):
            checkbox_item = self.video_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                selected_videos.append(self.video_info_list[row])

        if not selected_videos:
            QMessageBox.warning(self, "선택 없음", "다운로드할 비디오를 선택해주세요.")
            return

        download_directory = self.select_download_directory()
        if not download_directory:
            QMessageBox.warning(self, "다운로드 취소됨", "다운로드할 디렉토리를 선택하지 않았습니다.")
            return

        # Create a list to keep track of download threads
        download_threads = []

        for title, url in selected_videos:
            file_path = os.path.join(download_directory, f"{title}.m4a")
            if os.path.exists(file_path):
                reply = QMessageBox.question(self, '파일이 이미 존재합니다',
                                             f"다운로드 디렉토리에 '{title}.m4a'라는 파일이 이미 존재합니다. 덮어쓰시겠습니까?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    continue  # Skip downloading this file if the user chooses not to overwrite

            # Trigger the download process for this video
            downloader_thread = Downloader([(title, url)], download_directory)
            download_threads.append(downloader_thread)
            downloader_thread.updated_status.connect(self.set_status)
            downloader_thread.updated_progress.connect(self.progress_update)
            downloader_thread.overall_progress.connect(self.progress_update)  # Update progress for overall completion
            downloader_thread.download_failed.connect(self.download_failed)
            downloader_thread.start()

        # Wait for all download threads to finish before allowing further interaction
        for thread in download_threads:
            thread.wait()

    def download_failed(self, message):
        self.set_status(f"Download failed: {message}")

    def get_selected_videos(self):
        return {index.row() for index in self.video_table.selectedIndexes() if index.column() == 0}

    @pyqtSlot(str, str, str, list)
    def update_video_list(self, title, thumbnail_url, video_url, formats):
        row_position = self.video_table.rowCount()
        self.video_table.insertRow(row_position)
        # Assume FORMAT_COLUMN_INDEX is correctly set to the index of the format column
        format_combo_box = QComboBox()
        for format in formats:
            if 'video' in format.get('vcodec', 'none'):  # Check if it's a video format
                desc = f"{format.get('ext', '')} - {format.get('resolution', 'Unknown')} - Video"
            else:  # Assuming audio if not video
                desc = f"{format.get('ext', '')} - {format.get('abr', 'Unknown')}kbps - Audio"
            format_combo_box.addItem(desc, format['format_id'])
        self.video_table.setCellWidget(row_position, self.FORMAT_COLUMN_INDEX, format_combo_box)
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

    def search_finished(self):
        self.set_status('검색 완료.')
        self.progress_bar.setRange(0, 100)  # Reset the progress bar range
        self.progress_bar.setValue(100)  # Set completion value


    def download_finished(self):
        self.status_label.setText('다운로드 완료.')

    def set_status(self, message):
        self.status_label.setText(message)

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
    updated_list = pyqtSignal(str, str, str, list)  # Add a list for formats
    search_progress = pyqtSignal(int, int)    # Signal for updating search progress, emits current and total count

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url  # The URL to search or download from

    def run(self):
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            try:
                result = ydl.extract_info(self.url, download=False)
                if 'entries' in result:
                    # It's a playlist
                    total_videos = len(result['entries'])
                    for current_index, video in enumerate(result['entries'], start=1):
                        if video:
                            self.updated_list.emit(video.get('title', 'No title'),
                                                   video.get('thumbnail', ''),
                                                   video.get('webpage_url', 'No URL'),
                                                   video.get('formats', 'No Formats'))
                            self.search_progress.emit(current_index, total_videos)
                else:
                    # It's a single video
                    total_videos = 1
                    current_index = 1
                    self.updated_list.emit(result.get('title', 'No title'),
                                           result.get('thumbnail', ''),
                                           result.get('webpage_url', 'No URL'),
                                           result.get('formats', 'No Formats'))
                    self.search_progress.emit(current_index, total_videos)
            except yt_dlp.utils.ExtractorError as e:
                main_thread_signal_emitter.emit_warning(str(e))
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
    updated_status = pyqtSignal(str)  # Fix this line
    updated_progress = pyqtSignal(int)
    overall_progress = pyqtSignal(int)
    download_failed = pyqtSignal(str)

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
                'progress_hooks': [self.yt_dlp_progress_hook],
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
                'progress_hooks': [self.yt_dlp_progress_hook],
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

    def yt_dlp_progress_hook(self, d):
        """Called by yt_dlp during the download process."""
        if d['status'] == 'downloading':
            # Update download progress based on 'downloaded_bytes' and 'total_bytes'
            downloaded_bytes = d.get('downloaded_bytes', 0)
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if total_bytes > 0:
                progress_percentage = int((downloaded_bytes / total_bytes) * 100)
                self.updated_progress.emit(progress_percentage)
        elif d['status'] == 'finished':
            # Here, all postprocessing steps, including file deletion, have completed
            self.updated_status.emit(f"Download completed: {d['filename']}")
            # Optionally, update overall progress or perform other actions

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoDownloader()
    ex.show()
    sys.exit(app.exec_())