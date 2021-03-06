import sys
from datetime import datetime

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtMultimedia

import cv2
import numpy as np

from controller import Detection, VideoThread

s = 0
m = 0
h = 0


class MainWindow(QtWidgets.QMainWindow):
    """Main window of the program"""

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.display_width = 500
        self.display_height = 400
        self.camera_label = QtWidgets.QLabel(self)
        self._run = False

        # timer event
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.time)

        self.ui()

    # User interface of the application

    def ui(self):
        """Setting up the UI"""

        # general window settings
        self.setWindowTitle('Drowsiness detector')
        self.setFixedSize(QtCore.QSize(900, 600))
        self.show()

        # setting up the layouts
        self.general_layout = QtWidgets.QVBoxLayout()
        self.camera_layout = QtWidgets.QVBoxLayout()
        self.info_layout = QtWidgets.QHBoxLayout()

        # container and layout for the feed
        self.feed_container = QtWidgets.QWidget()
        self.feed_layout = QtWidgets.QVBoxLayout()
        self.feed_container.setLayout(self.feed_layout)

        # container and layout for the settings
        self.settings_container = QtWidgets.QWidget()
        self.settings_layout = QtWidgets.QVBoxLayout()
        self.settings_container.setLayout(self.settings_layout)

        self.general_layout.addLayout(self.camera_layout)
        self.general_layout.addLayout(self.info_layout)

        # separator widget [line dividing feed and settings]
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setLineWidth(1)

        # adding containers to info layout
        self.info_layout.addWidget(self.feed_container)
        self.info_layout.addWidget(separator)
        self.info_layout.addWidget(self.settings_container)

        # setting up the central widget
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setLayout(self.general_layout)
        self.setCentralWidget(self.central_widget)

        self.setStyleSheet('''
            QMainWindow {
                background-color: #282c34; 
                color: #abb2bf; 
                font-family: Fira code; 
                font-size: 15px;
            } 

            .QPushButton {
                background-color: #5c6370;
                color: #abb2bf;
                font-family: Fira code;
                font-size: 15px;
                margin-top: 5px;
                border-radius: 5px;
            }

            .QLabel {
                color: #abb2bf;
                font-size: 15px;
            }

            .QDialog {
                background-color: #282c34;
            }

        ''')

        self.menu_bar()
        self.camera_section()
        self.info_section()

        face_haarcascade = 'haarcascade_frontalface_default.xml'
        eyes_haarcascade = 'haarcascade_eye.xml'
        self.detection = Detection(
            face_haarcascade_name=face_haarcascade, eyes_haarcascade_name=eyes_haarcascade)

    def menu_bar(self):
        """Setting up the menu bar"""

        self.menu = self.menuBar()
        self.menu.setStyleSheet(
            'font-size: 15px; background-color: #21252b; color: #abb2bf;')

        self.exit_action = QtWidgets.QAction('Exit', self)
        self.exit_action.triggered.connect(sys.exit)

        self.file_menu = self.menu.addMenu('&File')
        self.file_menu.addAction(self.exit_action)

        self.about_menu = self.menu.addMenu('&About')

    def camera_section(self):
        """Setting up the camera section"""

        self.background = QtGui.QPixmap(
            self.display_width, self.display_height)
        self.background.fill(QtGui.QColor('darkGray'))
        self.camera_label.setPixmap(self.background)
        self.camera_label.setAlignment(QtCore.Qt.AlignCenter)
        self.camera_layout.addWidget(self.camera_label)

    def info_section(self):
        """Merging the feed and settings section"""

        self.feed()
        self.settings()

    def feed(self):
        """Setting up the feed section"""

        header = QtWidgets.QLabel('<h2>Feed</h2>')
        header.setAlignment(QtCore.Qt.AlignCenter)
        self.feed_layout.addWidget(header)

        bottom_layout = QtWidgets.QGridLayout()
        self.feed_layout.addLayout(bottom_layout)

        duration = QtWidgets.QLabel('Duration:                    ')
        self.placeholder_duration = QtWidgets.QLabel('00 : 00 : 00')
        bottom_layout.addWidget(duration, 0, 0)
        bottom_layout.addWidget(self.placeholder_duration, 0, 1)

        activity = QtWidgets.QLabel('Activity:')
        placeholder_activity = QtWidgets.QLabel('Drowsiness Detected')
        bottom_layout.addWidget(activity, 1, 0)
        bottom_layout.addWidget(placeholder_activity, 1, 1)

        self.start_button = QtWidgets.QPushButton('START')
        self.start_button.setCheckable(True)
        self.start_button.setFixedSize(QtCore.QSize(70, 30))
        bottom_layout.addWidget(self.start_button)

        self.start_button.pressed.connect(self.control_btn)

    def control_btn(self):
        if not self.start_button.isChecked():
            self.start_btn()
        else:
            self.stop_btn()

    def start_btn(self):
        self._run = True
        self.start_thread()
        self.start_timer()
        self.start_button.setText('Stop')
        print('Starting execution')

    def stop_btn(self):
        self._run = False
        self.thread.stop()
        self.reset_timer()
        self.start_button.setText('Start')
        print('Stopping execution')

    def settings(self):
        header = QtWidgets.QLabel('<h2>Settings</h2>')
        header.setAlignment(QtCore.Qt.AlignCenter)
        self.settings_layout.addWidget(header)

        bottom_layout = QtWidgets.QGridLayout()
        self.settings_layout.addLayout(bottom_layout)

        camera_label = QtWidgets.QLabel('Select camera:          ')
        camera_combo_box = QtWidgets.QComboBox()
        self.available_cameras = [device.description(
        ) for device in QtMultimedia.QCameraInfo.availableCameras()]
        camera_combo_box.addItems(self.available_cameras)
        bottom_layout.addWidget(camera_label, 0, 0)
        bottom_layout.addWidget(camera_combo_box, 0, 1)

        sound_label = QtWidgets.QLabel('Select sound:')
        sound_combo_box = QtWidgets.QComboBox()
        sound_combo_box.addItems(['Siren', 'Soft', 'Cools'])
        bottom_layout.addWidget(sound_label, 1, 0)
        bottom_layout.addWidget(sound_combo_box, 1, 1)

        log_button = QtWidgets.QPushButton('LOGS')
        log_button.setFixedSize(QtCore.QSize(70, 30))
        bottom_layout.addWidget(log_button)
        log_button.clicked.connect(self.LogWindow)

        self.camera = 0
        camera_combo_box.currentIndexChanged.connect(self.selectionChange)

    def selectionChange(self, i):
        self.camera = i

    @QtCore.pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        image_data_slot = self.detection.image_data_slot(cv_img)
        qt_img = self.convert_cv_qt(image_data_slot)
        if self._run:
            self.camera_label.setPixmap(qt_img)
        else:
            self.camera_label.setPixmap(self.background)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(
            rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(
            self.display_width, self.display_height, QtCore.Qt.KeepAspectRatio)
        return QtGui.QPixmap.fromImage(p)

    def start_thread(self):
        # Create the video capture thread
        self.thread = VideoThread(self.camera)
        # Connect its signal the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # Start the Thread
        self.thread.start()

    def reset_timer(self):
        global s, m, h

        self.timer.stop()

        h = 0
        m = 0
        s = 0

        hr, min, sec = self.format_time(h, m, s)

        time = f"{hr} : {min} : {sec}"


        self.placeholder_duration.setText(time)

    def start_timer(self):
        global s, m, h
        self.timer.start(1000)


    def time(self):
        global s, m, h

        if s < 59:
            s += 1
        else:
            if m < 59:
                s = 0
                m += 1
            elif m == 59 and h < 24:
                h += 1
                m = 0
                s = 0
            else:
                self.timer.stop()
        
        hr, min, sec = self.format_time(h, m, s)

        time = f"{hr} : {min} : {sec}"

        self.placeholder_duration.setText(time)

    def format_time(self, h, m, s):
        if len(str(h)) == 1:
            h = '0' + str(h)

        if len(str(m)) == 1:
            m = '0' + str(m)

        if len(str(s)) == 1:
            s = '0' + str(s)

        return h, m, s

    def LogWindow(self):

        log = LogsWindow(self)
        log.exec_()

class LogsWindow(QtWidgets.QDialog):
    "Logs window to give information about a session"

    def __init__(self, *args, **kwargs):
        super(LogsWindow, self).__init__(*args, **kwargs)
        
        self.setWindowTitle('LOGS')
        self.setFixedSize(QtCore.QSize(500, 500))

        log_layout = QtWidgets.QVBoxLayout(self)
        date_time = datetime.today().now()

        title_label = QtWidgets.QLabel(f"LOG File [{date_time.strftime('%Y-%m-%d -- %H:%M:%S')}]")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        log_layout.addWidget(title_label)

        formLayout =QtWidgets.QFormLayout()
        groupBox = QtWidgets.QGroupBox()
        time = []
        status = []

        for i in  range(10):
            self.count += 1
            time.append(QtWidgets.QLabel(f"{date_time.strftime('%H:%M:%S')} --"))
            status.append(QtWidgets.QLabel("Event"))
            formLayout.addRow(time[i], status[i])

        groupBox.setLayout(formLayout)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(groupBox)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(400)
        log_layout.addWidget(scroll)
        
        self.setLayout(log_layout)


        self.setStyleSheet(
            '''
            .QLabel {
                color: #000;
                font-size: 18px;
            }           
            '''
        )

        groupBox.setStyleSheet(
            '''
            .QLabel {
                color: #000;
                font-weight: 300;
            }
            '''
        )




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
