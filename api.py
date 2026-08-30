import re
import json
import httpx
import asyncio
import random
import time
import base64
import hashlib
from functools import lru_cache
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from urllib.parse import urlparse, quote, unquote, unquote_plus

app = FastAPI(
    title="Ajiputra-Project MovieBox API",
    description="Engineered & Powered by Ajiputra-Project — Ultra High Performance REST API with Smart Stream Proxy, Anti-Detection & Intelligent Caching",
    version="3.1.1-Ajiputra-FixBearer"
)

@app.middleware("http")
async def add_watermark_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Powered-By"] = "Ajiputra-Project"
    response.headers["X-Developer"] = "Ajiputra-Project"
    response.headers["X-Watermark"] = "Ajiputra-project"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

BASE_URL = "https://moviebox.ph"
API_BASE = "https://h5-api.aoneroom.com/wefeed-h5api-bff"

_shared_client: httpx.AsyncClient | None = None

def _get_shared_client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(25.0, connect=8.0, read=30.0),
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=50,
                keepalive_expiry=120.0,
            ),
        )
    return _shared_client

_bearer_token: str | None = None
_token_acquired_at: float = 0.0
TOKEN_TTL = 900  # 15 menit — rotasi token otomatis

# ==================== ANTI-DETECTION: USER-AGENT POOL ====================

_USER_AGENT_POOL = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    # Mobile
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Mobile/15E148 Safari/604.1",
    # Opera / Brave
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 OPR/114.0.0.0",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/27.0 Chrome/148.0.0.0 Mobile Safari/537.36",
]

_TIMEZONES = [
    "Asia/Jakarta", "Asia/Dhaka", "Asia/Kolkata", "Asia/Bangkok",
    "America/New_York", "America/Chicago", "America/Los_Angeles",
    "Europe/London", "Europe/Berlin", "Europe/Paris", "Asia/Tokyo",
    "Asia/Shanghai", "Asia/Singapore", "Australia/Sydney", "Asia/Dubai",
]

_LANGUAGES = ["en", "id", "bn", "hi", "th", "vi", "tl", "ms"]

_ACCEPT_LANGUAGE_POOL = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.9,id;q=0.8",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "en-US,en;q=0.9,es;q=0.8",
    "en-US,en;q=0.8,fr;q=0.6",
    "en-US,en;q=0.9,bn;q=0.7",
]

_VIEWPORT_WIDTHS = ["1280", "1366", "1440", "1536", "1920", "2560"]
_DEVICE_PIXEL_RATIOS = ["1", "1.25", "1.5", "2", "2.5", "3"]

# ==================== ANTI-DETECTION: FINGERPRINT BUILDER ====================

def _pick_ua() -> str:
    return random.choice(_USER_AGENT_POOL)

def _pick_timezone() -> str:
    return random.choice(_TIMEZONES)

def _pick_lang() -> str:
    return random.choice(_LANGUAGES)

def _pick_accept_lang() -> str:
    return random.choice(_ACCEPT_LANGUAGE_POOL)

def _build_fingerprint_headers(base_headers: dict | None = None) -> dict:
    """Bangun header dengan fingerprint acak setiap request."""
    ua = _pick_ua()
    tz = _pick_timezone()
    lang = _pick_lang()
    accept_lang = _pick_accept_lang()

    chrome_ver = "148"
    m = re.search(r"Chrome/(\d+)", ua)
    if m:
        chrome_ver = m.group(1)

    platform = '"Windows"'
    mobile = "?0"
    if "Macintosh" in ua:
        platform = '"macOS"'
    elif "Linux" in ua or "X11" in ua:
        platform = '"Linux"'
    elif "Android" in ua:
        platform = '"Android"'
        mobile = "?1"
    elif "iPhone" in ua or "iPad" in ua:
        platform = '"iOS"'
        mobile = "?1"

    headers = {
        "User-Agent": ua,
        "Accept": "application/json",
        "Accept-Language": accept_lang,
        "Content-Type": "application/json",
        "X-Client-Info": json.dumps({"timezone": tz}),
        "X-Request-Lang": lang,
        "sec-ch-ua": f'"Chromium";v="{chrome_ver}", "Google Chrome";v="{chrome_ver}", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile": mobile,
        "sec-ch-ua-platform": platform,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "Viewport-Width": random.choice(_VIEWPORT_WIDTHS),
        "DPR": random.choice(_DEVICE_PIXEL_RATIOS),
    }
    if base_headers:
        headers.update(base_headers)
    return headers

def _build_default_headers() -> dict:
    return _build_fingerprint_headers({
        "Referer": "https://moviebox.ph/",
        "Origin": "https://moviebox.ph",
    })

def _build_player_headers() -> dict:
    return _build_fingerprint_headers({
        "Accept": "application/json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "X-Source": "",
        "sec-fetch-site": "same-origin",
    })

def _random_jitter(min_ms: int = 10, max_ms: int = 40) -> float:
    return random.uniform(min_ms, max_ms) / 1000.0

# ==================== TOKEN MANAGEMENT (DENGAN ROTASI) ====================

