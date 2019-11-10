import logging
import time
import socketserver
import http
import urllib.parse

class HttpStreamingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

class HttpStreamingServerRequestHandler(http.server.BaseHTTPRequestHandler):
    INDEX_PAGE="""\
    <html>
    <head>
    <title>MJPEG Video Feed</title>
    </head>
    <body>
    <center><h1>mjpeg:</h1></center>
    <center><img src="http://{0}/mjpg" width="{1}" height="{2}"></center>
    <center><h3>Resolution: {1}x{2}</h3></center>
    </body>
    </html>
    """
    BOUNDARY = "_EndOfJpg_"
    
    def log_message(self, format, *args):
        #silent the std out log
        return

    def do_GET(self):
        uri = urllib.parse.urlparse(self.path, 'http')
        
        host = uri.hostname
        if not host:
            host = self.headers.get('host', "")

        if uri.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = self.INDEX_PAGE.format(host, self.server.camera.resolution[0], self.server.camera.resolution[1])
            b = bytes(html, "utf8")
            self.wfile.write(b)
        elif uri.path == '/jpg':
            jpg = self.server.camera.current_jpg
            if jpg is not None:
                self.send_response(200)
                self.send_header('Age', 0)
                self.send_header('Cache-Control', 'no-cache, private')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header("Content-length", str(jpg.size))
                self.end_headers()
                self.wfile.write(jpg.tostring())
            else:
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(bytes("500 Internal Server Error : no jpg", "utf8"))
        elif uri.path == '/mjpg':
            self.send_response(200)
            self.send_header("Content-type", "multipart/x-mixed-replace; boundary={}".format(self.BOUNDARY))
            self.end_headers()

            frame_rate_delay = 1.0 / self.server.camera.framerate
            last_frame_time = 0

            while not self.server.camera.shutdown:
                if last_frame_time != 0:
                    delay = time.time() - last_frame_time
                    if delay < frame_rate_delay:
                        time.sleep(frame_rate_delay - delay)

                jpg = self.server.camera.current_jpg
                if jpg is not None:
                    self.wfile.write("--{}\r\n".format(self.BOUNDARY).encode("utf-8"))
                    self.send_header("Content-type", "image/jpeg")
                    self.send_header("Content-length", str(jpg.size))
                    self.end_headers()
                    self.wfile.write(jpg.tostring())
                    self.wfile.write("\r\n".encode("utf-8"))

                last_frame_time = time.time()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes("404. Not found", "utf8"))
        return
