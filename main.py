"""
Ajiputra-Project MovieBox API - Unified Production Entrypoint
Powered & Engineered by Ajiputra-Project
"""
import os
import uvicorn
from api import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
