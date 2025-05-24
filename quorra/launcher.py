import uvicorn
from .main import app

def launch():
    uvicorn.run(app, host="0.0.0.0", port=8080, access_log=False)
