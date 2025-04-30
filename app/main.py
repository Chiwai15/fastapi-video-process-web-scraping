import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import health, trending, video
from app.core.dependencies import container
from app.core.config import get_settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events for the application.
    This replaces the deprecated @app.on_event() decorator.
    """
    # Startup
    logger.info("Starting Video Processing Service")
    
    # Initialize dependency container
    container.init_resources()
    logger.info("Dependency container initialized")
    
    # Create required directories
    media_dir = settings.MEDIA_DIR
    output_dir = settings.OUTPUT_DIR
    fonts_dir = os.path.join(settings.MEDIA_DIR, "fonts")
    
    # Create directories explicitly
    for directory in [media_dir, output_dir, fonts_dir]:
        if directory:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    # Check for font file
    font_path = settings.FONT_PATH
    if not os.path.exists(font_path):
        logger.warning(
            f"Required font file not found: {font_path}\n"
            f"Please download it as described in the README.md"
        )
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Video Processing Service")
    
    # Close Redis cache connection
    cache = await container.redis_cache()
    await cache.close()
    logger.info("Redis cache connection closed")
    
    # Shutdown dependency container to clean up resources
    container.shutdown_resources()
    logger.info("Dependency container resources cleaned up")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Video Processing Service API",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Wire up the dependency container
container.wire(packages=["app.api.routes", "app.core.dependencies"])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(trending.router, prefix=settings.API_PREFIX)
app.include_router(video.router, prefix=settings.API_PREFIX)

# Serve static files (videos)
app.mount("/videos", StaticFiles(directory=settings.OUTPUT_DIR), name="videos")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )