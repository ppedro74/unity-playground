import threading
import logging
import asyncio
import websockets
import base64


class WebSocketStreamingServer:
    def __init__(self, address, camera,log_level):
        self.name = self.__class__.__name__ + "-" + str(address[1])
        self.address = address
        self.camera = camera
        self.log_level = log_level
        self._logger = logging.getLogger(self.name)
        self._logger.setLevel(log_level)
        self._shutdown = False
        self._lock = threading.Lock()
        self._clients = set()
        self.run_thread = None
        self.loop = None

    def start(self):
        self._logger.debug("starting")
        self.run_thread = threading.Thread(target=self.run, args=())
        self.run_thread.start()

    def stop(self):
            self._logger.debug("stopping")
            self._shutdown = True
            if self.loop is not None:
                self.loop.stop()
            if self.run_thread is not None:
                self._logger.debug("join th:%s", self.run_thread.getName())
                self.run_thread.join()
            self._logger.debug("stopped")
        
    def run(self):
        self._logger.debug("started")
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.start_server = websockets.serve(self.message_handler, self.address[0], self.address[1])
            self.loop.run_until_complete(self.start_server)
            self.loop.run_forever()
        except Exception as ex:
            self._shutdown = True
            self._logger.error("run exception: %s", ex)
        self._logger.debug("terminated")
        self.loop.close()

    async def message_handler(self, websocket, path):
        try:
            self._logger.debug("client connected")
            task = self.loop.create_task(self.start_streaming(websocket))

            self._lock.acquire()
            try:
                self._clients.add(websocket)
            finally:
                self._lock.release()

            while not self._shutdown:
                async for message in websocket:
                    self._logger.debug("recv: %s", message)
        except Exception as ex:
            self._logger.error("message_handler exception: %s", ex)
        finally:
            self._lock.acquire()
            try:
                self._clients.remove(websocket)
            finally:
                self._lock.release()
            self._logger.debug("client disconnected")

    async def start_streaming(self, websocket):
        frame_rate_delay = 1.0 / self.camera.framerate

        try:
            while not self._shutdown:
            
                jpg = self.camera.current_jpg
                #base64str = base64.encodestring(jpg).decode()
                #base64str = base64.b64encode(jpg)
                #await websocket.send(base64str)
                await websocket.send(bytes(jpg))
                await asyncio.sleep(frame_rate_delay)
        except Exception as ex:
            self._logger.error("start_streaming exception: %s", ex)

         
