from flask import Flask, jsonify, render_template, request
from downloader import run_downloader, scan_videos

app = Flask(__name__)

CURRENT_STATUS = {
    "videos": [],
    "finished": True
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan")
def scan():
    global CURRENT_STATUS
    videos = scan_videos("YOUR_VIDEO_DIRECTORY", include_existing=True)

    CURRENT_STATUS = {
        "videos": [
            {
                "file": v["file"],
                "code": v["code"],
                "has_sub": v["has_sub"],
                "status": "",
                "log": []
            }
            for v in videos
        ],
        "finished": True
    }

    return jsonify({"videos": CURRENT_STATUS["videos"]})

@app.route("/download", methods=["POST"])
def download():
    global CURRENT_STATUS

    CURRENT_STATUS["finished"] = False

    def run():
        for i, v in enumerate(CURRENT_STATUS["videos"]):
            CURRENT_STATUS["videos"][i]["status"] = "downloading"
            CURRENT_STATUS["videos"][i]["log"].append("Starting download...")

            result = process_single_video(v)

            if result:
                CURRENT_STATUS["videos"][i]["status"] = "success"
                CURRENT_STATUS["videos"][i]["log"].append("Success!")
            else:
                CURRENT_STATUS["videos"][i]["status"] = "failed"
                CURRENT_STATUS["videos"][i]["log"].append("Failed.")

        CURRENT_STATUS["finished"] = True

    threading.Thread(target=run).start()

    return jsonify({"ok": True})

@app.route("/status")
def status():
    return jsonify(CURRENT_STATUS)