async def _get_bearer_token(force_refresh: bool = False) -> str:
    """Auto-acquire & rotate guest JWT — multi-source fallback otomatis."""
    global _bearer_token, _token_acquired_at
    now = time.time()
    if not force_refresh and _bearer_token and (now - _token_acquired_at) < 300:
        return _bearer_token
    _bearer_token = None

    token_urls = [
        f"{API_BASE}/home?host=moviebox.ph",
        "https://netfilm.world/wefeed-h5api-bff/home",
        f"{API_BASE}/home",
    ]

    client = _get_shared_client()
    for url in token_urls:
        try:
            headers = _build_default_headers()
            resp = await client.get(url, headers=headers, timeout=10)
            x_user = resp.headers.get("x-user") or resp.headers.get("X-User")
            if x_user:
                try:
                    _bearer_token = json.loads(x_user).get("token")
                except Exception:
                    pass
            if not _bearer_token:
                cookie_lines = resp.headers.get_list("set-cookie") or [resp.headers.get("set-cookie", "")]
                for c in cookie_lines:
                    if c:
                        m = re.search(r"token=([^;]+)", c)
                        if m:
                            _bearer_token = m.group(1)
                            break
            if _bearer_token:
                _token_acquired_at = now
                print(f"[TOKEN] Successfully acquired fresh token from {url}")
                break
        except Exception as e:
            print(f"[TOKEN] Failed getting token from {url}: {e}")

    # Fallback ke valid guest JWT jika jaringan token gagal di cloud/datacenter
    if not _bearer_token:
        _bearer_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjY0NjgxMzMwMzc1NjYwNTk3NzYsImF0cCI6MywiZXh0IjoiMTc4ODAzMTU2OSIsImV4cCI6MTc5NTgwNzU2OSwiaWF0IjoxNzg4MDMxMjY5fQ.JHryJZrdHSEV47_p1Zy36ZAPwoUxr2cTc8FSow-rIGE"
        _token_acquired_at = now

    return _bearer_token

# ==================== URL OBFUSCATION ====================

_OBFUSCATION_KEY = hashlib.sha256(b"moviebox-api-pro-v2").digest()

def _obfuscate_url(original_url: str) -> str:
    """Encode URL stream agar tidak terlihat sumber aslinya."""
    if not original_url:
        return original_url
    encoded = base64.urlsafe_b64encode(original_url.encode()).decode().rstrip("=")
    key_char = _OBFUSCATION_KEY[random.randint(0, len(_OBFUSCATION_KEY) - 1)]
    xored = "".join(chr(ord(c) ^ key_char) for c in encoded)
    return base64.urlsafe_b64encode(xored.encode()).decode().rstrip("=")

def _deobfuscate_url(obfuscated: str) -> str:
    """Decode URL yang di-obfuscate kembali ke asli."""
    if not obfuscated:
        return obfuscated
    try:
        xored = base64.urlsafe_b64decode(obfuscated + "===").decode()
        for k in _OBFUSCATION_KEY:
            try:
                decoded = "".join(chr(ord(c) ^ k) for c in xored)
                result = base64.urlsafe_b64decode(decoded + "===").decode()
                if result.startswith("http"):
                    return result
            except Exception:
                continue
        return obfuscated
    except Exception:
        return obfuscated

# ==================== CACHE LAYER ====================

_cache: dict = {}
DEFAULT_CACHE_TTL = 300  # 5 menit default TTL

def _cache_key(prefix: str, *args) -> str:
    return f"{prefix}:{':'.join(str(a) for a in args)}"

def _cache_get(key: str, ttl: int = DEFAULT_CACHE_TTL) -> dict | None:
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < ttl:
        return entry["data"]
    return None

MAX_CACHE_ENTRIES = 500

def _cache_set(key: str, data: dict):
    now = time.time()
    # Smart eviction jika cache terlalu besar
    if len(_cache) >= MAX_CACHE_ENTRIES:
        expired_keys = [k for k, v in _cache.items() if (now - v["ts"]) > DEFAULT_CACHE_TTL]
        for ek in expired_keys:
            _cache.pop(ek, None)
        # Jika masih melebihi batas, hapus 50 entri tertua
        if len(_cache) >= MAX_CACHE_ENTRIES:
            sorted_keys = sorted(_cache.keys(), key=lambda k: _cache[k]["ts"])
            for old_k in sorted_keys[:50]:
                _cache.pop(old_k, None)
    _cache[key] = {"data": data, "ts": now}

# ==================== SMART REQUEST ENGINE ====================

async def _make_request(
    url: str,
    method: str = "GET",
    payload: dict = None,
    custom_headers: dict = None,
    use_cache: bool = False,
    cache_prefix: str = "req",
    cache_args: tuple = (),
    ttl: int = DEFAULT_CACHE_TTL,
) -> dict:
    """Smart request dengan: persistent connection pool, micro-jitter, retry, cache opsional."""
    global _bearer_token, _token_acquired_at

    # Cache check
    if use_cache:
        ck = _cache_key(cache_prefix, *cache_args)
        cached = _cache_get(ck, ttl=ttl)
        if cached is not None:
            return cached

    token = await _get_bearer_token()
    headers = _build_default_headers()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if custom_headers:
        headers.update(custom_headers)

    # Micro-jitter acak sebelum request
    await asyncio.sleep(_random_jitter(10, 35))

    client = _get_shared_client()
    last_err = None
    for attempt in range(3):
        try:
            if method == "POST":
                resp = await client.post(url, headers=headers, json=payload)
            else:
                resp = await client.get(url, headers=headers)

            # Refresh token if server sends new one
            x_user = resp.headers.get("x-user")
            if x_user:
                try:
                    new_token = json.loads(x_user).get("token")
                    if new_token:
                        _bearer_token = new_token
                        _token_acquired_at = time.time()
                except Exception:
                    pass

            is_token_err = False
            if resp.status_code in (400, 401):
                is_token_err = True
            elif resp.status_code == 200:
                try:
                    body_json = resp.json()
                    if body_json.get("code") in (400, 401, 10001) or "invalid token" in str(body_json.get("message", "")).lower():
                        is_token_err = True
                except Exception:
                    pass

            if is_token_err:
                # Force refresh token dan coba ulang request
                fresh_token = await _get_bearer_token(force_refresh=True)
                if fresh_token:
                    headers["Authorization"] = f"Bearer {fresh_token}"
                    if method == "POST":
                        resp = await client.post(url, headers=headers, json=payload)
                    else:
                        resp = await client.get(url, headers=headers)

            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Upstream API error: {resp.status_code}")

            result = resp.json()

            # Cache if enabled
            if use_cache:
                ck = _cache_key(cache_prefix, *cache_args)
                _cache_set(ck, result)

            return result

        except HTTPException:
            raise
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as e:
            last_err = e
            await asyncio.sleep(0.3 * (attempt + 1) + _random_jitter(50, 200))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")

    raise HTTPException(status_code=502, detail=f"Upstream connection failed after retries: {last_err}")

