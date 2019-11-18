import sys
import logging
import threading
import argparse

def main():
    logging.basicConfig(format="%(process)d-%(name)s-%(levelname)s-%(message)s", level=logging.INFO)
    logging.info("Starting... platform=%s", sys.platform)

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addr", type=str, default="0.0.0.0", help="Server http port")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Server http port")
    parser.add_argument("-fw", "--width", type=int, default=640, help="Video frame width")
    parser.add_argument("-fh", "--height", type=int, default=480, help="Video frame height")
    parser.add_argument("-fs", "--fps", type=int, default=15, help="Video frames per second")
    parser.add_argument("-jq", "--quality", type=int, default=95, help="Jpeg quality (0-100)")
    parser.add_argument("-vs", "--videostream", type=int, default=0, help="Videostream device number")
    parser.add_argument("-pi", "--picamera", action='store_true', help="Use raspberry pi camera")
    parser.add_argument("-t", "--type", 
                    default="http", 
                    const="http",
                    nargs="?",
                    choices=["http", "websocket"],
                    help="type http, websocket (default: %(default)s)")
    args = parser.parse_args()

    #(1280,720)

    if args.picamera:
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

    input("===> Press Enter to quit...\n")

    server.shutdown()
    camera.stop()

if __name__ == '__main__' :
    main()
