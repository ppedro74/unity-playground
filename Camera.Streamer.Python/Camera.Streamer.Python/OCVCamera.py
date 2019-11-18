import threading
import logging
#import sys
#import os
#import io
#import datetime
import time
import cv2
import Camera

class OCVCamera(Camera.Camera):

    def __init__(self, device_index, resolution, quality, framerate, log_level):
        self.name = self.__class__.__name__ + "-" + str(device_index)
        self.device_index = device_index
        self.resolution = resolution
        self.quality = quality
        self.framerate = framerate
        self.log_level = log_level
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(log_level)
        self.shutdown = False
        self._lock = threading.Lock()
        self._video_capture = None
        self._current_frame = None
        self._current_jpg = None

    def start(self):
        self.shutdown = False

        self._video_capture = cv2.VideoCapture(self.device_index)
        if not self._video_capture.isOpened():
            self._logger.error("can't open video device:%s", self.device_index)
            return

        self._video_capture.set(cv2.CAP_PROP_FPS, self.framerate)
        self._video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self._video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

        w = self._video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self._video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if w!=self.resolution[0] or h!=self.resolution[1]:
            self._logger.error("video device:%s invalid resolution requested=% current=%s", 
                              self.device_index,
                              self.resolution,
                              (w,h))
            self._video_capture.release()
            return

        fps = self._video_capture.get(cv2.CAP_PROP_FPS) 
        if fps!=self.framerate:
            self._logger.warning("fps setting ignored requested=%s current=%s", self.framerate, fps)

        self.run_thread = threading.Thread(target=self.run, args=())
        self.run_thread.start()

    def stop(self):
        if self.shutdown:
            self._logger.warning("Already stopped")
            return

        self._logger.debug("stopping")
        self.shutdown = True
        self._logger.debug("join th:%s", self.run_thread.getName())
        self.run_thread.join()

    def run(self):
        self._logger.debug("running thread:%s", threading.current_thread().getName())
    
        try:
            self.main()
        except Exception as ex:
            self.shutdown = True
            self._logger.debug("exception %s", ex)

        try:
            self.run_end()
        except Exception as ex:
            self._logger.debug("end exception %s", ex)

        self._logger.debug("terminated")
    
    def run_end(self):
        self._video_capture.release()

    @property
    def current_jpg(self):
        self._lock.acquire()
        try:
            if self._current_jpg is None and self._current_frame is not None:
                ret, jpg = cv2.imencode('.jpg', self._current_frame, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
                if ret:
                    self._current_jpg = bytearray(jpg)

            return self._current_jpg
        finally:
            self._lock.release()

    def main(self):
        while not self.shutdown:
            ret, frame = self._video_capture.read()
            if ret:
                self._lock.acquire()
                try:
                    self._current_frame = frame
                    self._current_jpg = None
                finally:
                    self._lock.release()
            else:
                self._logger.warning("no frame")

        

