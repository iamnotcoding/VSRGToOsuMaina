import os, sys
import copy
import threading
import ffmpeg
import zipfile
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PySide6.QtCore import QObject, QFile, Slot, QThread, Signal
from ui_mainwindow import Ui_MainWindow
import maina

import logging
import cv2 as cv
import threading

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def is_there_a_note(frame, p):  # p : (y, x)
    result = True
    MAX_ERROR = 0
    # px (in order to avoid recongnizing bar lines as notes)
    min_note_height = 0
    empty_color = (0, 0, 0)

    for i in range(-(min_note_height // 2), min_note_height // 2 + 1):
        # opencv frames get (y, x) coordinates
        pixel_color = frame[p[0] + i][p[1]]

        if not ((abs(pixel_color[0] - empty_color[0]) > MAX_ERROR
                 or abs(pixel_color[1] - empty_color[1]) > MAX_ERROR
                 or abs(pixel_color[2] - empty_color[2]) > MAX_ERROR)):

            result = False

    return result

class GUIMsgboxCritClass(QObject):
    sig = Signal(str, str)

    def invoke(self):
        self.sig.emit(self.title, self.text)

    def __init__(self, title, text):
        super(GUIMsgboxCritClass, self).__init__()
        self.title = title
        self.text = text

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        is_exit_preview_flag = True

        self.vid_file_path = ""
        self.lane_start = 400
        self.lane_end = 800
        self.detection_height = 500
        self.key_count = 4
        self.global_offset = 0
        self.RN_offset = 0
        self.LN_hold_offset = 0
        self.LN_release_offset = 0

        self.audio_file_path = ""
        self.is_use_video_audio_flag = False
        self.is_show_progress_flag = False

        self.preview_thread = None

        self.ui.get_vid_pushButton.clicked.connect(self.get_vid_file_ex)
        self.ui.get_vid_pushButton.clicked.connect(
            self.update_vid_file_textEdit)
        self.ui.get_vid_pushButton.clicked.connect(self.start_preview)

        self.ui.lane_start_spinBox.setRange(1, 9999)
        self.ui.lane_start_spinBox.setValue(self.lane_start)
        self.ui.lane_start_spinBox.textChanged.connect(self.update_lane_start)

        self.ui.lane_end_spinBox.setRange(1, 9999)
        self.ui.lane_end_spinBox.setValue(self.lane_end)
        self.ui.lane_end_spinBox.textChanged.connect(self.update_lane_end)

        self.ui.detection_height_spinBox.setRange(1, 9999)
        self.ui.detection_height_spinBox.setValue(self.detection_height)
        self.ui.detection_height_spinBox.textChanged.connect(
            self.update_detection_height)

        self.ui.key_count_spinBox.setRange(1, 20)
        self.ui.key_count_spinBox.setValue(self.key_count)
        self.ui.key_count_spinBox.textChanged.connect(self.update_key_count)

        self.ui.global_offset_spinBox.setRange(-9999, 9999)
        self.ui.global_offset_spinBox.textChanged.connect(
            self.update_global_offset)

        self.ui.RN_offset_spinBox.setRange(-9999, 9999)
        self.ui.RN_offset_spinBox.textChanged.connect(self.update_RN_offset)

        self.ui.LN_hold_offset_spinBox.setRange(-9999, 9999)
        self.ui.LN_hold_offset_spinBox.textChanged.connect(
            self.update_LN_hold_offset)

        self.ui.LN_release_offset_spinBox.setRange(-9999, 9999)
        self.ui.LN_release_offset_spinBox.textChanged.connect(
            self.update_LN_release_offset
        )

        self.ui.get_audio_pushButton.clicked.connect(self.get_audio_file_ex)
        self.ui.get_audio_pushButton.clicked.connect(
            self.update_audio_file_textEdit)

        self.ui.use_video_audio_checkBox.stateChanged.connect(
            self.update_use_video_audio_flag
        )

        self.ui.show_progress_checkBox.stateChanged.connect(self.update_show_progress_flag)

        self.ui.run_pushButton.clicked.connect(self.run)

    @Slot()
    def run(self):
        osu_file_name = "map.osu"
        osz_file_name = "map.osz"

        if self.create_osu_file(osu_file_name):
            logging.info(f"Created the file {osu_file_name}")
        else:
            logging.info("Creating an osu file was interrupted")

        if self.is_use_video_audio_flag:
            self.extract_audio_from_vid('audio.mp3')
            logging.info("Extracted an audio from the video")

        if self.create_osz_file(osz_file_name, osu_file_name):
            logging.info("Created an osz file map.osz")

    def create_osu_file(self, osu_file_name):
        if self.lane_start >= self.lane_end:
            crit_msgbox_sig = GUIMsgboxCritClass(
                "Error", "Lane end have to be larger than lane start")
            crit_msgbox_sig.sig.connect(self.GUI_msgbox_critial)
            crit_msgbox_sig.invoke()
            return 1

        if self.preview_thread is not None:
            self.preview_thread._stop()
            cv.destroyAllWindows()
            logging.info("Stopped preview_thread")

        osu_file_name = "map.osu"

        file = open(osu_file_name, "+w")

        if self.is_show_progress_flag:
            cv.namedWindow("Image", cv.WINDOW_NORMAL)

        vid_capture = cv.VideoCapture(self.vid_file_path)

        if (vid_capture.isOpened() == False):
            logging.error("Error opening the video file")
            raise RuntimeError

        fps = vid_capture.get(cv.CAP_PROP_FPS)
        logging.info(f"Detected video frame rate : {fps}")

        ret, frame = vid_capture.read()  # the first frame

        if not ret:
            logging.info("Couldn't read the video")
            raise RuntimeError

        height, width, channels = frame.shape

        line_thickness = 10

        maina.create_header(file, os.path.basename(self.audio_file_path), self.key_count)
        maina.start_note_section(file)

        frame_count = 1

        note_start_frame = [0 for _ in range(self.key_count)]
        is_exit_preview_flag = False

        while (vid_capture.isOpened()):
            ret, frame = vid_capture.read()

            if ret == False:
                break

            drawn_frame = copy.deepcopy(frame) # since it's a numpy array

            cv.line(drawn_frame, (self.lane_start -
                            line_thickness, 1), (self.lane_start -
                                                 line_thickness, height), (0, 255, 0), line_thickness)
            cv.line(drawn_frame, (self.lane_end +
                            line_thickness, 1), (self.lane_end +
                                                 line_thickness, height), (0, 0, 255), line_thickness)

            cv.line(drawn_frame, (self.lane_start, height -
                            self.detection_height), (self.lane_end, height -
                                                     self.detection_height), (255, 255, 255), line_thickness)

            for i in range(self.key_count):
                lane_width = self.lane_end - self.lane_start
                x = int((self.lane_start + lane_width / 4 * i +
                        self.lane_start + lane_width / 4 * (i + 1))/2)
                p = (height - self.detection_height , x)
                is_there_a_note_flag = is_there_a_note(frame, p)

                #cv.circle(frame, (p[1], p[0]), 10, (255, 0, 255), -1)

                if is_there_a_note_flag:
                    if note_start_frame[i] == 0:
                        note_start_frame[i] = frame_count

                    #print('▇', end=' ')
                else:
                    #print(' ', end=' ')

                    if note_start_frame[i] != 0:
                        # if long note
                        if (frame_count - note_start_frame[i]) / fps > 0.05:
                            if self.is_show_progress_flag:
                                cv.circle(drawn_frame, (p[1], p[0]), 40, (255, 0, 255), -1)

                            maina.create_LN(file, self.key_count, i + 1,int(note_start_frame[i] / fps * 1000) + self.global_offset + self.LN_hold_offset, int(frame_count / fps * 1000) + self.global_offset + self.LN_release_offset)
                        else:  # if regular note
                            if self.is_show_progress_flag:
                                cv.circle(drawn_frame, (p[1], p[0]), 15, (0, 255, 0), -1)

                            maina.create_RN(file, self.key_count, i + 1, int(note_start_frame[i] / fps * 1000) + self.global_offset + self.RN_offset)
                    else:
                        if self.is_show_progress_flag:
                            cv.circle(drawn_frame, (p[1], p[0]), 15, (0, 0, 255), -1)

                    note_start_frame[i] = 0


            if cv.getWindowProperty('Image', cv.WND_PROP_VISIBLE) < 1:
                is_exit_preview_flag = True
                break

            if self.is_show_progress_flag:
                cv.imshow('Image', drawn_frame)
                cv.waitKey(int(1 / fps * 1000))

            frame_count += 1

        if self.is_show_progress_flag:
            cv.destroyAllWindows()

        file.close()

        return not is_exit_preview_flag

    def extract_audio_from_vid(self):
        stream = ffmpeg.input(self.vid_file_path)
        stream = ffmpeg.hflip(stream)
        stream = ffmpeg.output(stream, "audio.mp3")
        ffmpeg.run(stream)

    def create_osz_file(self, osz_file_name, osu_file_name):
        if self.is_use_video_audio_flag:
            final_audio_file_path = "./audio.mp3"
        else:
            final_audio_file_path = self.audio_file_path

        with zipfile.ZipFile(osz_file_name, 'w') as myzip:
            myzip.write(osu_file_name)
            myzip.write(final_audio_file_path, arcname=os.path.basename(final_audio_file_path))

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
    def update_detection_height(self):
        self.detection_height = self.ui.detection_height_spinBox.value()

    @Slot()
    def update_lane_start(self):
        self.lane_start = self.ui.lane_start_spinBox.value()

    @Slot()
    def update_lane_end(self):
        self.lane_end = self.ui.lane_end_spinBox.value()

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

    def start_preview_func(self):
        cv.namedWindow("Image", cv.WINDOW_NORMAL)
        is_exit_preview_flag = False

        vid_capture = cv.VideoCapture(self.vid_file_path)

        if (vid_capture.isOpened() == False):
            logging.error("Error opening the video file")
            raise RuntimeError

        fps = vid_capture.get(cv.CAP_PROP_FPS)
        logging.info(f"Detected video frame rate : {fps}")

        ret, frame = vid_capture.read()  # the first frame

        if not ret:
            logging.info("Couldn't read the video")
            raise RuntimeError

        height, width, channels = frame.shape

        line_thickness = 10

        while True:
            frame_count = 1

            vid_capture = cv.VideoCapture(self.vid_file_path)

            if (vid_capture.isOpened() == False):
                logging.error("Error opening the video file")
                raise RuntimeError

            frame_count = 1

            while (vid_capture.isOpened()):
                ret, frame = vid_capture.read()

                if not ret:
                    logging.info(
                        "Reached the end of the video. Going back to the start")
                    break

                cv.line(frame, (self.lane_start -
                                line_thickness, 1), (self.lane_start -
                                                     line_thickness, height), (0, 255, 0), line_thickness)
                cv.line(frame, (self.lane_end +
                                line_thickness, 1), (self.lane_end +
                                                     line_thickness, height), (0, 0, 255), line_thickness)

                cv.line(frame, (self.lane_start, height -
                                self.detection_height), (self.lane_end, height -
                                                         self.detection_height), (255, 255, 255), line_thickness)

                cv.imshow('Image', frame)
                cv.waitKey(int(1 / fps * 1000))

                if cv.getWindowProperty('Image', cv.WND_PROP_VISIBLE) < 1:
                    is_exit_preview_flag = True
                    break

                frame_count += 1

            if is_exit_preview_flag:
                break

        #cv.destroyAllWindows()

    @Slot()
    def start_preview(self):
        if self.preview_thread is not None:
            self.preview_thread._stop()
            logging.info("Joined preview_thread")

        self.preview_thread =threading.Thread(target=self.start_preview_func)
        logging.info("Created preview_thread")
        self.preview_thread.run()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    ret = app.exec()

    if window.preview_thread is not None:
        window.preview_thread._stop()
        logging.info("Joined preview_thread")

    cv.destroyAllWindows()

    sys.exit(ret)