@app.get("/")
async def root():
    return {
        "name": "Ajiputra-Project MovieBox API",
        "developer": "Ajiputra-Project",
        "watermark": "Ajiputra-project",
        "version": app.version,
        "docs": "/docs",
        "app_config": "/api/app/config",
        "status": "running",
        "features": [
            "anti-detection",
            "fingerprint-rotation",
            "url-obfuscation",
            "smart-cache",
            "auto-retry",
            "stream-proxy",
            "smart-search",
            "batch-episodes"
        ],
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "3.1.2-MultiToken",
        "powered_by": "Ajiputra-Project",
        "watermark": "Ajiputra-project",
        "token_active": bool(_bearer_token),
        "token_age_sec": round(time.time() - _token_acquired_at, 1) if _bearer_token else None,
        "cache_entries": len(_cache),
        "uptime_approx": "running",
    }

@app.get("/api/app/config")
async def get_app_config():
    """Smart config endpoint for Mobile Apps & Android Integrations."""
    return {
        "app_name": "Ajiputra-Project MovieBox API",
        "developer": "Ajiputra-Project",
        "watermark": "Ajiputra-project",
        "version": app.version,
        "server_status": "online",
        "proxy_enabled": True,
        "proxy_endpoint": "/proxy/stream",
        "anti_detection": True,
        "supported_codecs": ["H264", "HEVC", "MP4", "HLS", "DASH"],
        "cache_active": True,
        "powered_by": "Ajiputra-Project"
    }

@app.get("/home")
async def get_home():
    url = f"{API_BASE}/home?host=moviebox.ph"
    data = await _make_request(url, use_cache=True, cache_prefix="home", cache_args=())
    sections = []
    for op in data.get("data", {}).get("operatingList", []) or []:
        op_type = op.get("type")
        title = op.get("title", "Featured")
        if op_type == "BANNER":
            items = [{
                "name": item.get("title") or (item.get("subject") or {}).get("title"),
                "poster_url": item.get("image", {}).get("url") or (item.get("subject") or {}).get("cover", {}).get("url"),
                "slug": item.get("detailPath") or (item.get("subject") or {}).get("detailPath"),
                "subject_id": (item.get("subject") or {}).get("subjectId"),
                "badge": (item.get("subject") or {}).get("corner")
            } for item in op.get("banner", {}).get("items", []) if item.get("title") and "Communities" not in item.get("title")]
            sections.append({"section": "Banner", "count": len(items), "items": items})
        elif op_type in ["SUBJECTS_MOVIE", "SUBJECTS_TV", "SUBJECTS_ANIMATION"]:
            items = [{
                "name": sub.get("title"),
                "poster_url": sub.get("cover", {}).get("url"),
                "slug": sub.get("detailPath"),
                "subject_id": sub.get("subjectId"),
                "badge": sub.get("corner"),
                "rating": sub.get("imdbRatingValue")
            } for sub in op.get("subjects", [])]
            sections.append({"section": title, "count": len(items), "items": items})
    return {"status": "success", "sections": sections}

async def _get_category_data(tab_id: int, page: int = 1, per_page: int = 24, sort: str = "RECOMMEND") -> dict:
    url = f"{API_BASE}/subject/filter"
    payload = {"tabId": tab_id, "filter": {"sort": sort, "genre": "ALL", "country": "ALL", "year": "ALL", "language": "ALL"}, "page": page, "perPage": per_page}
    data = await _make_request(url, method="POST", payload=payload)
    inner = data.get("data", {})
    raw_items = inner.get("items", inner.get("subjects", []))
    items = [{
        "name": sub.get("title"),
        "poster_url": sub.get("cover", {}).get("url"),
        "slug": sub.get("detailPath"),
        "subject_id": sub.get("subjectId"),
        "badge": sub.get("corner"),
        "rating": sub.get("imdbRatingValue"),
        "year": sub.get("releaseDate", "")[:4] if sub.get("releaseDate") else None
    } for sub in raw_items]
    pager = inner.get("pager", {})
    total = pager.get("totalCount") or inner.get("total") or len(items)
    return {"page": page, "per_page": per_page, "total": total, "items": items}

@app.get("/movies")
async def get_movies(page: int = 1, sort: str = "RECOMMEND"):
    return await _get_category_data(tab_id=2, page=page, sort=sort)

@app.get("/tv-series")
async def get_tv_series(page: int = 1, sort: str = "RECOMMEND"):
    return await _get_category_data(tab_id=5, page=page, sort=sort)

@app.get("/animation")
async def get_animation(page: int = 1, sort: str = "RECOMMEND"):
    return await _get_category_data(tab_id=8, page=page, sort=sort)

