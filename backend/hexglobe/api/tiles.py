from fastapi import APIRouter, HTTPException, Path
from typing import Dict, List, Optional
import h3
import logging
from datetime import datetime

from ..models.tile import Tile, HexagonTile, PentagonTile, VisualProperties

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/tiles",
    tags=["tiles"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{tile_id}")
async def get_tile(tile_id: str = Path(..., description="H3 index of the tile")):
    """Get information about a specific tile."""
    logger.info(f"[{datetime.now()}] GET request received for tile: {tile_id}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Try to load from storage
        tile = Tile.load(tile_id)
        
        # If not found in storage, create a new one
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
        else:
            logger.info(f"[{datetime.now()}] Tile {tile_id} loaded from storage")
        
        return tile.to_dict()
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error processing request for tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{tile_id}")
async def update_tile(
    tile_data: Dict,
    tile_id: str = Path(..., description="H3 index of the tile")
):
    """Update tile information."""
    logger.info(f"[{datetime.now()}] PUT request received to update tile: {tile_id}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id)
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
        
        # Update content if provided
        if "content" in tile_data:
            tile.content = tile_data["content"]
        
        # Update visual properties if provided
        if "visual_properties" in tile_data:
            for key, value in tile_data["visual_properties"].items():
                tile.set_visual_property(key, value)
        
        # Save the updated tile
        tile.save()
        logger.info(f"[{datetime.now()}] Tile {tile_id} updated successfully")
        
        return {"message": "Tile updated successfully", "tile": tile.to_dict()}
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error updating tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tile_id}/neighbors")
async def get_neighbors(tile_id: str = Path(..., description="H3 index of the tile")):
    """Get neighboring tiles."""
    logger.info(f"[{datetime.now()}] GET request received for neighbors of tile: {tile_id}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id)
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
        
        # Get neighbors
        neighbors = tile.get_neighbors()
        logger.info(f"[{datetime.now()}] Found {len(neighbors)} neighbors for tile {tile_id}")
        
        return {
            "tile_id": tile_id,
            "neighbors": [n.to_dict() for n in neighbors]
        }
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error getting neighbors for tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tile_id}/parent")
async def get_parent(tile_id: str = Path(..., description="H3 index of the tile")):
    """Get parent tile."""
    logger.info(f"[{datetime.now()}] GET request received for parent of tile: {tile_id}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id)
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
        
        # Get parent
        parent = tile.get_parent()
        
        if parent is None:
            logger.info(f"[{datetime.now()}] No parent found for tile {tile_id}")
            return {"tile_id": tile_id, "parent": None}
        
        logger.info(f"[{datetime.now()}] Found parent {parent.id} for tile {tile_id}")
        return {
            "tile_id": tile_id,
            "parent": parent.to_dict()
        }
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error getting parent for tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tile_id}/children")
async def get_children(tile_id: str = Path(..., description="H3 index of the tile")):
    """Get child tiles."""
    logger.info(f"[{datetime.now()}] GET request received for children of tile: {tile_id}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id)
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
        
        # Get children
        children = tile.get_children()
        logger.info(f"[{datetime.now()}] Found {len(children)} children for tile {tile_id}")
        
        return {
            "tile_id": tile_id,
            "children": [c.to_dict() for c in children]
        }
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error getting children for tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{tile_id}/move-content/{target_id}")
async def move_content(
    tile_id: str = Path(..., description="Source H3 index"),
    target_id: str = Path(..., description="Target H3 index")
):
    """Move content from one tile to another."""
    logger.info(f"[{datetime.now()}] POST request received to move content from tile {tile_id} to {target_id}")
    try:
        # Validate the H3 indices
        if not h3.h3_is_valid(tile_id) or not h3.h3_is_valid(target_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: source={tile_id}, target={target_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the source tile
        source_tile = Tile.load(tile_id)
        if source_tile is None:
            logger.info(f"[{datetime.now()}] Source tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                source_tile = PentagonTile(tile_id)
            else:
                source_tile = HexagonTile(tile_id)
        
        # Load or create the target tile
        target_tile = Tile.load(target_id)
        if target_tile is None:
            logger.info(f"[{datetime.now()}] Target tile {target_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(target_id):
                target_tile = PentagonTile(target_id)
            else:
                target_tile = HexagonTile(target_id)
        
        # Move content
        success = source_tile.move_content_to(target_tile)
        
        if not success:
            logger.warning(f"[{datetime.now()}] Content could not be moved from {tile_id} to {target_id}")
            raise HTTPException(
                status_code=400,
                detail="Content could not be moved. Tiles may not be neighbors."
            )
        
        logger.info(f"[{datetime.now()}] Content successfully moved from {tile_id} to {target_id}")
        return {
            "message": "Content moved successfully",
            "source_tile": source_tile.to_dict(),
            "target_tile": target_tile.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error moving content from {tile_id} to {target_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{tile_id}/visual")
async def update_visual_properties(
    visual_props: Dict,
    tile_id: str = Path(..., description="H3 index of the tile")
):
    """Update visual properties of a tile."""
    logger.info(f"[{datetime.now()}] PUT request received to update visual properties of tile: {tile_id}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id)
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
        
        # Update visual properties
        updated = False
        for key, value in visual_props.items():
            if tile.set_visual_property(key, value):
                updated = True
        
        if not updated:
            logger.warning(f"[{datetime.now()}] No valid visual properties provided for tile {tile_id}")
            raise HTTPException(
                status_code=400,
                detail="No valid visual properties provided"
            )
        
        # Save the updated tile
        tile.save()
        logger.info(f"[{datetime.now()}] Visual properties updated for tile {tile_id}")
        
        return {
            "message": "Visual properties updated successfully",
            "tile": tile.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error updating visual properties for tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
