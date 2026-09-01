"""
Ajiputra-Project MovieBox API - Unified Production Entrypoint
Powered & Engineered by Ajiputra-Project
"""
import os
import uvicorn
from api import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    workers = int(os.environ.get("WORKERS", 1))
    uvicorn.run("api:app", host="0.0.0.0", port=port, workers=workers, reload=False)