@app.get("/search/suggest")
async def get_search_suggestions(q: str = Query(..., min_length=1)):
    url = f"{API_BASE}/subject/search-suggest"
    data = await _make_request(url, method="POST", payload={"keyword": q, "perPage": 10})
    inner = data.get("data", {})
    raw = inner.get("items", inner.get("list", []))
    suggestions = []
    for item in raw:
        sub = item.get("subject") or {}
        suggestions.append({
            "title": sub.get("title") or item.get("word") or item.get("title"),
            "slug": sub.get("detailPath") or item.get("detailPath"),
            "subject_id": sub.get("subjectId") or item.get("subjectId")
        })
    return {"suggestions": suggestions}

@app.get("/search")
async def search(q: str = Query(..., min_length=1), page: int = 1):
    clean_q = unquote_plus(q).replace("+", " ").strip()
    url = f"{API_BASE}/subject/search"
    try:
        data = await _make_request(url, method="POST", payload={"keyword": clean_q, "page": page, "perPage": 20})
    except Exception as e:
        print(f"[SEARCH RETRY] Error searching '{clean_q}': {e}. Forcing fresh token...")
        await _get_bearer_token(force_refresh=True)
        try:
            data = await _make_request(url, method="POST", payload={"keyword": clean_q, "page": page, "perPage": 20})
        except Exception:
            data = {}

    inner = data.get("data", {})
    raw = inner.get("items", inner.get("list", []))
    items = [{
        "name": sub.get("title"),
        "poster_url": sub.get("cover", {}).get("url"),
        "slug": sub.get("detailPath"),
        "subject_id": sub.get("subjectId")
    } for sub in raw if sub.get("title")]
    pager = inner.get("pager", {})
    total = pager.get("totalCount") or inner.get("total") or len(items)

    is_fallback = False
    if not items and page == 1:
        try:
            fallback_data = await _get_category_data(tab_id=2, page=1, per_page=12)
            items = fallback_data.get("items", [])
            total = len(items)
            is_fallback = True
        except Exception:
            pass

    return {"query": clean_q, "page": page, "total": total, "items": items, "is_fallback": is_fallback}

@app.get("/search/smart")
async def smart_search(q: str = Query(..., min_length=1), page: int = 1):
    """Smart search engine with auto-categorization & rich metadata."""
    res = await search(q=q, page=page)
    raw_items = res.get("items", [])
    smart_items = []
    for item in raw_items:
        smart_items.append({
            "name": item.get("name"),
            "poster_url": item.get("poster_url"),
            "slug": item.get("slug"),
            "subject_id": item.get("subject_id"),
            "year": item.get("year"),
            "badge": item.get("badge"),
            "rating": item.get("rating"),
            "quick_stream_url": f"/api/stream/{item.get('subject_id')}/best?detail_path={item.get('slug')}" if item.get('subject_id') and item.get('slug') else None
        })
    return {
        "status": "success",
        "developer": "Ajiputra-Project",
        "watermark": "Ajiputra-project",
        "query": res.get("query"),
        "page": res.get("page"),
        "total": res.get("total"),
        "is_fallback": res.get("is_fallback"),
        "items": smart_items
    }

# ==================== QUALITY ENGINE ====================

# Urutan kualitas dari rendah ke tinggi
_QUALITY_RANK = {
    "144": 0, "240": 1, "360": 2, "480": 3,
    "540": 4, "720": 5, "1080": 6, "1440": 7, "2160": 8, "4320": 9,
}

def _parse_resolution(res_str: str) -> int:
    """Ekstrak angka resolusi dari string seperti '720p', '1080', '4K'."""
    if not res_str:
        return 0
    res_str = str(res_str).lower().replace("p", "").strip()
    if res_str == "4k":
        return 2160
    if res_str == "8k":
        return 4320
    if res_str == "2k":
        return 1440
    try:
        return int(res_str)
    except ValueError:
        return 0

def _quality_sort_key(stream: dict) -> int:
    """Key untuk sorting: resolusi tertinggi dulu."""
    res = _parse_resolution(stream.get("resolution", "0"))
    return -res  # negative for descending

async def _parse_hls_master(m3u8_url: str, referer: str = "https://netfilm.world/") -> list[dict]:
    """Fetch & parse HLS master playlist (.m3u8) untuk ekstrak variant streams."""
    try:
        token = await _get_bearer_token()
        headers = {**_build_player_headers(), "Referer": referer}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            resp = await client.get(m3u8_url, headers=headers)
            content = resp.text
    except Exception:
        return []

    variants = []
    current_bandwidth = None
    current_resolution = None
    current_url = None

    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#EXT-X-STREAM-INF"):
            # Parse bandwidth & resolution
            bw_match = re.search(r"BANDWIDTH=(\d+)", line)
            res_match = re.search(r"RESOLUTION=(\d+)x(\d+)", line)
            if bw_match:
                current_bandwidth = int(bw_match.group(1))
            if res_match:
                current_resolution = int(res_match.group(2))  # height = resolution
        elif line and not line.startswith("#") and current_bandwidth:
            # Ini URL variant
            current_url = line
            if not current_url.startswith("http"):
                # Resolve relative URL
                base = m3u8_url.rsplit("/", 1)[0]
                current_url = f"{base}/{current_url}"
            variants.append({
                "resolution": f"{current_resolution or 0}p",
                "resolution_height": current_resolution or 0,
                "bandwidth": current_bandwidth,
                "bandwidth_mbps": round(current_bandwidth / 1_000_000, 2) if current_bandwidth else 0,
                "format": "HLS",
                "url": current_url,
                "url_raw": current_url,
                "codec": "HLS",
            })
            current_bandwidth = None
            current_resolution = None
            current_url = None

    return variants

