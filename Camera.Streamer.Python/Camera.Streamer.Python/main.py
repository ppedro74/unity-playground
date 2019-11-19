import sys
import logging
import threading
import argparse
import asyncio
import tornado

async def aio_readline(loop):
    line = await loop.run_in_executor(None, sys.stdin.readline)
    return line

def main():
    logging.basicConfig(format="%(process)d-%(name)s-%(levelname)s-%(message)s", level=logging.INFO)
    logging.info("Starting... platform=%s", sys.platform)

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addr", type=str, default="0.0.0.0", help="Server http port")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Server http port")
    parser.add_argument("--width", type=int, default=640, help="Video frame width")
    parser.add_argument("--height", type=int, default=480, help="Video frame height")
    parser.add_argument("--fps", type=int, default=15, help="Video frames per second")
    parser.add_argument("--quality", type=int, default=95, help="Jpeg quality (0-100)")
    parser.add_argument("-vs", "--videostream", type=int, default=0, help="Videostream device number")
    parser.add_argument("-pi", "--picamera", action='store_true', help="Use raspberry pi camera")
    parser.add_argument("-t", "--type", 
                    default="http", 
                    const="http",
                    nargs="?",
                    choices=["http", "websocket"],
                    help="type http, websocket (default: %(default)s)")
    args = parser.parse_args()

    if args.picamera:
        #(1280,720)        
        import RPICamera
        camera = RPICamera.RPICamera((args.width, args.height), args.fps, args.quality, logging.DEBUG) 
    else:
        import OCVCamera
        camera = OCVCamera.OCVCamera(args.videostream, (args.width, args.height), args.quality, args.fps, logging.DEBUG)
    camera.start()

    address = (args.addr, args.port)
    server = None
    if args.type == "websocket":
        import WebSocketStreamingServer
        server = WebSocketStreamingServer.WebSocketStreamingServer(address, camera, logging.DEBUG)
        server.start()
    else:
        import HttpStreamingServer
        server = HttpStreamingServer.HttpStreamingServer(address, camera)
        server.start()

    try:
        #asyncio.set_event_loop_policy(tornado.platform.asyncio.AnyThreadEventLoopPolicy())
        #tornado.ioloop.IOLoop.instance().start()

        logging.info("===> Press Enter to quit...\n")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(aio_readline(loop))
        loop.close()

        #input("===> Press Enter to quit...\n")
        
        logging.info("*** Enter pressed ***")
    except KeyboardInterrupt:
        logging.info("*** KeyboardInterrupt ***")

    try:
        server.stop()
        camera.stop()
    except Exception as ex:
        logging.error("Shutdown exception: %s", ex)



if __name__ == '__main__' :
    main()
