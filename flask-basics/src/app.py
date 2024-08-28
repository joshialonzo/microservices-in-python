from flask import Flask
from flask import jsonify
from flask import render_template

import socket


app = Flask(__name__)


def fetch_details():
    """
    Function to fetch the hostname and IP address of the host
    """
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)
    return host_name, host_ip


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/health")
def health():
    return jsonify(
        status="UP",
    )


@app.route("/details")
def details():
    hostname, ip = fetch_details()
    return render_template("index.html", hostname=hostname, ip=ip)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
