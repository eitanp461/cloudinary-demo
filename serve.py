#!/usr/bin/env python3
"""A static file server that honours Range requests, for previewing this demo.

`python3 -m http.server` is enough for the image pages, but it ignores the Range
header and answers every request with the whole file and a 200. Browsers need
`206 Partial Content` to seek in a video and to fetch it in chunks, so on
/video-before/ the stock server makes the scrub bar useless and can leave the
player waiting on a 43 MB response it never asked for in full.

    python3 serve.py [port]        # default 8000

Standard library only, no dependencies, no build step.
"""

import os
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")
CHUNK = 64 * 1024


class QuietThreadingHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer that does not shout about normal disconnects.

    A media element opens several range requests, keeps what it needs and drops
    the rest, so the client resetting a connection is routine here rather than a
    fault. Left alone, socketserver prints a full traceback for every one of
    them (ConnectionResetError from readline() waiting for the next keep-alive
    request, BrokenPipeError from a response body abandoned mid-write) and the
    console fills with noise while the page is working perfectly.

    Only those disconnect errors are swallowed; anything else still reports.
    """

    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


class RangeRequestHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler plus single-range support for GET."""

    protocol_version = "HTTP/1.1"

    def send_head(self):
        header = self.headers.get("Range")
        if header is None:
            return super().send_head()

        match = RANGE_RE.match(header.strip())
        if match is None or not (match.group(1) or match.group(2)):
            # Multi-range and malformed values fall back to the whole file,
            # which is a legal response to any Range request.
            return super().send_head()

        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()

        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        try:
            size = os.fstat(f.fileno()).st_size
            first, last = match.group(1), match.group(2)
            if first:
                start = int(first)
                end = min(int(last), size - 1) if last else size - 1
            else:
                # A suffix range: "bytes=-500" means the final 500 bytes.
                start = max(size - int(last), 0)
                end = size - 1

            if start >= size or start > end:
                self.send_response(416, "Requested Range Not Satisfiable")
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                f.close()
                return None

            self.send_response(206, "Partial Content")
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(end - start + 1))
            # Accept-Ranges is added for every response in end_headers().
            self.send_header("Last-Modified", self.date_time_string(int(os.fstat(f.fileno()).st_mtime)))
            self.end_headers()
            f.seek(start)
            return _Slice(f, end - start + 1)
        except Exception:
            f.close()
            raise

    def end_headers(self):
        # Advertise range support even on the full-file responses.
        #
        # Note there is deliberately no `Cache-Control: no-store` here. It
        # sounds like the honest choice for a measurement demo, but a media
        # element that may not cache re-requests ranges it has already played,
        # which inflated a 43 MB video to 70 MB of transfer in testing. Tick
        # *Disable cache* in DevTools to measure a cold load instead — that
        # bypasses the cache for the navigation without lying to the player.
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()


class _Slice:
    """A read-only view of `length` bytes from the file's current position.

    copyfile() reads until EOF, so a range response needs a wrapper that stops
    at the end of the range rather than the end of the file.
    """

    def __init__(self, f, length):
        self._f = f
        self._left = length

    def read(self, amount=-1):
        if self._left <= 0:
            return b""
        if amount is None or amount < 0:
            amount = min(self._left, CHUNK)
        data = self._f.read(min(amount, self._left))
        self._left -= len(data)
        return data

    def close(self):
        self._f.close()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    root = os.path.dirname(os.path.abspath(__file__))
    handler = partial(RangeRequestHandler, directory=root)
    with QuietThreadingHTTPServer(("", port), handler) as httpd:
        print(f"Serving {root} on http://localhost:{port}/  (Ctrl-C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()


if __name__ == "__main__":
    main()
