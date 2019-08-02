import board
import busio
import time
import os
import gc
from digitalio import DigitalInOut
from struct import *
import neopixel

from adafruit_esp32spi import adafruit_esp32spi
import adafruit_esp32spi.adafruit_esp32spi_wifimanager as wifimanager
import adafruit_esp32spi.adafruit_esp32spi_wsgiserver as server
from bmpReader import bmpReader


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

try:
    import json as json_module
except ImportError:
    import ujson as json_module

import adafruit_dotstar as dotstar
status_light = dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1, brightness=1)

print("Pixel Painter Web Server!")

esp32_cs = DigitalInOut(board.D10)
esp32_ready = DigitalInOut(board.D9)
esp32_reset = DigitalInOut(board.D7)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
# esp.set_ip_addr("192.168.0.177")
## Connect to wifi with secrets
wifi = wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light, debug=True)
wifi.create_ap()

pixel_pin = board.D5
num_pixels = 59
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=1, auto_write = False, pixel_order = neopixel.GRB)

# TODO: Move to separate File (and eventually remove in favor of CircuitPython_WSGI)
class SimpleWSGIApplication:
    """
    An example of a simple WSGI Application that supports 
    basic route handling and static asset file serving
    """

    INDEX = "/index.html"
    CHUNK_SIZE = 8912 # Number of bytes to send at once when serving files

    def on(self, method, path, request_handler):
        """
        Register a Request Handler for a particular HTTP method and path.
        request_handler will be called whenever a matching HTTP request is received.

        request_handler should accept the following args:
            (Dict environ)
        request_handler should return a tuple in the shape of:
            (status, header_list, data_iterable)

        :param str method: the method of the HTTP request
        :param str path: the path of the HTTP request
        :param func request_handler: the function to call
        """
        self._listeners[self._get_listener_key(method, path)] = request_handler

    def __init__(self, static_dir=None, debug=True):
        self._debug = debug
        self._listeners = {}
        self._start_response = None
        self._static = static_dir
        if self._static:
            self._static_files = ["/" + file for file in os.listdir(self._static)]

    def __call__(self, environ, start_response):
        """
        Called whenever the server gets a request.
        The environ dict has details about the request per wsgi specification.
        Call start_response with the response status string and headers as a list of tuples.
        Return a single item list with the item being your response data string.
        """
        if self._debug:
            self._log_environ(environ)

        self._start_response = start_response
        status = ""
        headers = []
        resp_data = []

        key = self._get_listener_key(environ["REQUEST_METHOD"].lower(), environ["PATH_INFO"])
        if key in self._listeners:
            status, headers, resp_data = self._listeners[key](environ)
        if environ["REQUEST_METHOD"].lower() == "get" and self._static:
            path = environ["PATH_INFO"]
            if path in self._static_files:
                status, headers, resp_data = self.serve_file(path, directory=self._static)
            elif path == "/" and self.INDEX in self._static_files:
                status, headers, resp_data = self.serve_file(self.INDEX, directory=self._static)

        self._start_response(status, headers)
        return resp_data

    def serve_file(self, file_path, directory=None):
        status = "200 OK"
        contentType = self._get_content_type(file_path)
        headers = [("Content-Type", contentType)]
        if (contentType == 'text/css'):
            headers.append(("cache-control", "public, max-age=604800, s-maxage=43200"))


        full_path = file_path if not directory else directory + file_path
        def resp_iter():
            with open(full_path, 'rb') as file:
                while True:
                    chunk = file.read(self.CHUNK_SIZE)
                    if chunk:
                        # time.sleep(0.05)
                        yield chunk
                    else:
                        break

        return (status, headers, resp_iter())

    def _log_environ(self, environ): # pylint: disable=no-self-use
        print("environ map:")
        for name, value in environ.items():
            if name == "wsgi.input":
                continue
            else:
                print(name, value)

    def _get_listener_key(self, method, path): # pylint: disable=no-self-use
        return "{0}|{1}".format(method.lower(), path)

    def _get_content_type(self, file): # pylint: disable=no-self-use
        ext = file.split('.')[-1]
        if ext in ("html", "htm"):
            return "text/html"
        if ext == "js":
            return "application/javascript"
        if ext == "css":
            return "text/css"
        if ext in ("jpg", "jpeg"):
            return "image/jpeg"
        if ext == "png":
            return "image/png"
        return "text/plain"


