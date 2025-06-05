from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .api import tiles

app = FastAPI(
    title="HexGlobe API",
    description="A web application framework that implements a global hexagonal grid system",
    version="0.1.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"],  # Vue.js dev server ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