async def _parse_dash_manifest(mpd_url: str, referer: str = "https://netfilm.world/") -> list[dict]:
    """Fetch & parse DASH MPD manifest untuk ekstrak resolution heights (1080p, 720p, 480p, 360p)."""
    try:
        token = await _get_bearer_token()
        headers = {**_build_player_headers(), "Referer": referer}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            headers["Cookie"] = f"token={token}"
        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            resp = await client.get(mpd_url, headers=headers)
            content = resp.text
    except Exception:
        return []

    variants = []
    # Flexible regex: parse all <Representation ...> tags regardless of attribute order
    rep_tags = re.findall(r'<Representation\b([^>]*)>', content, re.IGNORECASE)
    for tag_attrs in rep_tags:
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', tag_attrs))
        rep_id = attrs.get("id", "")
        bw = attrs.get("bandwidth", "0")
        height = attrs.get("height", "")
        codecs = attrs.get("codecs", "hevc")

        height_val = int(height) if height.isdigit() else 0
        res_label = f"{height_val}p" if height_val > 0 else "1080p"

        variants.append({
            "resolution": res_label,
            "resolution_height": height_val or 1080,
            "bandwidth": int(bw) if bw.isdigit() else 0,
            "bandwidth_mbps": round(int(bw) / 1_000_000, 2) if bw.isdigit() and int(bw) > 0 else 0,
            "format": "DASH",
            "url": mpd_url,
            "url_raw": mpd_url,
            "representation_id": rep_id,
            "codec": codecs,
            "is_hd": (height_val or 1080) >= 720,
            "status": "unlocked_hd" if (height_val or 1080) >= 1080 else "unlocked",
        })

    return variants
@app.get("/detail/{slug}")
async def get_movie_detail(slug: str):
    url = f"{API_BASE}/detail?detailPath={slug}"
    return await _make_request(url)



