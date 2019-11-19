import io
import time
import datetime
import threading
import logging
import base64
import http
import tornado.web
import tornado.websocket
import tornado.gen
import asyncio
import traceback

class StreamingWebSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        # allow access
        return True

    def initialize(self, server, logger):
        self.server = server
        self.logger = logger

    async def open(self):
        self.logger.debug("new connection: %s", self.request.remote_ip)
        #self.write_message("Hello World")
        self.server.register_client(self)
        interval = 1.0 / self.server.camera.framerate * 1000
        self.callback = tornado.ioloop.PeriodicCallback(self.send_image, interval)
        self.callback.start()

    def on_message(self, message):
        self.logger.debug("on_message: %s", message)
 
    def on_close(self):
        self.logger.debug("connection: %s closed", self.request.remote_ip)
        self.server.unregister_client(self)
        self.callback.stop()

    @tornado.gen.coroutine
    def send_image(self):
        jpg = self.server.camera.current_jpg
        self.write_message(bytes(jpg), binary=True)

class WebSocketStreamingServer(tornado.web.Application):
    def __init__(self, address, camera,log_level):
        self.name = self.__class__.__name__ + "-" + str(address[1])
        self.address = address
        self.camera = camera
        self.log_level = log_level
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(log_level)
        self.shutdown = False
        self._lock = threading.Lock()
        self._clients = []
        self.run_thread = None
        self.run_tornado_thread = None
        handlers = [(r"/", StreamingWebSocketHandler, {'server': self, 'logger': self._logger})]
        settings = {'debug': True}
        super().__init__(handlers, **settings)

    def start(self):
        self._logger.info("starting")
        self.shutdown = False
        self.listen(self.address[1], address=self.address[0])
        self.loop = asyncio.new_event_loop()
        self.run_tornado_thread = threading.Thread(target=self.run_tornado, args=())
        self.run_tornado_thread.start()
        #self.run_thread = threading.Thread(target=self.run, args=())
        #self.run_thread.start()

    def stop(self):
        self._logger.info("stopping")
        self.shutdown = True
        if self.ioloop is not None:
            self.ioloop.add_callback(self.ioloop.stop)
        if self.run_tornado_thread is not None:
            self._logger.debug("join th:%s", self.run_tornado_thread.getName())
            self.run_tornado_thread.join()
        if self.run_thread is not None:
            self._logger.debug("join th:%s", self.run_thread.getName())
            self.run_thread.join()
        self._logger.info("stopped")
        
    def run_tornado(self):
        try:
            asyncio.set_event_loop(self.loop)
            self.ioloop = tornado.ioloop.IOLoop.instance()
            self.ioloop.start()
        except Exception as ex:
            self.shutdown = True
            self._logger.error("run_tornado exception: %s", ex)
        self._logger.debug("tornado terminated")

    def run(self):
        self._logger.info("started")
        frame_rate_delay = 1.0 / self.camera.framerate
        last_frame_time = 0
        try:
            asyncio.set_event_loop(self.loop)

            while not self.shutdown:
                if last_frame_time != 0:
                    delay = time.time() - last_frame_time
                    if delay < frame_rate_delay:
                        time.sleep(frame_rate_delay - delay)

                jpg = self.camera.current_jpg
                self.send_data_to_all(jpg)
                last_frame_time = time.time()
        except Exception as ex:
            self.shutdown = True
            self._logger.error("run exception: %s", ex)
        self._logger.debug("terminated")

    def send_data_to_all(self, data):
        try:
            if data is None:
                return

            data = bytes(data)
            clients = []
            self._lock.acquire()
            try:
                clients = self._clients.copy()
            finally:
                self._lock.release()

            for client in clients: 
                try:
                    client.write_message(data, binary=True)
                except Exception as ex:
                    self._logger.error("write_message exception: %s is_bytes=%s len=%s", ex, isinstance(data, bytes), len(data))
                    print(ex)
                    traceback.print_exc()
        except Exception as ex:
            self._logger.error("send_data_to_all exception: %s", ex)

    def register_client(self, client):
        self._lock.acquire()
        try:
            if client not in self._clients:
                self._clients.append(client)
            self._logger.debug("register client:%s #clients:%s", client.request.remote_ip, len(self._clients))
            dummy = 0
        finally:
            self._lock.release()

    def unregister_client(self, client):
        self._lock.acquire()
        try:
            if client in self._clients:
                self._clients.remove(client)
                self._logger.debug("unregister client:%s #clients:%s", client.request.remote_ip, len(self._clients))
            dummy = 0
        finally:
            self._lock.release()


    
         
