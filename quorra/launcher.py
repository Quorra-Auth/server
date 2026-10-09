import uvicorn
from os import cpu_count
from .config import config

def launch():
    workers = config["server"].get("workers") or cpu_count() or 1
    uvicorn.run("quorra.main:app", host="0.0.0.0", port=8080, access_log=False, workers=workers)
