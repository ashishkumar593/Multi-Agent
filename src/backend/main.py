"""Backend main entrypoint."""
import uvicorn
from src.backend.api.app import app
from src.backend.core.config import settings

def start() -> None:
    """Launch FastAPI application with uvicorn."""
    uvicorn.run("src.backend.api.app:app", host="0.0.0.0", port=8000, reload=settings.debug)

if __name__ == "__main__":
    start()