@app.get("/api/stream/{subject_id}")
async def get_stream_sources(
    subject_id: str,
    detail_path: str,
    se: int = 1,
    ep: int = 1,
    obfuscate: bool = True,
    min_quality: int = 0,
    parse_hls: bool = True,
    parse_dash: bool = True,
):
    """
    Stream endpoint dengan dukungan kualitas penuh.
    - min_quality: filter minimum resolusi (e.g., 720 untuk 720p+)
    - parse_hls: parse HLS master playlist untuk variant streams
    - parse_dash: parse DASH manifest untuk representation
    """
    # Auto-resolve numeric subject_id if slug/string passed
    if not str(subject_id).isdigit():
        detail_res = await get_movie_detail(detail_path or subject_id)
        real_sid = detail_res.get("data", {}).get("subject", {}).get("subjectId")
        if real_sid:
            subject_id = str(real_sid)

    # Step 1: get the player domain
    dom_data = await _make_request(f"{API_BASE}/media-player/get-domain")
    domain = dom_data.get("data", "https://netfilm.world").rstrip("/")

    # Step 2: build the Referer
    player_referer = (
        f"{domain}/spa/videoPlayPage/movies/{detail_path}"
        f"?id={subject_id}&type=/movie/detail&detailSe={se}&detailEp={ep}&lang=en"
    )

    token = await _get_bearer_token()
    player_headers = _build_player_headers()
    if token:
        player_headers["Authorization"] = f"Bearer {token}"
        player_headers["Cookie"] = f"token={token}"

    async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
        # Strategy 1: Direct API_BASE URL (unblocked direct API endpoint)
        play_url = f"{API_BASE}/subject/play?subjectId={subject_id}&se={se}&ep={ep}&detailPath={detail_path}"
        resp = await client.get(play_url, headers={**player_headers, "Referer": player_referer})
        data = resp.json().get("data", {})

        # Auto-retry with force-refreshed token if limited session detected or no streams returned
        if data.get("limited") or (not data.get("streams") and not data.get("hls") and not data.get("dash")):
            fresh_token = await _get_bearer_token(force_refresh=True)
            if fresh_token:
                player_headers["Authorization"] = f"Bearer {fresh_token}"
                player_headers["Cookie"] = f"token={fresh_token}"
                resp = await client.get(play_url, headers={**player_headers, "Referer": player_referer})
                data = resp.json().get("data", {})

        # Strategy 2: Fallback se=0, ep=0 on API_BASE (Movies require se=0, ep=0)
        if not data.get("streams") and not data.get("hls") and not data.get("dash"):
            alt_se = 0 if se != 0 else 1
            alt_ep = 0 if ep != 0 else 1
            alt_play_url = f"{API_BASE}/subject/play?subjectId={subject_id}&se={alt_se}&ep={alt_ep}&detailPath={detail_path}"
            alt_resp = await client.get(alt_play_url, headers={**player_headers, "Referer": player_referer})
            alt_data = alt_resp.json().get("data", {})
            if alt_data.get("streams") or alt_data.get("hls") or alt_data.get("dash"):
                data = alt_data

        # Strategy 3: Fallback player domain URL (netfilm.world)
        if not data.get("streams") and not data.get("hls") and not data.get("dash"):
            dom_play_url = f"{domain}/wefeed-h5api-bff/subject/play?subjectId={subject_id}&se={se}&ep={ep}&detailPath={detail_path}"
            dom_resp = await client.get(dom_play_url, headers={**player_headers, "Referer": player_referer})
            dom_data = dom_resp.json().get("data", {})
            if dom_data.get("streams") or dom_data.get("hls") or dom_data.get("dash"):
                data = dom_data

    has_resource = data.get("hasResource", False)

    # Direct MP4/DASH streams dari API
    raw_streams = data.get("streams", [])
    streams = [
        {
            "resolution": f"{s.get('resolutions')}p",
            "resolution_height": int(s.get("resolutions", 0)) if s.get("resolutions") else 0,
            "format": s.get("format"),
            "url": _obfuscate_url(s.get("url")) if obfuscate and s.get("url") else s.get("url"),
            "url_raw": s.get("url"),
            "size": s.get("size"),
            "size_mb": round(float(s.get("size", 0)) / (1024 * 1024), 2) if s.get("size") else None,
            "duration": s.get("duration"),
            "codec": s.get("codecName"),
        }
        for s in raw_streams
        # Filter: skip streams with empty URL or VIP-locked
        if s.get("url") and not s.get("vipLocked", False)
    ]

    # HLS master playlist parsing
    hls_data = data.get("hls", [])
    hls_variants = []
    if parse_hls and hls_data:
        for hls_item in hls_data:
            hls_url = hls_item.get("url") or hls_item
            if isinstance(hls_url, str) and hls_url.endswith(".m3u8"):
                variants = await _parse_hls_master(hls_url, player_referer)
                for v in variants:
                    v["url"] = _obfuscate_url(v["url"]) if obfuscate else v["url"]
                hls_variants.extend(variants)

    # DASH manifest parsing (unlocking 1080p HD adaptive streams)
    dash_data = data.get("dash", [])
    dash_variants = []
    if parse_dash and dash_data:
        for dash_item in dash_data:
            mpd_url = dash_item.get("url") if isinstance(dash_item, dict) else dash_item
            if isinstance(mpd_url, str):
                variants = await _parse_dash_manifest(mpd_url, player_referer)
                if variants:
                    for v in variants:
                        v["url"] = _obfuscate_url(v["url"]) if obfuscate else v["url"]
                    dash_variants.extend(variants)
                else:
                    # Fallback single 1080p entry if manifest parsing fails
                    res_info = dash_item.get("resolutions", "1080,720,480") if isinstance(dash_item, dict) else "1080,720,480"
                    dash_variants.append({
                        "resolution": "1080p",
                        "resolutions": res_info,
                        "resolution_height": 1080,
                        "format": "DASH",
                        "url": _obfuscate_url(mpd_url) if obfuscate else mpd_url,
                        "url_raw": mpd_url,
                        "codec": dash_item.get("codecName", "hevc") if isinstance(dash_item, dict) else "hevc",
                        "is_hd": True,
                        "status": "unlocked_hd",
                    })

    # Deduplicate DASH variants by resolution height
    seen_dash_res = set()
    unique_dash_variants = []
    for dv in dash_variants:
        res_h = dv.get("resolution_height", 0)
        if res_h not in seen_dash_res:
            seen_dash_res.add(res_h)
            unique_dash_variants.append(dv)

    # Gabungkan semua sources
    all_sources = streams + hls_variants + unique_dash_variants

    # Sort by quality (highest first)
    all_sources.sort(key=_quality_sort_key)

    # Filter by min_quality
    if min_quality > 0:
        all_sources = [s for s in all_sources if _parse_resolution(s.get("resolution", "0")) >= min_quality]

    # Hitung statistik kualitas
    resolutions_found = sorted(set(
        _parse_resolution(s.get("resolution", "0")) for s in all_sources
    ), reverse=True)
    best_quality = resolutions_found[0] if resolutions_found else 0

    return {
        "subject_id": subject_id,
        "se": se,
        "ep": ep,
        "has_resource": has_resource or bool(all_sources),
        "quality_stats": {
            "available_resolutions": [f"{r}p" for r in resolutions_found],
            "best_available": f"{best_quality}p" if best_quality else "unknown",
            "total_sources": len(all_sources),
            "min_quality_filter": f"{min_quality}p" if min_quality else "none",
            "filtered_count": len(all_sources),
            "supports_1080p": 1080 in resolutions_found or best_quality >= 1080,
        },
        "sources": all_sources,
        "hls_raw": hls_data,
        "dash_raw": dash_data,
        "free_episodes": data.get("freeNum"),
        "limited": data.get("limited", False),
        "note": None if (has_resource or all_sources) else "No stream found for this episode."
    }

@app.get("/api/stream/{subject_id}/best")
async def get_best_stream(
    subject_id: str,
    detail_path: str,
    se: int = 1,
    ep: int = 1,
    obfuscate: bool = True,
    min_quality: int = 0,
):
    """Return only the BEST quality stream available."""
    result = await get_stream_sources(
        subject_id=subject_id,
        detail_path=detail_path,
        se=se,
        ep=ep,
        obfuscate=obfuscate,
        min_quality=min_quality,
        parse_hls=True,
        parse_dash=True,
    )
    sources = result.get("sources", [])
    if not sources:
        return {**result, "best": None, "note": "No stream available"}
    return {
        **result,
        "best": sources[0],  # sudah sorted, index 0 = kualitas tertinggi (1080p)
        "sources": None,  # hide all sources, only show best
    }

@app.get("/api/stream/{subject_id}/1080p")
async def get_1080p_stream(
    subject_id: str,
    detail_path: str,
    se: int = 1,
    ep: int = 1,
    obfuscate: bool = True,
):
    """Force & return only the 1080p Full HD stream (or highest available HD stream)."""
    result = await get_stream_sources(
        subject_id=subject_id,
        detail_path=detail_path,
        se=se,
        ep=ep,
        obfuscate=obfuscate,
        min_quality=0,
        parse_hls=True,
        parse_dash=True,
    )
    sources = result.get("sources", [])
    if not sources:
        return {**result, "stream_1080p": None, "note": "No 1080p stream available for this title."}

    # Search for exact 1080p or fallback to highest available stream
    hd_1080p = next((s for s in sources if _parse_resolution(s.get("resolution", "")) == 1080), sources[0])
    return {
        **result,
        "quality": hd_1080p.get("resolution"),
        "stream_1080p": hd_1080p,
        "sources": None,
    }

