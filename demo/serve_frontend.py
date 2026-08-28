#!/usr/bin/env python3
"""
JurisBot demo web server: serves the built React frontend (SPA fallback)
and proxies /api/* to the backend, mirroring the production nginx layout.

Usage: python demo/serve_frontend.py [--port 8080]
"""
import argparse
import http.server
import os
import socketserver
import urllib.request

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "jurisconsultor", "frontend", "dist")
BACKEND = "http://127.0.0.1:8000"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.abspath(DIST), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            self.send_error(405)

    def do_PUT(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            self.send_error(405)

    def do_DELETE(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            self.send_error(405)

    def _proxy(self):
        body = None
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            body = self.rfile.read(length)
        req = urllib.request.Request(BACKEND + self.path, data=body, method=self.command)
        for h in ("Content-Type", "Authorization", "X-Tenant-ID"):
            if self.headers.get(h):
                req.add_header(h, self.headers[h])
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(502, f"Proxy error: {e}")

    def send_error(self, code, message=None, explain=None):
        # SPA fallback: unknown paths serve index.html (React Router)
        if code == 404 and not self.path.startswith("/api/"):
            try:
                with open(os.path.join(os.path.abspath(DIST), "index.html"), "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            except OSError:
                pass
        super().send_error(code, message, explain)

    def log_message(self, fmt, *args):
        print(f"[web] {self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--pid-file", default=None, help="Write the process PID to this file")
    args = parser.parse_args()
    if args.pid_file:
        with open(args.pid_file, "w") as f:
            f.write(str(os.getpid()))
    with socketserver.ThreadingTCPServer((args.host, args.port), Handler) as httpd:
        print(f"Serving JurisBot frontend at http://{args.host}:{args.port} (dist={os.path.abspath(DIST)})")
        httpd.serve_forever()
