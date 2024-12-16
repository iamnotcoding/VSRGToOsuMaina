import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import QFile, Slot
from ui_mainwindow import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.get_vid_pushButton.clicked.connect(self.get_vid_file_ex)
        self.ui.get_vid_pushButton.clicked.connect(self.update_vid_file_textEdit)

        self.vid_file_path = ""

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


