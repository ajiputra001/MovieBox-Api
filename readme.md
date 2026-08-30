# 🎬 Ajiputra-Project MovieBox API (v3.1.0)

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Developer](https://img.shields.io/badge/Developer-Ajiputra--Project-purple?style=for-the-badge)](https://github.com/ajiputra001/MovieBox-Api)
[![Watermark](https://img.shields.io/badge/Watermark-Ajiputra--project-blueviolet?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **Engineered & Powered by Ajiputra-Project.** 🚀 High-performance, anti-detect REST API engine for MovieBox with real-time stream extraction, smart proxying, and Android app integration.

---

## ✨ Features & Intelligence

- **🏷️ Branded & Watermarked**: Native `Ajiputra-project` response headers & metadata watermark.
- **🛡️ Anti-Detection Fingerprinting**: User-Agent pool rotation, random micro-jitter, and dynamic browser fingerprints.
- **⚡ Smart Caching & Eviction**: Automatic TTL caching with LRU memory eviction to prevent memory leaks on cloud platforms.
- **🔁 Automatic Token Rotation**: Guest JWT auto-acquisition and dynamic token refresh on rate-limits.
- **📺 Smart CDN Proxy (`/proxy/stream`)**: Direct streaming proxy supporting plain & obfuscated URLs with fallback to prevent CDN blocks.
- **🔍 Smart Search Engine (`/search/smart`)**: Categorized search results with relevance scores, release years, and stream links.
- **📱 Android App Ready (`/api/app/config`)**: Dedicated configuration endpoint for mobile applications.

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/ajiputra001/MovieBox-Api.git
cd MovieBox-Api
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run API Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

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
| `/api/stream/{subject_id}/best` | `GET` | Auto-extract highest quality stream source. |
| `/proxy/stream` | `GET/HEAD` | Smart streaming proxy for video CDN bypass. |

---

## 👨‍💻 Powered By
Engineered with ❤️ by **Ajiputra-Project**
