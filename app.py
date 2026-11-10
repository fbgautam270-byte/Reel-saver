import os, re, uuid, shutil, tempfile, threading, time
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, abort
import yt_dlp

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
DOWNLOAD_DIR = Path(os.environ.get("DOWNLOAD_DIR", "/tmp/reelsaver-downloads"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
INSTAGRAM_RE = re.compile(r"^https?://(www\.)?instagram\.com/(reel|reels|p|tv)/[A-Za-z0-9_-]+/?(?:\?.*)?$", re.I)

def cleanup_old_files():
    cutoff = time.time() - 60 * 30
    for p in DOWNLOAD_DIR.iterdir():
        try:
            if p.is_file() and p.stat().st_mtime < cutoff:
                p.unlink(missing_ok=True)
        except OSError:
            pass

@app.get("/")
def home():
    return app.send_static_file("index.html")

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "ReelSaver"})

@app.post("/api/fetch")
def fetch_media():
    cleanup_old_files()
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    kind = (data.get("type") or "video").lower()
    if kind not in {"video", "audio", "photo"}:
        return jsonify({"error": "Unsupported download type."}), 400
    if not INSTAGRAM_RE.match(url):
        return jsonify({"error": "Enter a valid public Instagram reel or post URL."}), 400

    job = uuid.uuid4().hex
    outtmpl = str(DOWNLOAD_DIR / f"{job}.%(ext)s")
    opts = {
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "socket_timeout": 20,
        "retries": 1,
        "extractor_retries": 1,
        "max_filesize": 150 * 1024 * 1024,
    }
    if kind == "audio":
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        })
    elif kind == "photo":
        # Instagram's extractor exposes the post thumbnail; photo posts may not expose
        # the original image as a downloadable format on every account/post.
        opts.update({"skip_download": True, "writethumbnail": True})
    else:
        opts.update({"format": "best[ext=mp4]/best", "merge_output_format": "mp4"})

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=(kind != "photo"))
            title = info.get("title") or "Instagram download"
            thumbnail = info.get("thumbnail") or ""
        matches = list(DOWNLOAD_DIR.glob(job + ".*"))
        if not matches:
            return jsonify({"error": "No downloadable media was returned. The post may be private or restricted."}), 404
        chosen = max(matches, key=lambda p: p.stat().st_size)
        ext = chosen.suffix.lstrip(".").lower() or ("mp3" if kind == "audio" else "mp4")
        if kind == "photo" and ext not in {"jpg", "jpeg", "png", "webp"}:
            return jsonify({"error": "A downloadable photo was not available for this post."}), 404
        return jsonify({
            "title": title,
            "thumbnail": thumbnail,
            "medias": [{
                "url": f"/downloads/{chosen.name}",
                "label": "Download " + ("MP3" if kind == "audio" else "Photo" if kind == "photo" else "Video"),
                "ext": ext
            }]
        })
    except Exception:
        for p in DOWNLOAD_DIR.glob(job + ".*"):
            p.unlink(missing_ok=True)
        return jsonify({"error": "Instagram could not provide this media. Check that the post is public and try again later."}), 502

@app.get("/downloads/<path:filename>")
def download_file(filename):
    if not re.fullmatch(r"[a-f0-9]{32}\.[A-Za-z0-9]{1,8}", filename):
        abort(404)
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True, download_name="reelsaver." + filename.rsplit(".", 1)[-1])

@app.get("/<path:page>")
def pages(page):
    if page in {"privacy-policy", "terms", "dmca", "contact"}:
        return app.send_static_file(page + ".html")
    abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
