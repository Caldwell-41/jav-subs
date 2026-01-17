from flask import Flask, render_template, request, redirect, url_for
import os
from downloader import run_downloader

LOG_FILE = "jav_subtitle_downloader.log"

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    root_dir = os.environ.get("VIDEO_ROOT_DIR", "/videos")
    multithread = True
    max_threads = 10

    logs = ""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            logs = f.read()

    return render_template(
        "index.html",
        root_dir=root_dir,
        multithread=multithread,
        max_threads=max_threads,
        logs=logs
    )

@app.route("/start", methods=["POST"])
def start():
    root_dir = request.form.get("root_dir")
    multithread = request.form.get("multithread") == "on"
    max_threads = int(request.form.get("max_threads") or 10)

    run_downloader(root_dir, use_multithreading=multithread, max_threads=max_threads)

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=16969)
