from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

from .api import tiles

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HexGlobe API",
    description="A web application framework that implements a global hexagonal grid system",
    version="0.1.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001", "http://localhost:8080"],  # Add port 8080 for Python's http.server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    path = request.url.path
    method = request.method
    
    logger.info(f"[{start_time}] {method} request received: {path}")
    
    response = await call_next(request)
    
    process_time = datetime.now() - start_time
    logger.info(f"[{datetime.now()}] {method} request completed: {path} - Status: {response.status_code} - Time: {process_time.total_seconds():.4f}s")
    
    return response

# Include routers
app.include_router(tiles.router)

@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {"message": "Welcome to HexGlobe API"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
