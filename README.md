# Airwave 

![GitHub stars](https://img.shields.io/github/stars/76696265636f646572/Airwave?style=social)
![GitHub forks](https://img.shields.io/github/forks/76696265636f646572/Airwave?style=social)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688.svg)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org/)

# 🚀 Airwave  
**Self-hosted music for friends — everyone listens in sync.**

Paste a YouTube, SoundCloud, or Mixcloud link and instantly create a **shared live stream**.  
Open the same link on any device — browser or Sonos — and everyone hears the **exact same audio**.

No accounts. No premium APIs. No sync issues.

![Airwave Demo](./app.png)

---

## 🎧 What makes Airwave different?

Most music apps:
- ❌ Everyone plays their own stream  
- ❌ Limited to one platform  

Airwave:
- ✅ **One shared live stream**
- ✅ **Multi-source playback** (YouTube, SoundCloud, Mixcloud)  
- ✅ **Works on browsers + Sonos**  
- ✅ **Self-hosted, no lock-in**  

---

## ⚡ Try it in 30 seconds

```bash
docker run -d -p 8000:8000 ghcr.io/yourname/airwave
```

Open:  
👉 http://localhost:8000  

Paste a link → music starts → share the URL.

---

## 🧠 How it works (simple idea, powerful result)

```text
yt-dlp → ffmpeg → shared MP3 stream → all listeners
```

- One audio pipeline  
- One live stream  
- Unlimited listeners  

---

## 🔥 Core Features

### 🔊 Shared live stream
- One `/stream/live.mp3` endpoint  
- All listeners hear the same audio  
- No duplicate encoding or per-user streams  

### 📋 Collaborative queue
- Add tracks from the UI  
- Reorder with drag-and-drop  
- Shared history  

### ▶️ Multi-source playback
- **YouTube** (videos + playlists)  
- **SoundCloud** (tracks + sets)  
- **Mixcloud** (shows)  

### 🎵 Spotify → playable tracks
- Import Spotify playlists into your library  
- Auto-match tracks across providers  
- Review and pick the best source  

### 🔈 Sonos integration
- Discover speakers on your LAN  
- Group and control playback  
- Stream the same audio as browsers  

### 🎮 Player experience
- Play / pause / skip / repeat  
- Seek when supported  
- Fullscreen “now playing”  
- Media Session support (lock screen controls)  

### 📚 Library & playlists
- Create and manage playlists  
- Import YouTube playlists  
- Merge playlists (with duplicate detection)  
- Pin and reorder  

---

## 🧑‍🤝‍🧑 Perfect for

- Listening with friends remotely  
- Shared music in a house  
- Sonos power users  
- Self-hosted setups  
- Small communities  

---

## 🐳 Docker (recommended)

For full functionality (especially Sonos):

```yaml
network_mode: host
```

Set your public URL:

```env
AIRWAVE_PUBLIC_BASE_URL=http://192.168.1.50:8000
```

---

## ⚙️ Configuration

```env
AIRWAVE_HOST=0.0.0.0
AIRWAVE_PORT=8000
AIRWAVE_PUBLIC_BASE_URL=http://192.168.1.50:8000

AIRWAVE_FFMPEG_PATH=./bin/ffmpeg
AIRWAVE_YT_DLP_PATH=./bin/yt-dlp
AIRWAVE_DENO_PATH=./bin/deno

AIRWAVE_MP3_BITRATE=128k
AIRWAVE_LOG_LEVEL=info
```

---

## 🧱 Tech Stack

- FastAPI  
- Vue 3  
- yt-dlp  
- ffmpeg  
- SQLite  

---

## 🏗 Architecture

- StreamEngine — playback worker  
- SharedMp3Hub — fan-out  
- YtDlpService — providers  
- FfmpegPipeline — transcoding  
- Repository — storage  

---

## 🧪 Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install ".[dev]"

npm install
npm run build

./scripts/run_dev.sh
```

---

## 💬 Why Airwave?

No accounts. No lock-in. No sync issues.  

Just:
paste → play → share



> Airwave turns any link into a shared listening experience.

