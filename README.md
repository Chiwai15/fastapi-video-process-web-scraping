# Video Processing & Web Scrapping Service

A modern Python service for video generation and web scraping with caching built on FastAPI.

## Features

- **Video Generation**
  - Create videos with customizable text overlay
  - Generate videos with animated text moving from top-left to bottom-right
  - Parallel video processing using ProcessPoolExecutor
  - Font handling with fallback support

- **Web Scraping**
  - Scrape and cache trending science news
  - Redis-based caching with configurable TTL

- **Architecture**
  - Async/await throughout the codebase
  - Redis for fast caching
  - Process pool for CPU-intensive operations
  - Dependency injection with container
  - Comprehensive error handling

## System Architecture

This service follows clean architecture principles with dependency injection:

```
app/
├── api/            # API endpoints and routes
│   ├── dependencies.py      # Dependency injection setup
│   └── routes/             # Route modules for endpoints
│       ├── health.py       # Health check endpoints
│       ├── trending.py     # News scraping endpoints
│       └── video.py        # Video generation endpoints
├── core/           # Core functionality and configuration
│   ├── config.py           # Application settings
│   ├── decorators.py       # Error and timing decorators
│   ├── exceptions.py       # Error handling
│   └── moviepy_config.py   # Video processing config
├── services/       # Business logic services
│   ├── cache/              # Caching implementation
│   │   └── redis_cache.py  # Redis-based cache
│   ├── scraper/            # Web scraping logic
│   │   └── science_news_scraper.py  # Science news scraper
│   └── video/              # Video processing
│       └── video_processor.py  # Video generation service
└── main.py         # Application entry point
```

### Parallelization Strategy

- Uses `ProcessPoolExecutor` for CPU-bound video processing
- Worker count optimized for CPU tasks
- Tasks run in isolated processes to avoid GIL limitations

## Setup

### Prerequisites

- Docker and Docker Compose
- Make (optional, for convenience commands)

### Font Setup

The service requires specific font files for video text rendering:

1. The service automatically checks for required fonts at startup
2. Default fonts are configured in the Dockerfile
3. Custom fonts can be added to the `/app/media/fonts/` directory

### Running the Service

1. Clone the repository
2. Start the service:

```bash
make up
```

This will:
- Build the Docker images
- Start the application and Redis containers
- Make the API available at http://localhost:8000

### API Documentation

Once the service is running, view the API documentation at:

- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## API Endpoints

### Video Generation

- `POST /api/v1/generate-video`: Create a video with custom text and parameters
  ```json
  {
    "text": "Your text overlay here",
    "duration": 5.0,
    "text_position_x": 50,
    "text_position_y": 150,
    "text_start": 1.0,
    "text_end": 5.0,
    "font_size": 30,
    "text_color": "white"
  }
  ```

- `POST /api/v1/animate-text-video`: Create a video with text animating from top-left to bottom-right
  ```json
  {
    "text": "Your animated text here",
    "duration": 5.0,
    "font_size": 30,
    "text_color": "white"
  }
  ```

- `GET /api/v1/videos/{filename}`: Retrieve a generated video

### Web Scraping

- `GET /api/v1/trending-news`: Get trending news from Science News Magazine (cached for 10 minutes)
  - Optional query param: `refresh=true` to force fresh data

### Health Check

- `GET /api/v1/health`: Service health check with Redis status

## Docker Environment

The service is containerized with Docker:

- Python 3.11 base image
- Redis for caching
- Proper setup for MoviePy and ImageMagick
- Volume mounting for persistent storage

### Environment Variables

Customize the service with these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_HOST` | Redis server host | `redis` |
| `REDIS_PORT` | Redis server port | `6379` |
| `MAX_WORKERS` | Process pool size | CPU count |
| `CACHE_TTL` | Cache TTL in seconds | `600` |

## Development

### Project Structure

The project follows a modular structure with clear separation of concerns:

- **API Layer**: FastAPI routes and endpoints
- **Service Layer**: Business logic components
- **Core**: Configuration, error handling, and shared utilities
- **Dependencies**: Centralized dependency injection

### Key Design Patterns

1. **Decorator-Based Error Handling**
   - Centralized error transformation
   - Consistent error response format
   - Automatic logging

2. **Async Throughout**
   - Async Redis client
   - Async web scraping
   - Async API endpoints

3. **Resource Management**
   - Proper initialization and cleanup
   - Graceful shutdown handling

4. **Performance Monitoring**
   - Timing decorators for key operations
   - Detailed logging

### Available Commands

- `make build`: Build Docker images
- `make up`: Start services
- `make down`: Stop services
- `make logs`: View service logs
- `make clean`: Clean up containers and media
- `make test`: Run tests
- `make shell`: Open a shell in the app container
- `make help`: Show available commands

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT

## Future Improvements

- User authentication and API keys
- Additional video templates and effects
- Thumbnail generation for videos
- Queue system for long-running video tasks
- Metrics dashboard for system performance