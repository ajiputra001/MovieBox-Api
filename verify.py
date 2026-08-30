import httpx, json

BASE = "https://moviebox-api-e5dk.onrender.com"

ENDPOINTS = [
    "/",
    "/health",
    "/api/app/config",
    "/home",
    "/tv-series",
    "/movies",
    "/animation",
    "/search/smart?q=avengers",
]

print("==================================================")
print("  VERIFYING AJIPUTRA-PROJECT MOVIEBOX API  ")
print("==================================================\n")

for path in ENDPOINTS:
    url = BASE + path
    try:
        r = httpx.get(url, timeout=30)
        data = r.json()
        status = "OK" if r.status_code == 200 else f"ERR {r.status_code}"
        watermark = r.headers.get("x-watermark", "N/A")
        print(f"[{status}] {path} | Watermark: {watermark}")

        if path == "/":
            print(f"  App: {data.get('name')} | Dev: {data.get('developer')} | Watermark: {data.get('watermark')}")
        elif path == "/api/app/config":
            print(f"  App Name: {data.get('app_name')} | Status: {data.get('server_status')}")
        elif "search" in path:
            print(f"  Query: {data.get('query')} | Items found: {len(data.get('items', []))}")
        elif "items" in data:
            print(f"  Total items: {len(data.get('items', []))}")

    except Exception as e:
        print(f"[FAIL] {path} => {e}")

print("\nDone. Ajiputra-Project Verification Completed.")
