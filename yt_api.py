import yt_dlp
from fastapi import FastAPI, HTTPException

app = FastAPI()

YDL_OPTS = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "nocheckcertificate": True,
    "skip_download": True,
}

@app.get("/audio")
def audio(url: str):
    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)

            # 🔥 DIRECT AUDIO URL (NOT HLS)
            audio_url = info["url"]

            return {
                "audio_url": audio_url,
                "title": info.get("title"),
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
