import sys
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QSlider, QLabel, QFileDialog, QListWidget, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QInputDialog, QMenu, QAction, QMessageBox, QMenuBar
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QKeySequence
import os
import site
import json
from functools import partial

# Get the site-packages directory
site_packages = site.getsitepackages()[0]
qt_plugins_path = os.path.join(site_packages, 'PyQt5', 'Qt5', 'plugins')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugins_path
thisDir = os.path.dirname(os.path.abspath(__file__))


class Ataata(QMainWindow):
    def __init__(self, videoPath=None):
        super().__init__()
        self.setWindowTitle("Video Chapter Builder")
        self.setGeometry(100, 100, 800, 600)
        self.video_path = None
        self.cap = None
        self.current_frame = 0
        self.fps = 0
        self.chapters = []
        self.playback_speed = 1.0

        self.init_ui()
        self.create_menu()
        self.create_shortcuts()  # Add this line
        if videoPath:
            self.set_and_play_video(videoPath)

    def init_ui(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Video display
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(400, 300)  # min size 
        left_layout.addWidget(self.video_label, 1)  # stretch

        # Control buttons and sliders
        controls_layout = QVBoxLayout()

        # Time slider
        time_layout = QHBoxLayout()
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_label = QLabel("00:00:00")
        time_layout.addWidget(self.time_slider)
        time_layout.addWidget(self.time_label)
        controls_layout.addLayout(time_layout)

        # Speed control
        speed_layout = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(-2)
        self.speed_slider.setMaximum(3)
        self.speed_slider.setValue(0)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(1)
        self.speed_label = QLabel("1x")
        speed_layout.addWidget(QLabel("Speed:"))
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        controls_layout.addLayout(speed_layout)

        # buttons
        button_layout = QHBoxLayout()
        self.open_button = QPushButton("Open Video")
        self.play_pause_button = QPushButton("Play/Pause")
        self.add_chapter_button = QPushButton("Add Chapter")
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.play_pause_button)
        button_layout.addWidget(self.add_chapter_button)
        controls_layout.addLayout(button_layout)

        left_layout.addLayout(controls_layout)

        # Chapters
        chapters_layout = QVBoxLayout()
        chapters_layout.addWidget(QLabel("Chapters:"))
        self.chapter_list = QListWidget()
        chapters_layout.addWidget(self.chapter_list)
        
        chapters_button_layout = QHBoxLayout()
        self.import_button = QPushButton("Import Chapters")
        self.export_button = QPushButton("Export Chapters")
        chapters_button_layout.addWidget(self.import_button)
        chapters_button_layout.addWidget(self.export_button)
        chapters_layout.addLayout(chapters_button_layout)
        
        right_layout.addLayout(chapters_layout)

        # layouts
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        # central widget and set the main layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # signals
        self.open_button.clicked.connect(self.open_video)
        self.play_pause_button.clicked.connect(self.play_pause)
        self.add_chapter_button.clicked.connect(self.add_chapter)
        self.chapter_list.itemDoubleClicked.connect(self.edit_chapter)
        self.time_slider.sliderMoved.connect(self.set_position)
        self.speed_slider.valueChanged.connect(self.change_speed)
        self.chapter_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.chapter_list.customContextMenuRequested.connect(self.show_context_menu)
        self.export_button.clicked.connect(self.export_chapters)
        self.import_button.clicked.connect(self.import_chapters)

        # Timer 
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def create_menu(self):
        menubar = self.menuBar()
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_about_dialog(self):
        about_text = f"""
        Ataata - Video Chapter Builder
        Version: 0.1.0
        
        Author: Fraser M. Callaghan
        Copyright © 2024 Fraser M. Callaghan
        LICENSE: MIT
        
        A simple application for creating chapters in video files.
        """
        QMessageBox.about(self, "About Ataata", about_text)

    def open_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov, *.mkv)")
        if file_path:
            self.set_and_play_video(file_path)

    def set_and_play_video(self, file_path):
        if os.path.exists(file_path):
            self.video_path = file_path
            self.cap = cv2.VideoCapture(self.video_path)
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.time_slider.setRange(0, total_frames)
            self.play_pause()
        else:
            self.video_path = None
            QMessageBox.warning(self, "Open Video", "Failed to open video file.")

    def play_pause(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(int(1000 / self.fps))

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.current_frame += 1 * self.playback_speed
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label.setPixmap(scaled_pixmap)
            
            self.time_slider.setValue(int(self.current_frame))
            self.update_time_label()
        else:
            self.timer.stop()

    def set_position(self, position):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
        self.current_frame = position
        self.update_time_label()

    def update_time_label(self):
        current_time = self.current_frame / self.fps
        total_time = self.cap.get(cv2.CAP_PROP_FRAME_COUNT) / self.fps
        self.time_label.setText(f"{self.format_time(current_time)} / {self.format_time(total_time)}")

    def change_speed(self, value):
        speeds = [0.5, 0.75, 1, 2, 4, 8]
        self.playback_speed = speeds[value + 2]
        self.speed_label.setText(f"{self.playback_speed}x")
        if self.timer.isActive():
            self.timer.setInterval(int(1000 / (self.fps * self.playback_speed)))

    def _count_chapters(self, chapterPrefix="Chapter"):
        count = 0
        for iChapter in self.chapters:
            if iChapter[1].startswith(chapterPrefix):
                count += 1
        return count

    def add_chapter(self, chapterPrefix="Chapter", showEditPrompt=True):
        if self.cap is not None:
            current_time = self.current_frame / self.fps
            count = self._count_chapters(chapterPrefix) + 1
            if showEditPrompt:
                chapter_name, ok = QInputDialog.getText(self, 
                                                        "Add Chapter", 
                                                        "Enter chapter name:", 
                                                        text=f"{chapterPrefix}{count}")
            else:
                chapter_name = f"{chapterPrefix}{count}"
                ok = True
            if ok and chapter_name:
                self.chapters.append((current_time, chapter_name))
                self.update_chapter_list()

    def update_chapter_list(self):
        self.chapter_list.clear()
        for time, name in sorted(self.chapters):
            self.chapter_list.addItem(f"{self.format_time(time)} - {name}")

    def edit_chapter(self, item):
        index = self.chapter_list.row(item)
        time, old_name = self.chapters[index]
        new_name, ok = QInputDialog.getText(self, "Edit Chapter", "Enter new chapter name:", text=old_name)
        if ok and new_name:
            self.chapters[index] = (time, new_name)
            self.update_chapter_list()

    def show_context_menu(self, position):
        menu = QMenu()
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_chapter)
        menu.addAction(delete_action)
        # seek
        seek_action = QAction("Seek to Chapter", self)
        seek_action.triggered.connect(self.seek_to_chapter)
        menu.addAction(seek_action)

        menu.exec_(self.chapter_list.mapToGlobal(position))

    def seek_to_chapter(self):
        current_item = self.chapter_list.currentItem()
        if current_item and self.cap is not None:
            index = self.chapter_list.row(current_item)
            chapter_time, _ = self.chapters[index]
            frame_number = int(chapter_time * self.fps)
            self.set_position(frame_number)
            self.update_frame()

    def delete_chapter(self):
        current_item = self.chapter_list.currentItem()
        if current_item:
            index = self.chapter_list.row(current_item)
            del self.chapters[index]
            self.update_chapter_list()

    def import_chapters(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Chapters", "", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                self.chapters = []
                for line in lines:
                    time_str, name = line.strip().split(' - ', 1)
                    h, m, s = map(int, time_str.split(':'))
                    time_seconds = h * 3600 + m * 60 + s
                    self.chapters.append((time_seconds, name))
                
                self.update_chapter_list()
                QMessageBox.information(self, "Import Chapters", "Chapters imported successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Import Chapters", f"Failed to import chapters: {str(e)}")

    def export_chapters(self):
        if not self.chapters:
            QMessageBox.warning(self, "Export Chapters", "No chapters to export.")
            return

        # Ensure the video is paused
        if self.timer.isActive():
            self.timer.stop()

        default_name = f"{os.path.splitext(self.video_path)[0]}_Chapters.txt" 
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Chapters", default_name, "Text Files (*.txt)")
        if file_path:
            with open(file_path, 'w') as f:
                for time, name in sorted(self.chapters):
                    f.write(f"{self.format_time(time)} - {name}\n")
            QMessageBox.information(self, "Export Chapters", "Chapters exported successfully.")

    @staticmethod
    def format_time(seconds):
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def create_shortcuts(self):
        # Standard shortcuts
        play_pause_action = QAction('Play/Pause', self)
        play_pause_action.setShortcut(QKeySequence('Space'))
        play_pause_action.triggered.connect(self.play_pause)
        self.addAction(play_pause_action)

        open_video_action = QAction('Open Video', self)
        open_video_action.setShortcut(QKeySequence('Ctrl+O'))
        open_video_action.triggered.connect(self.open_video)
        self.addAction(open_video_action)

        save_chapters_action = QAction('Save Chapters', self)
        save_chapters_action.setShortcut(QKeySequence('Ctrl+S'))
        save_chapters_action.triggered.connect(self.export_chapters)
        self.addAction(save_chapters_action)

        # Additional custom shortcuts
        try:
            with open(os.path.join(thisDir, 'shortcuts.json'), 'r') as f:
                shortcuts = json.load(f)
        except Exception as e:
            # QMessageBox.warning(self, "Error", f"Failed to load shortcuts: {str(e)}")
            return

        # Create shortcuts based on the JSON file
        for shortcut in shortcuts:
            key_combination = shortcut.get("key_combination")
            chapter_prefix = shortcut.get("chapter_prefix")
            if key_combination and chapter_prefix:
                action = QAction(f'Add {chapter_prefix}', self)
                action.setShortcut(QKeySequence(key_combination))
                action.triggered.connect(partial(self.add_chapter, chapter_prefix))
                self.addAction(action)
                print(f"Added shortcut: {key_combination} -> Add {chapter_prefix}")

if __name__ == "__main__":
    app = QApplication(sys.argv[:1])
    vidPath = None
    if len(sys.argv) > 1:
        vidPath = sys.argv[1]
    window = Ataata(vidPath)
    window.show()
    sys.exit(app.exec_())