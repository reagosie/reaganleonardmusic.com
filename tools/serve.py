"""
serve.py — local preview server for site/

Mimics the .htaccess rules so the site behaves locally exactly as it will on
Hostinger: extensionless URLs (/pricing -> pricing.html), root-absolute asset
paths, and 404.html for unknown paths.

    py tools/serve.py                       # http://localhost:8080/  (site/)
    py tools/serve.py 9000                  # custom port
    py tools/serve.py --root site-v2 8081   # preview version 2.0
"""
import http.server, os, sys, mimetypes

_args = sys.argv[1:]
_root = "site"
if "--root" in _args:
    _i = _args.index("--root"); _root = _args[_i + 1]; del _args[_i:_i + 2]
ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), _root)
PORT = int(_args[0]) if _args else 8080

mimetypes.add_type("image/avif", ".avif")
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("font/woff2", ".woff2")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def translate_path(self, path):
        path = path.split("?", 1)[0].split("#", 1)[0]
        if path in ("", "/"):
            return os.path.join(ROOT, "index.html")
        full = super().translate_path(path)
        # /pricing -> pricing.html (only when there is no slash or extension)
        if not os.path.exists(full) and "/" not in path.strip("/") and "." not in path:
            candidate = full + ".html"
            if os.path.isfile(candidate):
                return candidate
        return full

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            page = os.path.join(ROOT, "404.html")
            if os.path.isfile(page):
                body = open(page, "rb").read()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        super().send_error(code, message, explain)

    def log_message(self, fmt, *args):
        pass  # quiet


if __name__ == "__main__":
    import socket
    print(f"Serving {ROOT} at http://localhost:{PORT}/  (Ctrl+C to stop)")
    try:   # the address a phone on the same Wi-Fi can use
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); probe.connect(("8.8.8.8", 80))
        print(f"  on this network: http://{probe.getsockname()[0]}:{PORT}/   (allow it if Windows Firewall asks)")
        probe.close()
    except OSError:
        pass
    http.server.ThreadingHTTPServer(("", PORT), Handler).serve_forever()