@app.get("/api/stream/{subject_id}/quality/{target_quality}")
async def get_stream_by_quality(
    subject_id: str,
    detail_path: str,
    target_quality: int,
    se: int = 1,
    ep: int = 1,
    obfuscate: bool = True,
):
    """Retrieve stream matching exact target quality resolution (e.g. 1080, 720, 480, 360)."""
    result = await get_stream_sources(
        subject_id=subject_id,
        detail_path=detail_path,
        se=se,
        ep=ep,
        obfuscate=obfuscate,
        min_quality=0,
        parse_hls=True,
        parse_dash=True,
    )
    sources = result.get("sources", [])
    matched = [s for s in sources if _parse_resolution(s.get("resolution", "")) == target_quality]
    selected = matched[0] if matched else (sources[0] if sources else None)
    return {
        **result,
        "target_quality": f"{target_quality}p",
        "matched": bool(matched),
        "stream": selected,
        "sources": None,
    }

@app.get("/api/stream/{subject_id}/captions")
async def get_captions(subject_id: str, detail_path: str, se: int = 1, ep: int = 1):
    dom_data = await _make_request(f"{API_BASE}/media-player/get-domain")
    domain = dom_data.get("data", "https://netfilm.world").rstrip("/")

    player_referer = (
        f"{domain}/spa/videoPlayPage/movies/{detail_path}"
        f"?id={subject_id}&type=/movie/detail&detailSe={se}&detailEp={ep}&lang=en"
    )

    token = await _get_bearer_token()
    player_headers = _build_player_headers()
    if token:
        player_headers["Authorization"] = f"Bearer {token}"
        player_headers["Cookie"] = f"token={token}"

    play_url = f"{API_BASE}/subject/play?subjectId={subject_id}&se={se}&ep={ep}&detailPath={detail_path}"

    async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
        play_resp = await client.get(play_url, headers={**player_headers, "Referer": player_referer})
        play_data = play_resp.json().get("data", {})
        if not play_data.get("streams") and not play_data.get("dash"):
            alt_se = 0 if se != 0 else 1
            alt_ep = 0 if ep != 0 else 1
            alt_url = f"{API_BASE}/subject/play?subjectId={subject_id}&se={alt_se}&ep={alt_ep}&detailPath={detail_path}"
            alt_resp = await client.get(alt_url, headers={**player_headers, "Referer": player_referer})
            alt_data = alt_resp.json().get("data", {})
            if alt_data.get("streams") or alt_data.get("dash"):
                play_data = alt_data

    streams = play_data.get("streams", [])
    dash = play_data.get("dash", [])

    stream_id = None
    stream_format = None
    if streams:
        stream_id = streams[0].get("id")
        stream_format = streams[0].get("format", "MP4")
    elif dash:
        stream_id = dash[0].get("id")
        stream_format = dash[0].get("format", "DASH")

    if not stream_id:
        return {"subject_id": subject_id, "se": se, "ep": ep, "count": 0, "captions": []}

    cap_url = (
        f"{API_BASE}/subject/caption"
        f"?format={stream_format}&id={stream_id}&subjectId={subject_id}&detailPath={detail_path}"
    )
    data = await _make_request(cap_url)
    inner = data.get("data", {})
    captions = inner.get("captions", []) if isinstance(inner, dict) else inner
    return {"subject_id": subject_id, "se": se, "ep": ep, "count": len(captions), "captions": captions}

# ==================== Streaming Proxy & Web UI ====================

ALLOWED_PROXY_HOSTS = (
    "hakunaymatata.com",
    "aoneroom.com",
    "netfilm.world",
    "moviebox.ph",
    "aoneroom.net",
    "aoneroom.org",
    "aoneroom.info",
    "cloudfront.net",
    "akamaized.net",
    "fastly.net",
)

def _is_host_allowed(host: str) -> bool:
    if not host:
        return False
    host = host.lower()
    if any(host == h or host.endswith("." + h) for h in ALLOWED_PROXY_HOSTS):
        return True
    if any(keyword in host for keyword in ("hakunaymatata", "aoneroom", "netfilm", "moviebox", "sacdn", "bcdn", "playstream")):
        return True
    return False

PROXY_CHUNK_SIZE = 1024 * 1024  # 1 MB

_proxy_client: httpx.AsyncClient | None = None

def _get_proxy_client() -> httpx.AsyncClient:
    global _proxy_client
    if _proxy_client is None or _proxy_client.is_closed:
        _proxy_client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(30.0, connect=10.0, read=60.0, write=60.0, pool=30.0),
            limits=httpx.Limits(
                max_connections=32,
                max_keepalive_connections=16,
                keepalive_expiry=120.0,
            ),
        )
    return _proxy_client

@app.on_event("shutdown")
async def _close_proxy_client():
    global _proxy_client
    if _proxy_client is not None and not _proxy_client.is_closed:
        await _proxy_client.aclose()

