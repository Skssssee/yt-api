import asyncio
import yt_dlp
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="YT Audio API")

# ------------------------------------
# yt-dlp OPTIONS (AUDIO ONLY)
# ------------------------------------
YTDLP_OPTS = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "nocheckcertificate": True,
    "geo_bypass": True,
    "extractor_args": {
        "youtube": {
            "player_client": ["android"],
        }
    },
    # cookies (optional but recommended)
    "cookiefile": "cookies.txt" if True else None,
}


def extract_audio(url: str):
    with yt_dlp.YoutubeDL(YTDLP_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)

        if "formats" not in info:
            raise Exception("No formats found")

        # pick best audio-only
        for f in info["formats"]:
            if (
                f.get("acodec") != "none"
                and f.get("vcodec") == "none"
                and f.get("url")
            ):
                return f["url"]

        raise Exception("No audio-only stream found")


# ------------------------------------
# API ENDPOINT
# ------------------------------------
@app.get("/audio")
async def audio(url: str = Query(...)):
    try:
        audio_url = await asyncio.to_thread(extract_audio, url)
        return JSONResponse(
            {
                "status": "ok",
                "audio_url": audio_url,
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": str(e),
            },
        )
