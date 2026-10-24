import hashlib
import os
import time

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(status="ok", service="costpilot-demo")


@app.get("/health")
def health():
    return "ok", 200


@app.get("/work")
def work():
    """CPU use karne wala endpoint, load test isi ko hit karega."""
    rounds = int(os.environ.get("WORK_ROUNDS", "20000"))
    data = b"costpilot"
    start = time.time()
    for _ in range(rounds):
        data = hashlib.sha256(data).digest()
    return jsonify(took_ms=round((time.time() - start) * 1000, 2))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
