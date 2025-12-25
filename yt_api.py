import asyncio
import json
import time
import os

from fastapi import FastAPI, HTTPException
import yt_dlp
import redis
import psutil

# ================= CONFIG =================

COOKIE_FILE = "/root/cookies.txt"     # VPS ONLY
MAX_CONCURRENT = 20                   # 4GB RAM safe
AUDIO_CACHE_TTL = 3600                # 1 hour
VIDEO_CACHE_TTL = 1800                # 30 min

START_TIME = time.time()

# =========================================

app = FastAPI()

# Redis
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Concurrency control
sem = asyncio.Semaphore(MAX_CONCURRENT)

BASE_OPTS = {
    "quiet": True,
    "cookiefile": COOKIE_FILE,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "socket_timeout": 10,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

# ================= UTIL =================

def extract_info(url, opts):
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)

# ================= ROUTES =================

@app.get("/ping")
async def ping():
    return {
        "status": "online",
        "audio": True,
        "video": True,
        "concurrent_limit": MAX_CONCURRENT,
        "uptime_sec": int(time.time() - START_TIME)
    }

@app.get("/stats")
async def stats():
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.5)

    return {
        "status": "online",
        "uptime_sec": int(time.time() - START_TIME),
        "cpu_percent": cpu,
        "ram_total_mb": int(mem.total / 1024 / 1024),
        "ram_used_mb": int(mem.used / 1024 / 1024),
        "ram_free_mb": int(mem.available / 1024 / 1024),
        "concurrent_limit": MAX_CONCURRENT,
        "pid": os.getpid()
    }

# ---------------- AUDIO ----------------

@app.get("/audio")
async def audio(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL missing")

    key = f"AUDIO:{url}"
    cached = r.get(key)
    if cached:
        data = json.loads(cached)
        data["cached"] = True
        return data

    async with sem:
        try:
            opts = BASE_OPTS | {"format": "bestaudio/best"}
            info = extract_info(url, opts)

            data = {
                "type": "audio",
                "title": info.get("title"),
                "duration": info.get("duration"),
                "audio_url": info.get("url"),
                "cached": False
            }

            r.setex(key, AUDIO_CACHE_TTL, json.dumps(data))
            return data

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# ---------------- VIDEO ----------------

@app.get("/video")
async def video(url: str, quality: str = "720"):
    if not url:
        raise HTTPException(status_code=400, detail="URL missing")

    key = f"VIDEO:{url}:{quality}"
    cached = r.get(key)
    if cached:
        data = json.loads(cached)
        data["cached"] = True
        return data

    async with sem:
        try:
            if quality == "1080":
                fmt = "bestvideo[height<=1080]+bestaudio/best"
            elif quality == "480":
                fmt = "bestvideo[height<=480]+bestaudio/best"
            else:
                fmt = "bestvideo[height<=720]+bestaudio/best"

            opts = BASE_OPTS | {
                "format": fmt,
                "merge_output_format": "mp4"
            }

            info = extract_info(url, opts)

            video_url = None
            for f in info.get("formats", []):
                if f.get("vcodec") != "none" and f.get("acodec") != "none":
                    video_url = f.get("url")
                    break

            if not video_url:
                raise Exception("No video stream found")

            data = {
                "type": "video",
                "title": info.get("title"),
                "duration": info.get("duration"),
                "quality": quality,
                "video_url": video_url,
                "cached": False
            }

            r.setex(key, VIDEO_CACHE_TTL, json.dumps(data))
            return data

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
