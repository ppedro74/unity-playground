import io
import logging
import threading 
import picamera
import Camera
import time

class RPICamera(Camera.Camera):

    def __init__(self, resolution, quality, framerate, log_level):
        self.name = self.__class__.__name__
        self.resolution = resolution
        self.quality = quality
        self.framerate = framerate
        self.log_level = log_level
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(log_level)
        self.shutdown = False
        self._lock = threading.Lock()
        self._camera = None
        self._current_jpg = None

    def start(self):
        self.shutdown = False
        self._camera = picamera.PiCamera()
        self._camera.resolution = self.resolution
        self._camera.framerate = self.framerate
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
        self._camera.stop_preview()

    @property
    def current_jpg(self):
        self._lock.acquire()
        try:
            return self._current_jpg
        finally:
            self._lock.release()

    def main(self):
        self._camera.start_preview()
        time.sleep(2)
        stream = io.BytesIO()
        for foo in self._camera.capture_continuous(stream, "jpeg", use_video_port=True):
            if self.shutdown:
                break

            stream.seek(0)
            jpg = stream.read()
            stream.seek(0)
            stream.truncate()

            self._lock.acquire()
            try:
                self._current_jpg = bytearray(jpg)
            finally:
                self._lock.release()
        return