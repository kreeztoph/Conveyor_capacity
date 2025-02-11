from flask import Flask, request, abort
import socket
import re

app = Flask(__name__)

ALLOWED_SUFFIX_PATTERN = r'^ant\.amazon\.com$'

@app.route('/')
def index():
    dns_suffix = socket.getfqdn(request.remote_addr)
    if re.match(ALLOWED_SUFFIX_PATTERN, dns_suffix):
        print(dns_suffix)
        return "Access granted"
    else:
        print(dns_suffix)
        abort(403, "Access denied")
