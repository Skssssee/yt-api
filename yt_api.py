
from fastapi import FastAPI, HTTPException
import yt_dlp
import time
import psutil
import asyncio

app = FastAPI()
START_TIME = time.time()
SEM = asyncio.Semaphore(20)
COOKIE_FILE = "/root/cookies.txt"


@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.get("/stats")
def stats():
    return {
        "status": "online",
        "uptime_sec": int(time.time() - START_TIME),
        "cpu_percent": psutil.cpu_percent(),
        "ram_total_mb": round(psutil.virtual_memory().total / 1024 / 1024),
        "ram_used_mb": round(psutil.virtual_memory().used / 1024 / 1024),
        "ram_free_mb": round(psutil.virtual_memory().available / 1024 / 1024),
        "concurrent_limit": 20,
        "pid": psutil.Process().pid
    }


@app.get("/audio")
async def audio(url: str):
    async with SEM:
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "cookies": COOKIE_FILE
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {"audio_url": info["url"]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/video")
async def video(url: str, quality: int = 720):
    async with SEM:
        ydl_opts = {
            "format": f"bestvideo[height<={quality}]/best",
            "quiet": True,
            "noplaylist": True,
            "cookies": COOKIE_FILE
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # direct stream
                if "url" in info:
                    return {"video_url": info["url"]}

                # fallback
                for f in info.get("formats", []):
                    if f.get("url"):
                        return {"video_url": f["url"]}

                raise Exception("No playable format found")

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
