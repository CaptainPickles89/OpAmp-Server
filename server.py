"""Entry point — delegates to opamp_server package."""
import uvicorn
from opamp_server.config import settings
from opamp_server.main import app  # noqa: F401 — imported for uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "opamp_server.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
