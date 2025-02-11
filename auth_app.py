from flask import Flask, request, abort
import socket
import re

app = Flask(__name__)

# Allow local testing and correct Amazon domain
ALLOWED_SUFFIX_PATTERN = r'.*\.?ant\.amazon\.com$'

@app.route('/')
def index():
    remote_addr = request.remote_addr  # Get client IP
    fqdn = socket.getfqdn(remote_addr)  # Resolve to domain

    print(f"Remote Addr: {remote_addr}, Resolved FQDN: {fqdn}")  # Debugging output

    if remote_addr == "127.0.0.1" or re.search(ALLOWED_SUFFIX_PATTERN, fqdn):
        return "Access granted"
    else:
        abort(403, "Access denied")

if __name__ == "__main__":
    app.run(port=5001, debug=True)

