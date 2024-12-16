import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.vid_file_path = ""
        self.lane_start = 0
        self.lane_end = 0
        self.key_count = 0
        self.global_offset = 0
        self.RN_offset = 0
        self.LN_hold_offset = 0
        self.LN_release_offset = 0

        self.audio_file_path = ""
        self.is_use_video_audio_flag = False
        self.is_show_progress_flag = False

        self.ui.get_vid_pushButton.clicked.connect(self.get_vid_file_ex)
        self.ui.get_vid_pushButton.clicked.connect(self.update_vid_file_textEdit)

        self.ui.lane_start_spinBox.textChanged.connect(self.update_lane_start)

        self.ui.lane_end_spinBox.textChanged.connect(self.update_lane_end)

        self.ui.key_count_spinBox.textChanged.connect(self.update_key_count)

        self.ui.key_count_spinBox.textChanged.connect(self.update_key_count)

        self.ui.key_count_spinBox.textChanged.connect(self.update_key_count)

        self.ui.global_offset_spinBox.textChanged.connect(self.update_global_offset)

        self.ui.RN_offset_spinBox.textChanged.connect(self.update_RN_offset)

        self.ui.LN_hold_offset_spinBox.textChanged.connect(self.update_LN_hold_offset)

        self.ui.LN_release_offset_spinBox.textChanged.connect(
            self.update_LN_release_offset
        )

        self.ui.get_audio_pushButton.clicked.connect(self.get_audio_file_ex)
        self.ui.get_audio_pushButton.clicked.connect(self.update_audio_file_textEdit)

        self.ui.use_video_audio_checkBox.stateChanged.connect(
            self.update_use_video_audio_flag
        )

        self.ui.run_pushButton.clicked.connect(self.run)

    @Slot()
    def run(self):
        pass

    @Slot()
    def update_show_progress_flag(self):
        self.is_show_progress_flag = self.ui.show_progress_checkBox.checkState()

    @Slot()
    def update_use_video_audio_flag(self):
        self.is_use_video_audio_flag = self.ui.use_video_audio_checkBox.checkState()

    @Slot()
    def get_audio_file_ex(self):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select an audio")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            self.audio_file_path = selected_files[0]

    @Slot()
    def update_audio_file_textEdit(self):
        self.ui.audio_file_path_textEdit.clear()
        self.ui.audio_file_path_textEdit.append(self.audio_file_path)

    @Slot()
    def update_LN_release_offset(self):
        self.LN_release_offset = self.ui.LN_release_offset_spinBox.value()

    @Slot()
    def update_LN_hold_offset(self):
        self.LN_hold_offset = self.ui.LN_hold_offset_spinBox.value()

    @Slot()
    def update_RN_offset(self):
        self.RN_offset = self.ui.RN_offset_spinBox.value()

    @Slot()
    def update_global_offset(self):
        self.global_offset = self.ui.global_offset_spinBox.value()

    @Slot()
    def update_lane_start(self):
        self.lane_start = self.ui.lane_start_spinBox.value()

    @Slot()
    def update_lane_end(self):
        self.lane_start = self.ui.lane_end_spinBox.value()

    @Slot()
    def update_key_count(self):
        self.key_count = self.ui.key_count_spinBox.value()

    @Slot()
    def get_vid_file_ex(self):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select a video")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            self.vid_file_path = selected_files[0]

    @Slot()
    def update_vid_file_textEdit(self):
        self.ui.vid_file_path_textEdit.clear()
        self.ui.vid_file_path_textEdit.append(self.vid_file_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