class pixel_painter_application:
    def __init__(self):
        self.is_displaying = False
        self.loop = False
        self.current_display = []
    
    # Our HTTP Request handlers
    def led_on(self,environ): # pylint: disable=unused-argument
        print("led on!")
        status_light.fill((0, 0, 100))
        return web_app.serve_file("static/index.html")

    def led_off(self,environ): # pylint: disable=unused-argument
        print("led off!")
        status_light.fill(0)
        return web_app.serve_file("static/index.html")

    def led_color(self,environ): # pylint: disable=unused-argument
        json = json_module.loads(environ["wsgi.input"].getvalue())
        print(json)
        rgb_tuple = (json.get("r"), json.get("g"), json.get("b"))
        status_light.fill(rgb_tuple)
        return ("200 OK", [], [])

    def load_image(self,environ):
        print("yo!")
        file_name = '/static/current_image.bmp'
        b = environ["wsgi.input"]
        file = open(file_name, "wb")
        file.write(bytes(b.getvalue(),'utf-8'))
        file.flush()
        file.close()

        return ("200 OK", [], [])

    def start_display(self, environ):
        print("start display")
        # TODO: accept argument for turning loop mode on
        self.is_displaying = True
        r = bmpReader('/static/current_image.bmp')
        (self.display_width, self.display_height, self.current_display) = r.read_rows()
        gc.collect()        # TODO: if width is different than pixel strip length, return 400

        return ("200 OK", [], [])

    def stop_display(self, environ):
        self.is_displaying = False
        return ("200 OK", [], [])
    
    def process_display(self):
        if self.is_displaying and self.current_display:
            print("start displaying")
            rowSize = (self.display_width * 3)
            print("current_display_size: ", len(self.current_display))
            for row in range(self.display_height):
                pixel_index = 0
                for col in range(self.display_width):
                    idx = (rowSize * row) + (col * 3)
                    pixels[pixel_index] = tuple(self.current_display[idx:idx+3])
                    pixel_index += 1
                pixels.show()
                time.sleep(0.01)
            if (not self.loop):
                self.is_displaying = False
                pixels.fill((0,0,0))
                pixels.show()

# Here we create our application, setting the static directory location
# and registering the above request_handlers for specific HTTP requests
# we want to listen and respond to.
static_dir = "/static"
try:
    static_files = os.listdir(static_dir)
    if "index.html" not in static_files:
        raise RuntimeError("""
            This example depends on an index.html, but it isn't present.
            Please add it to the {0} directory""".format(static_dir))
except (OSError) as e:
    raise RuntimeError("""
        This example depends on a static asset directory.
        Please create one named {0} in the root of the device filesystem.""".format(static_dir))

pixelStick = pixel_painter_application()
web_app = SimpleWSGIApplication(static_dir=static_dir)
web_app.on("GET", "/led_on", pixelStick.led_on)
web_app.on("GET", "/led_off", pixelStick.led_off)
web_app.on("POST", "/ajax/ledcolor", pixelStick.led_color)
web_app.on("POST", "/ajax/loadImage", pixelStick.load_image)
web_app.on("POST", "/ajax/startDisplay", pixelStick.start_display)
web_app.on("POST", "/ajax/stopDisplay", pixelStick.stop_display)

# Here we setup our server, passing in our web_app as the application
server.set_interface(esp)
wsgiServer = server.WSGIServer(80, application=web_app)

print("open this IP in your browser: ", esp.pretty_ip(esp.ip_address))

# Start the server
wsgiServer.start()
while True:
    # Our main loop where we have the server poll for incoming requests
    try:
        wsgiServer.update_poll()
        # Could do any other background tasks here, like reading sensors
    except (ValueError, RuntimeError) as e:
        print("Failed to update server, restarting ESP32\n", e)
        wifi.reset()
        continue
    pixelStick.process_display()
