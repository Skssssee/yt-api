
import os
import subprocess
import tempfile
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import yt_dlp

app = FastAPI()

# ---------------------------------------------------
# yt-dlp SAFE OPTIONS (AUTO FORMAT)
# ---------------------------------------------------
YTDLP_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "format": "bestaudio/best",
    "geo_bypass": True,
    "nocheckcertificate": True,
}

# Optional cookies (recommended)
COOKIES_PATH = "cookies.txt"
if os.path.exists(COOKIES_PATH):
    YTDLP_OPTS["cookiefile"] = COOKIES_PATH


# ---------------------------------------------------
# Extract audio URL safely
# ---------------------------------------------------
def extract_audio_url(url: str) -> str:
    with yt_dlp.YoutubeDL(YTDLP_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)

        # LIVE or HLS
        if "url" in info:
            return info["url"]

        # NORMAL VIDEO
        for f in info.get("formats", []):
            if f.get("acodec") != "none" and f.get("vcodec") == "none":
                return f["url"]

        raise Exception("No audio stream found")


# ---------------------------------------------------
# /audio endpoint
# ---------------------------------------------------
@app.get("/audio")
async def audio(url: str = Query(...)):
    try:
        audio_url = extract_audio_url(url)
        return {
            "status": "ok",
            "audio_url": audio_url
        }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "detail": str(e)
            }
        )


# ---------------------------------------------------
# /video endpoint (OPTIONAL)
# ---------------------------------------------------
@app.get("/video")
async def video(url: str = Query(...)):
    try:
        opts = YTDLP_OPTS.copy()
        opts["format"] = "best"

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "status": "ok",
                "video_url": info["url"]
            }
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "detail": str(e)
            }
        )
