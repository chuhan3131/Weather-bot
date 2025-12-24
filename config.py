import os
from dotenv import load_dotenv

load_dotenv()

# required
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")

# optional
OPENWEATHERMAP_BASE_URL = os.getenv("OPENWEATHERMAP_BASE_URL") or "https://api.openweathermap.org"
THREAD_POOL_WORKERS = int(os.getenv("THREAD_POOL_WORKERS", "4"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "4"))
UPLOAD_TIMEOUT = int(os.getenv("UPLOAD_TIMEOUT", "3"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "600"))

required_vars = ["BOT_TOKEN", "OPENWEATHERMAP_API_KEY", "IMGBB_API_KEY"]
for var in required_vars:
    if not globals()[var]:
        raise ValueError(
            f"Missing required environment variable: {var}"
        )
