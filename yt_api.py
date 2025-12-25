
# yt_api.py
# Fully fixed for PyTgCalls (NO m3u8, direct audio only)

import yt_dlp
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="YT Audio API")

YDL_OPTS = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "nocheckcertificate": True,
    "skip_download": True,
    "extract_flat": False,
    "forceurl": True,
    "noplaylist": True,
}

@app.get("/")
async def root():
    return {"status": "ok", "message": "YT Audio API running"}

@app.get("/audio")
async def audio(url: str = Query(..., description="YouTube video url")):
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)

            # 🔒 safety checks
            if not info:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "detail": "Failed to extract info"},
                )

            audio_url = info.get("url")

            # ❌ reject m3u8
            if not audio_url or ".m3u8" in audio_url:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "detail": "HLS playlist detected, audio not supported",
                    },
                )

            return {
                "status": "success",
                "audio_url": audio_url,
                "title": info.get("title"),
                "duration": info.get("duration"),
            }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)},
        )