@app.api_route("/proxy/stream", methods=["GET", "HEAD"])
async def proxy_stream(url: str, request: Request, obfuscated: bool = False):
    """Proxy video/subtitle CDN — supports plain & obfuscated URLs, DASH manifest rewriting & anti-block header injection."""
    # Fix cut-off query params if request URL query contains unencoded '&'
    raw_query = request.url.query
    if "url=" in raw_query:
        url_part = raw_query.split("url=", 1)[1]
        if "&obfuscated=" in url_part:
            url_part = url_part.split("&obfuscated=")[0]
        from urllib.parse import unquote
        extracted_url = unquote(url_part)
        if extracted_url:
            url = extracted_url

    # Decode jika URL di-obfuscate atau jika tidak diawali http(s)
    if obfuscated or not (url.startswith("http://") or url.startswith("https://")):
        actual_url = _deobfuscate_url(url)
    else:
        actual_url = url

    host = (urlparse(actual_url).hostname or "").lower()
    if not _is_host_allowed(host):
        raise HTTPException(status_code=400, detail="Host not allowed")

    ua = _pick_ua()
    range_header = request.headers.get("range")

    # Gunakan curl via subprocess (httpx diblokir CDN)
    cmd = [
        "curl", "-s", "-D", "-", "--max-time", "60",
        "-H", f"User-Agent: {ua}",
        "-H", "Referer: https://moviebox.ph/",
    ]
    if request.method == "HEAD":
        cmd.insert(1, "-I")
    if range_header:
        cmd += ["-H", f"Range: {range_header}"]
    cmd.append(actual_url)

    # Try subprocess curl first (preferred for anti-CDN blocking)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        header_bytes = bytearray()
        while True:
            chunk = await proc.stdout.read(1)
            if not chunk:
                break
            header_bytes.extend(chunk)
            if header_bytes.endswith(b"\r\n\r\n"):
                break

        header_text = header_bytes.decode("utf-8", errors="replace")
        status_code = 200
        resp_headers = {}
        for line in header_text.split("\r\n"):
            if line.startswith("HTTP/"):
                try:
                    status_code = int(line.split()[1])
                except (IndexError, ValueError):
                    pass
            elif ":" in line:
                key, _, val = line.partition(":")
                resp_headers[key.strip().lower()] = val.strip()

        if status_code < 400 and header_bytes:
            content_type = resp_headers.get("content-type", "").lower()
            is_mpd = ".mpd" in actual_url.lower() or "dash+xml" in content_type or "text/xml" in content_type

            if is_mpd and request.method != "HEAD":
                # Read full MPD XML content and rewrite segment URLs for seamless 1080p video player playback
                full_body = bytearray()
                while True:
                    chunk = await proc.stdout.read(PROXY_CHUNK_SIZE)
                    if not chunk:
                        break
                    full_body.extend(chunk)
                await proc.wait()

                try:
                    xml_text = full_body.decode("utf-8", errors="replace")
                    proxy_base = f"{request.base_url}proxy/stream".rstrip("/")

                    # Pattern for initialization and media segment templates in DASH MPD
                    parts = []
                    last_end = 0
                    pattern = re.compile(r'(initialization|media)=\"([^\"]+)\"', re.IGNORECASE)
                    for m in pattern.finditer(xml_text):
                        parts.append(xml_text[last_end:m.start()])
                        attr_name = m.group(1)
                        raw_seg_url = m.group(2).replace("&amp;", "&")
                        # Quote URL while preserving DASH template parameters ($%...)
                        encoded_seg_url = quote(raw_seg_url, safe="$%")
                        proxied_seg_url = f"{proxy_base}?url={encoded_seg_url}".replace("&", "&amp;")
                        parts.append(f'{attr_name}="{proxied_seg_url}"')
                        last_end = m.end()
                    parts.append(xml_text[last_end:])
                    rewritten_xml = "".join(parts).encode("utf-8")

                    pass_through = {
                        "content-type": "application/dash+xml;charset=UTF-8",
                        "content-length": str(len(rewritten_xml)),
                        "cache-control": "public, max-age=3600",
                        "access-control-allow-origin": "*",
                        "x-stream-mode": "rewritten-dash-1080p",
                    }
                    return StreamingResponse(iter([rewritten_xml]), status_code=status_code, headers=pass_through)
                except Exception as e:
                    print(f"[MPD REWRITE FALLBACK] {e}")

            pass_through = {}
            for key in ("content-type", "content-length", "content-range", "accept-ranges", "etag", "last-modified"):
                if key in resp_headers:
                    pass_through[key] = resp_headers[key]
            pass_through.setdefault("cache-control", "public, max-age=3600")

            async def body_stream():
                try:
                    while True:
                        chunk = await proc.stdout.read(PROXY_CHUNK_SIZE)
                        if not chunk:
                            break
                        yield chunk
                finally:
                    await proc.wait()

            return StreamingResponse(body_stream(), status_code=status_code, headers=pass_through)
    except Exception as e:
        print(f"[PROXY FALLBACK] curl process error: {e}. Falling back to httpx async client...")

    # Smart Fallback: Use httpx AsyncClient
    client = _get_proxy_client()
    req_headers = {"User-Agent": ua, "Referer": "https://moviebox.ph/"}
    if range_header:
        req_headers["Range"] = range_header

    try:
        req = client.build_request("GET" if request.method != "HEAD" else "HEAD", actual_url, headers=req_headers)
        r = await client.send(req, stream=True)
        pass_through = {}
        for key in ("content-type", "content-length", "content-range", "accept-ranges", "etag", "last-modified"):
            if key in r.headers:
                pass_through[key] = r.headers[key]
        pass_through.setdefault("cache-control", "public, max-age=3600")

        return StreamingResponse(r.aiter_bytes(PROXY_CHUNK_SIZE), status_code=r.status_code, headers=pass_through)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Proxy stream failed: {str(e)}")

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000)