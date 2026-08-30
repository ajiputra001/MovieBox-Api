# 🎬 Ajiputra-Project MovieBox API (v3.1.2-MultiToken)

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Developer](https://img.shields.io/badge/Developer-Ajiputra--Project-purple?style=for-the-badge)](https://github.com/ajiputra001/MovieBox-Api)
[![Watermark](https://img.shields.io/badge/Watermark-Ajiputra--project-blueviolet?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **Engineered & Powered by Ajiputra-Project.** 🚀 High-performance, anti-detect REST API engine for MovieBox with real-time 1080p Full HD stream extraction, smart DASH manifest rewriting, CDN proxying, and Android app integration.

---

## ✨ Key Features & Enhancements

- **🏷️ Branded & Watermarked**: Native `Ajiputra-project` response headers & metadata watermark.
- **🎬 1080p Full HD Stream Engine**: Unlocks 1080p HD streams with automatic DASH MPD manifest URL rewriting for seamless video player playback.
- **🛡️ Anti-Detection Fingerprinting**: User-Agent pool rotation, random micro-jitter, and dynamic browser fingerprints.
- **⚡ Smart Caching & Eviction**: Automatic TTL caching with LRU memory eviction to prevent memory leaks on cloud platforms.
- **🔁 Automatic Token Rotation**: Guest JWT auto-acquisition and dynamic multi-source token fallback.
- **📺 Smart CDN Proxy (`/proxy/stream`)**: Direct streaming proxy supporting plain & obfuscated URLs with fallback to prevent CDN blocks.
- **🔍 Smart Search Engine (`/search/smart`)**: Categorized search results with relevance scores, release years, and stream links.
- **📱 Android App Ready (`/api/app/config`)**: Dedicated configuration endpoint for mobile applications.

---

## 🚀 One-Command Automatic Linux Server Setup

Instantly setup and run dependencies automatically on any Linux Server (Ubuntu, Debian, CentOS, Arch, VPS):

```bash
git clone https://github.com/ajiputra001/MovieBox-Api.git
cd MovieBox-Api
chmod +x setup.sh && ./setup.sh
```

After running `setup.sh`, start the API server anytime with:
```bash
./start.sh
```

---

## 🐳 Docker Deployment (Optional)

Deploy with a single command using Docker / Docker Compose:

```bash
docker compose up -d
```

---

## ☁️ Cloud Hosting Deployment (Render / Railway / Koyeb)

1. **Render**:
   - Build Command: `./setup.sh` or `pip install -r requirements.txt`
   - Start Command: `python main.py` or `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Railway / Koyeb**:
   - Automatically detects `Procfile` or `Dockerfile`.

---

## 📡 Key Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | API Root info & Ajiputra-project watermark. |
| `/health` | `GET` | Server status, token age, and cache metrics. |
| `/api/app/config` | `GET` | Smart Android App configuration endpoint. |
| `/home` | `GET` | Complete homepage sections & banners. |
| `/movies` | `GET` | Movie filter catalog. |
| `/tv-series` | `GET` | TV series catalog. |
| `/animation` | `GET` | Anime & animation catalog. |
| `/search/smart` | `GET` | Smart search engine with rich metadata. |
| `/api/stream/{subject_id}/1080p` | `GET` | Direct 1080p Full HD stream extractor. |
| `/api/stream/{subject_id}/best` | `GET` | Auto-extract highest quality stream source. |
| `/proxy/stream` | `GET/HEAD` | Smart streaming proxy with DASH manifest segment rewriting. |

---

## 👨‍💻 Powered By
Engineered with ❤️ by **Ajiputra-Project**
