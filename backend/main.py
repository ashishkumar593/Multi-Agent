"""Backend main entrypoint."""
import uvicorn
from backend.api.app import app
from backend.core.config import settings

def start() -> None:
    """Launch FastAPI application with uvicorn."""
    uvicorn.run("backend.api.app:app", host="0.0.0.0", port=8000, reload=settings.debug)

if __name__ == "__main__":
    start()
