import time
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.logging_config import setup_logging
from backend.router import router as api_router
from config.settings import settings
from database.init_db import init_database

# Initialize unified logger
setup_logging()
logger = logging.getLogger("disaster_assist.main")

# Initialize FastAPI App
app = FastAPI(
    title="DisasterAssist AI Backend Gateway",
    description="Multi-agent AI emergency response coordinator backend using Google ADK & Gemini.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

from backend.security import global_rate_limiter

cors_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Rate Limiting Middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Exclude docs and root from rate limits
    if request.url.path in ["/", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)
        
    if global_rate_limiter.is_rate_limited(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests. Please slow down during emergencies."}
        )
    return await call_next(request)

# 3. Performance Tracking Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Measures and logs API response latency."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    
    # Log requests details in production format
    logger.info(
        f"Request: {request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Latency: {process_time:.4f}s"
    )
    return response

# 3. Global Exception Handler Middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catches unhandled errors to prevent raw debug stacktraces leaking."""
    logger.error(f"Unhandled system error: {str(exc)} on path {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Emergency services have been notified.",
            "error_type": exc.__class__.__name__
        }
    )

# 4. Register API Routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.on_event("startup")
async def startup_event():
    """Ensure database tables and seed data exist before serving requests."""
    init_database()
    logger.info("Database startup check completed.")

@app.get("/")
async def root():
    """Welcome index redirection query."""
    return {
        "message": "Welcome to DisasterAssist AI Gateway. Please refer to /docs for API documentation.",
        "status": "active"
    }

if __name__ == "__main__":
    import uvicorn
    # Start ASGI server on standard host and port
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
