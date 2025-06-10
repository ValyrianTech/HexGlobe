from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Optional
import h3
import logging
import requests
from datetime import datetime
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/geocode",
    tags=["geocode"],
    responses={404: {"description": "Not found"}},
)

# Simple in-memory cache for geocoding results
# Structure: {"address": {"lat": lat, "lng": lng, "timestamp": timestamp}}
geocode_cache = {}
CACHE_EXPIRY = 86400  # 24 hours in seconds

@router.get("/")
async def geocode_address(
    address: Optional[str] = Query(None, description="Address to geocode"),
    lat: Optional[float] = Query(None, description="Latitude coordinate"),
    lng: Optional[float] = Query(None, description="Longitude coordinate"),
    resolution: int = Query(9, description="H3 resolution level")
):
    """
    Convert an address or coordinates to an H3 index.
    
    This endpoint accepts either:
    - An address string that will be geocoded to coordinates
    - Direct latitude and longitude coordinates
    
    It returns the corresponding H3 index at the specified resolution.
    """
    logger.info(f"[{datetime.now()}] Geocode request received")
    
    try:
        # Input validation
        if address is None and (lat is None or lng is None):
            raise HTTPException(
                status_code=400, 
                detail="Either 'address' or both 'lat' and 'lng' must be provided"
            )
        
        # If resolution is out of bounds, use default
        if resolution < 0 or resolution > 15:
            logger.warning(f"[{datetime.now()}] Invalid resolution: {resolution}, using default (9)")
            resolution = 9
        
        # Case 1: Coordinates provided directly
        if lat is not None and lng is not None:
            logger.info(f"[{datetime.now()}] Converting coordinates ({lat}, {lng}) to H3 index")
            h3_index = h3.geo_to_h3(lat, lng, resolution)
            return {
                "h3_index": h3_index,
                "coordinates": {"lat": lat, "lng": lng},
                "resolution": resolution
            }
        
        # Case 2: Address provided, needs geocoding
        # Check cache first
        current_time = time.time()
        if address in geocode_cache:
            cache_entry = geocode_cache[address]
            if current_time - cache_entry["timestamp"] < CACHE_EXPIRY:
                logger.info(f"[{datetime.now()}] Cache hit for address: {address}")
                lat, lng = cache_entry["lat"], cache_entry["lng"]
                h3_index = h3.geo_to_h3(lat, lng, resolution)
                return {
                    "h3_index": h3_index,
                    "coordinates": {"lat": lat, "lng": lng},
                    "address": address,
                    "resolution": resolution,
                    "source": "cache"
                }
        
        # Not in cache or expired, query Nominatim
        logger.info(f"[{datetime.now()}] Geocoding address: {address}")
        
        # Call Nominatim API with appropriate headers
        headers = {
            "User-Agent": "HexGlobe/0.1.0"  # Nominatim requires a user agent
        }
        
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            headers=headers,
            params=params
        )
        
        # Check if request was successful
        if response.status_code != 200:
            logger.error(f"[{datetime.now()}] Nominatim API error: {response.status_code}")
            raise HTTPException(
                status_code=502,
                detail=f"Geocoding service error: {response.status_code}"
            )
        
        # Parse response
        results = response.json()
        if not results:
            logger.warning(f"[{datetime.now()}] No results found for address: {address}")
            raise HTTPException(
                status_code=404,
                detail=f"No location found for address: {address}"
            )
        
        # Extract coordinates
        location = results[0]
        lat = float(location["lat"])
        lng = float(location["lon"])
        display_name = location.get("display_name", address)
        
        # Update cache
        geocode_cache[address] = {
            "lat": lat,
            "lng": lng,
            "timestamp": current_time
        }
        
        # Convert to H3 index
        h3_index = h3.geo_to_h3(lat, lng, resolution)
        
        logger.info(f"[{datetime.now()}] Successfully geocoded address to H3 index: {h3_index}")
        
        return {
            "h3_index": h3_index,
            "coordinates": {"lat": lat, "lng": lng},
            "address": display_name,
            "resolution": resolution,
            "source": "nominatim"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error processing geocode request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
