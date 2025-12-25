import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import re

# ================= CONFIG =================
COOKIES_FILE = "/root/cookies.txt"   # path confirm kar lena
# ========================================

app = FastAPI(title="YT Audio API", version="1.0")


def clean_url(url: str) -> str:
    # remove tracking params
    if "?" in url:
        url = url.split("?")[0]
    return url


def extract_audio_url(youtube_url: str):
    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIES_FILE,
        "nocheckcertificate": True,
        "skip_download": True,
        "format": "bestaudio/best",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)

        # Sometimes formats directly give URL
        if "url" in info:
            return info["url"]

        # Otherwise pick best audio format
        for f in info.get("formats", []):
            if f.get("acodec") != "none":
                return f.get("url")

    return None


def extract_video_url(youtube_url: str):
    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIES_FILE,
        "nocheckcertificate": True,
        "skip_download": True,
        "format": "bestvideo+bestaudio/best",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)

        if "url" in info:
            return info["url"]

        for f in info.get("formats", []):
            if f.get("vcodec") != "none":
                return f.get("url")

    return None


@app.get("/audio")
async def audio(url: str):
    try:
        url = clean_url(url)
        audio_url = extract_audio_url(url)

        if not audio_url:
            raise HTTPException(status_code=400, detail="Audio stream not found")

        return JSONResponse({"audio_url": audio_url})

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )


@app.get("/video")
async def video(url: str):
    try:
        url = clean_url(url)
        video_url = extract_video_url(url)

        if not video_url:
            raise HTTPException(status_code=400, detail="Video stream not found")

        return JSONResponse({"video_url": video_url})

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )


@app.get("/")
async def root():
    return {
        "status": "online",
        "audio": True,
        "video": True,
        "cookies": True
}
