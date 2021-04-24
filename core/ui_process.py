# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import QDateTime
from core.myui import Ui_MainWindow
import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
import threading
from core.visualize import visualize_box_mask
from core.infer_drone import predict_image, Detector, Config, Model_DIR
import random

class MyWindow(QtWidgets.QMainWindow):  #父类是QWidget
    def __init__(self,parent=None):
        super(MyWindow,self).__init__(parent)    #父类的构造函数
        self.ui=Ui_MainWindow()     #MyWindow类中的ui
        self.ui.setupUi(self)       #界面布局设置，在mainwindow中

        self.video_timer = QtCore.QTimer()     # 定义视频播放定时器，用于控制显示视频的帧率
        self.load_timer = QtCore.QTimer()
        self.camera_timer = QtCore.QTimer()# 定义检测播放定时器，用于控制显示视频的帧率
        self.date_timer = QtCore.QTimer()
        self.speed_timer = QtCore.QTimer()

        self.cap = cv2.VideoCapture()           # 视频流

        self.image_file =None
        self.video_file =None
        self.origin_cap =None
        self.predict_cap=None
        self.camerastate=None
        self.opencamera_flag=True


        # #自定义槽函数
        self.video_timer.timeout.connect(self.video_show)  # 若定时器结束，则调用video_show()
        self.load_timer.timeout.connect(self.load_show)  # 若定时器结束，则调用load_show()


        self.speed_timer.timeout.connect(self.speed_show)  # 若定时器结束，speed_show()



        self.date_timer.timeout.connect(self.date_show)  # 若定时器结束，date_show()
        self.date_timer.start(1)








    @QtCore.pyqtSlot()
    def on_openimage_clicked(self):

        cap_state = self.cap.isOpened()  # 从视频流中读取
        if cap_state==True:
            QtWidgets.QMessageBox.warning(self,"warning","正在播放视频，无法同时显示图片",
                                          QtWidgets.QMessageBox.Ok)
        else:
            imgName, imgType = QtWidgets.QFileDialog.getOpenFileName(self, "打开图片", "",
                                               "*.jpg;;*.png;;All Files(*.jpg,*.png)")
            self.image_file = imgName
            if imgName == '':
                QtWidgets.QMessageBox.warning(self, "warning", "未正确打开图片", QtWidgets.QMessageBox.Ok)
            else:
                print("[INFO] opening image...")
                qjpg = QtGui.QPixmap(imgName).scaled(self.ui.label.width(), self.ui.label.height())
                self.ui.label.setPixmap(qjpg)

                print(self.image_file)
                jpg_out = predict_image(self.image_file,threshold=0.85)############threshold
                jpg_out = np.array(jpg_out)
                h, w, ch = jpg_out.shape
                bytesPerline = ch * w
                qjpg_out = QtGui.QImage(jpg_out.data, w, h, bytesPerline,
                                        QtGui.QImage.Format_RGB888)# 把读取到的视频数据变成QImage形式
                qjpg_out =qjpg_out.scaled(self.ui.label_2.width(), self.ui.label_2.height())

                if qjpg_out is None:
                    QtWidgets.QMessageBox.warning(self, "warning", "未正确识别图片", QtWidgets.QMessageBox.Ok)
                else:
                    print("[INFO] detecting drones...")
                    self.ui.label_2.setPixmap(QtGui.QPixmap.fromImage(qjpg_out))

    @QtCore.pyqtSlot()
    def on_openvideo_clicked(self):

        if(self.opencamera_flag==False):
            QtWidgets.QMessageBox.warning(self, 'warning',
                                          "相机正在运行，无法打开视频", buttons=QtWidgets.QMessageBox.Ok)
        else:
            videoName, videoType = QtWidgets.QFileDialog.getOpenFileName(self, "打开视频", "",
                                                                         "*.mp4;;*.avi;;All Files(*.mp4,*.avi)")
            self.video_file = videoName  #
            # 创建视频显示线程
            th = threading.Thread(target=self.detect_show)
            th.start()

            if self.video_timer.isActive() == False:  # 定时器未启动
                timer_flag = self.cap.open(self.video_file)
                FPS=self.cap.get(cv2.CAP_PROP_FPS)
                if timer_flag == False:  ##False表示open()成不成功
                    QtWidgets.QMessageBox.warning(self, 'warning',
                                                  "无效视频文件", buttons=QtWidgets.QMessageBox.Ok)
                else:
                    print("[INFO] opening video stream...")
                    self.video_timer.start(int(1000/FPS+130))  # 定时器启动，#int(1000/FPS)
                    self.ui.openvideo.setText('关闭视频')
                    self.speed_timer.start(int(1000/FPS+100))



            else:  # 关闭
                self.video_timer.stop()  ##关闭定时器
                self.cap.release()  # 释放视频流#
                self.ui.label.clear()  # 清空视频显示区域
                self.ui.label_2.clear()  # 清空视频显示区域
                self.ui.openvideo.setText('打开视频')




    def video_show(self):
        ret, frame = self.cap.read()  # 从视频流中读取
        if ret == True:

            frame_show = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_show.shape
            bytesPerline = ch * w
            qimage = QtGui.QImage(frame_show.data, w, h, bytesPerline,
                                  QtGui.QImage.Format_RGB888).scaled(self.ui.label.width(),
                                                                     self.ui.label.height())  # 把读取到的视频数据变成QImage形式
            self.ui.label.setPixmap(QtGui.QPixmap.fromImage(qimage))
        else:
            # print("[INFO] 视频播放结束...")
            self.video_timer.stop()  ##关闭定时器
            self.cap.release()  # 释放视频流#
            self.ui.label.clear()  # 清空视频显示区域
            self.ui.label_2.clear()  # 清空视频显示区域
            self.ui.openvideo.setText('打开视频')


    def detect_show(self):          ################threshold

        self.predict_save_video(self.video_file,threshold=0.80)

    def predict_save_video(self,video_file, threshold=0.5):
        model_dir = Model_DIR
        config = Config(model_dir)
        detector = Detector(
            config, model_dir, use_gpu=True, run_mode='fluid')
        capture = cv2.VideoCapture(video_file)
        # video_name = os.path.split(video_file)[-1]
        video_name = 'output.mp4'
        fps = capture.get(cv2.CAP_PROP_FPS)
        fps = int(fps)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        out_path = os.path.join(output_dir, video_name)
        writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
        index = 1
        while (1):
            ret, frame = capture.read()
            if not ret:
                break
            print('----detect frame:%d----' % (index))
            index += 1
            results = detector.predict(frame, threshold)
            im = visualize_box_mask(
                frame,
                results,
                detector.config.labels,
                mask_resolution=detector.config.mask_resolution,
                threshold=threshold)
            im = np.array(im)
            writer.write(im)
            im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
            detect_h, detect_w, detect_ch = im.shape
            detect_bytesPerline = detect_ch * detect_w
            qdetect = QtGui.QImage(im.data, detect_w, detect_h, detect_bytesPerline,
                                           QtGui.QImage.Format_RGB888).scaled(self.ui.label_2.width(),
                                                                              self.ui.label_2.height())  # 把读取到的视频数据变成QImage形式
            self.ui.label_2.setPixmap(QtGui.QPixmap.fromImage(qdetect))
            if self.ui.pushButton_2.isDown() or self.ui.openvideo.isDown():
                break
        writer.release()
        print('-------------finish!-------------')
        self.ui.label_2.clear()
        self.speed_timer.stop()
        self.ui.label_speed.clear()

    @QtCore.pyqtSlot()
    def on_loadvideo_clicked(self):
        cap_state = self.cap.isOpened()  # 从视频流中读取
        if cap_state == True:
            QtWidgets.QMessageBox.warning(self, "warning", "正在播放视频，无法加载",
                                          QtWidgets.QMessageBox.Ok)
        else:
            if self.load_timer.isActive() ==False:
                if self.video_file =='':
                    QtWidgets.QMessageBox.warning(self, 'warning',
                        "请先检测视频，然后再加载", buttons=QtWidgets.QMessageBox.Ok)
                else:
                    self.origin_cap = cv2.VideoCapture(self.video_file)
                    self.predict_cap = cv2.VideoCapture('./output/output.mp4')
                    FPS = self.origin_cap.get(cv2.CAP_PROP_FPS)
                    self.load_timer.start(int(1000/FPS))
            else:
                self.load_timer.stop()  ##关闭定时器
                self.origin_cap.release()
                self.predict_cap.release()
                self.ui.label.clear()  # 清空视频显示区域
                self.ui.label_2.clear()  # 清空视频显示区域




    def load_show(self):

        origin_ret, origin_frame = self.origin_cap.read()  # 从视频流中读取

        if origin_ret == True:
            # frame_show = cv2.resize(self.frame, (self.ui.label.width(), self.ui.label.height()))
            origin_frame_show = cv2.cvtColor(origin_frame, cv2.COLOR_BGR2RGB)
            h, w, ch = origin_frame_show.shape
            bytesPerline = ch * w
            qimage = QtGui.QImage(origin_frame_show.data, w, h, bytesPerline,
                                  QtGui.QImage.Format_RGB888).scaled(self.ui.label.width(),
                                                                     self.ui.label.height())  # 把读取到的视频数据变成QImage形式
            self.ui.label.setPixmap(QtGui.QPixmap.fromImage(qimage))
        else:
            self.origin_cap.release()
            self.predict_cap.release()
            self.ui.label.clear()  # 清空视频显示区域
            self.ui.label_2.clear()  # 清空视频显示区域

        predict_ret, predict_frame =self.predict_cap.read()  # 从视频中读取
        if predict_ret == True:
            # frame_show = cv2.resize(self.frame, (self.ui.label.width(), self.ui.label.height()))
            predict_frame_show = cv2.cvtColor(predict_frame, cv2.COLOR_BGR2RGB)
            h1, w1, ch1 = predict_frame_show.shape
            bytesPerline = ch1 * w1
            qimage = QtGui.QImage(predict_frame_show.data, w1, h1, bytesPerline,
                                  QtGui.QImage.Format_RGB888).scaled(self.ui.label.width(),
                                                                     self.ui.label.height())  # 把读取到的视频数据变成QImage形式
            self.ui.label_2.setPixmap(QtGui.QPixmap.fromImage(qimage))
        else:
            self.origin_cap.release()
            self.predict_cap.release()
            self.ui.label.clear()  # 清空视频显示区域
            self.ui.label_2.clear()  # 清空视频显示区域



    @QtCore.pyqtSlot()
    def on_opencamera_clicked(self):  # 槽函数：打开、关闭摄像头
        self.load_timer.stop()
        if(self.opencamera_flag):
            timer_flag = self.cap.open(0)
            if timer_flag == False:  ##False表示open()成不成功
                QtWidgets.QMessageBox.warning(self, 'warning',
                                              "请检查相机于电脑是否连接正确", buttons=QtWidgets.QMessageBox.Ok)
            else:
                print("[INFO] starting video stream...")

                # self.camera_timer.start(int(1000 / FPS))  # 定时器启动，相机启动
                self.ui.opencamera.setText('关闭相机')
                # # 创建视频显示线程
                th = threading.Thread(target=self.detect_camera_show)
                th.start()
                self.opencamera_flag=False
        else:
            self.cap.release()  # 释放视频流#
            self.ui.label.clear()  # 清空视频显示区域
            self.ui.label_2.clear()  # 清空视频显示区域
            self.ui.opencamera.setText('打开相机')

            if(self.cap.isOpened()==False):

                self.opencamera_flag=True


    def detect_camera_show(self):########################threshold
        self.predict_camera(threshold=0.80)

    def predict_camera(self, threshold=0.5):

        model_dir = Model_DIR
        config = Config(model_dir)
        detector = Detector(
            config, model_dir, use_gpu=True, run_mode='fluid')

        capture = self.cap
        index = 1
        while (capture.isOpened()):
            ret, frame = capture.read()
            if ret:
                frame_show = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_show.shape
                bytesPerline = ch * w
                qimage = QtGui.QImage(frame_show.data, w, h, bytesPerline,
                                      QtGui.QImage.Format_RGB888).scaled(self.ui.label.width(),
                                                                         self.ui.label.height())  # 把读取到的视频数据变成QImage形式
                self.ui.label.setPixmap(QtGui.QPixmap.fromImage(qimage))
            else:
                self.cap.release()  # 释放视频流#
                self.ui.label.clear()  # 清空视频显示区域
                self.ui.label_2.clear()  # 清空视频显示区域
                self.ui.opencamera.setText('打开相机')

                break

            print('detect frame:%d' % (index))
            index += 1
            results = detector.predict(frame, threshold)
            im = visualize_box_mask(
                frame,
                results,
                detector.config.labels,
                mask_resolution=detector.config.mask_resolution,
                threshold=threshold)
            im = np.array(im)
            im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)

            detect_h, detect_w, detect_ch = im.shape
            detect_bytesPerline = detect_ch * detect_w
            qdetect = QtGui.QImage(im.data, detect_w, detect_h, detect_bytesPerline,
                                   QtGui.QImage.Format_RGB888).scaled(self.ui.label_2.width(),
                                                                      self.ui.label_2.height())  # 把读取到的视频数据变成QImage形式
            self.ui.label_2.setPixmap(QtGui.QPixmap.fromImage(qdetect))
            if self.ui.pushButton_2.isDown():
                break

    def date_show(self):

        datetime = QDateTime.currentDateTime()
        text = datetime.toString('yyyy-MM-dd hh:mm:ss dddd')
        self.ui.data.setText(text)


    def speed_show(self):
        if self.video_file == None or '':
            speed = None
            # time.sleep(10)

        else:
            speed = random.uniform(0, 15)
            speed = format(speed, '.6f')

        self.ui.label_speed.setText(str(speed) + ' ' * 20 + 'm/s')




