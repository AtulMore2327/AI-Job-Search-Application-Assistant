import uvicorn
from app.config import settings
from app.utils.logging import logger

if __name__ == "__main__":
    logger.info(f"Starting {settings.PROJECT_NAME} server on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

