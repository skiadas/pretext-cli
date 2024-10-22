import http.server
import re
from urllib.parse import urlparse, parse_qs, urlencode
from hashlib import sha256
import os
import urllib.request


def register_current_directory() -> str:
    directory = os.getcwd()
    query = urlencode({'path': directory})
    url = f"http://localhost:8128/register?{query}"
    print(url)
    urllib.request.urlopen(url)


class MyHandler(http.server.SimpleHTTPRequestHandler):
    knownPaths = dict()
    # knownPaths = {
    #     '8269987a8f90086753fe17609f7cb89cdf86ee1befb699eadef0be4bcec00478':
    #     '/Users/haris/Documents/sd-book'
    # }

    def do_GET(self):
        print(MyHandler.knownPaths)
        if self.path == '/quit':
            print('shutting down...')
            self.server.shutdown()
            return
        if self.path.startswith('/register'):
            return self.handle_register_path()
        return super().do_GET()

    def translate_path(self, path: str) -> str:
        match = re.match(r"^/([^/]+)(/.*)", path)
        [hash, rest] = match.groups()
        print(hash, rest)
        self.directory = MyHandler.knownPaths[hash]
        return super().translate_path(rest)

    def handle_register_path(self):
        qs = urlparse(self.path).query
        directory = parse_qs(qs)["path"][0]
        hash = sha256(directory.encode()).hexdigest()
        MyHandler.knownPaths[hash] = directory
        # A simple return here
        self.send_response(200)  # Set the response code to 200 OK
        self.send_header('Content-type', 'text/html')
        self.end_headers()



class MyWebServer(http.server.ThreadingHTTPServer):

    def __init__(self, port: int):
        super().__init__(('localhost', port), MyHandler)
