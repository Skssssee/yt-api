import asyncio
import yt_dlp
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="YT Audio + Video API")

# =========================
# yt-dlp BASE OPTIONS
# =========================
BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "nocheckcertificate": True,
    "geo_bypass": True,
    "cookiefile": "cookies.txt",
    "extractor_args": {
        "youtube": {
            "player_client": ["android"],
        }
    },
}

# =========================
# AUDIO (NO VIDEO)
# =========================
AUDIO_OPTS = {
    **BASE_OPTS,
    "format": "bestaudio[ext=m4a]/bestaudio",
}

# =========================
# VIDEO (VIDEO + AUDIO)
# =========================
VIDEO_OPTS = {
    **BASE_OPTS,
    # progressive mp4 (video+audio together)
    "format": "best[ext=mp4]/best",
}


# =========================
# HELPERS
# =========================
def extract_audio(url: str):
    with yt_dlp.YoutubeDL(AUDIO_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)

        for f in info.get("formats", []):
            if (
                f.get("acodec") != "none"
                and f.get("vcodec") == "none"
                and f.get("url")
            ):
                return f["url"]

        raise Exception("No audio-only format found")


def extract_video(url: str):
    with yt_dlp.YoutubeDL(VIDEO_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)

        for f in info.get("formats", []):
            if (
                f.get("acodec") != "none"
                and f.get("vcodec") != "none"
                and f.get("ext") == "mp4"
                and f.get("url")
            ):
                return f["url"]

        raise Exception("No progressive video found")


# =========================
# API ENDPOINTS
# =========================
@app.get("/audio")
async def audio(url: str = Query(...)):
    try:
        audio_url = await asyncio.to_thread(extract_audio, url)
        return {
            "status": "ok",
            "type": "audio",
            "audio_url": audio_url,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)},
        )


@app.get("/video")
async def video(url: str = Query(...)):
    try:
        video_url = await asyncio.to_thread(extract_video, url)
        return {
            "status": "ok",
            "type": "video",
            "video_url": video_url,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)},
            )
