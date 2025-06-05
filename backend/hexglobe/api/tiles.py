from fastapi import APIRouter, HTTPException, Path
from typing import Dict, List, Optional
import h3

from ..models.tile import Tile, HexagonTile, PentagonTile, VisualProperties

router = APIRouter(
    prefix="/api/tiles",
    tags=["tiles"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{tile_id}")
async def get_tile(tile_id: str = Path(..., description="H3 index of the tile")):
    """Get information about a specific tile."""
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Try to load from storage
        tile = Tile.load(tile_id)
        
        # If not found in storage, create a new one
        if tile is None:
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
        
        return tile.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{tile_id}")
async def update_tile(
    tile_data: Dict,
    tile_id: str = Path(..., description="H3 index of the tile")
):
    """Update tile information."""
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id)
        if tile is None:
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
        
        return {"message": "Tile updated successfully", "tile": tile.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tile_id}/neighbors")
async def get_neighbors(tile_id: str = Path(..., description="H3 index of the tile")):
    """Get neighboring tiles."""
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id)
        if tile is None:
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
        
        # Get neighbors
        neighbors = tile.get_neighbors()
        
        return {
            "tile_id": tile_id,
            "neighbors": [n.to_dict() for n in neighbors]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tile_id}/parent")
async def get_parent(tile_id: str = Path(..., description="H3 index of the tile")):
    """Get parent tile."""
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id)
        if tile is None:
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
        
        # Get parent
        parent = tile.get_parent()
        
        if parent is None:
            return {"tile_id": tile_id, "parent": None}
        
        return {
            "tile_id": tile_id,
            "parent": parent.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tile_id}/children")
async def get_children(tile_id: str = Path(..., description="H3 index of the tile")):
    """Get child tiles."""
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id)
        if tile is None:
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
        
        # Get children
        children = tile.get_children()
        
        return {
            "tile_id": tile_id,
            "children": [c.to_dict() for c in children]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{tile_id}/move-content/{target_id}")
async def move_content(
    tile_id: str = Path(..., description="Source H3 index"),
    target_id: str = Path(..., description="Target H3 index")
):
    """Move content from one tile to another."""
    try:
        # Validate the H3 indices
        if not h3.h3_is_valid(tile_id) or not h3.h3_is_valid(target_id):
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the source tile
        source_tile = Tile.load(tile_id)
        if source_tile is None:
            if h3.h3_is_pentagon(tile_id):
                source_tile = PentagonTile(tile_id)
            else:
                source_tile = HexagonTile(tile_id)
        
        # Load or create the target tile
        target_tile = Tile.load(target_id)
        if target_tile is None:
            if h3.h3_is_pentagon(target_id):
                target_tile = PentagonTile(target_id)
            else:
                target_tile = HexagonTile(target_id)
        
        # Move content
        success = source_tile.move_content_to(target_tile)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Content could not be moved. Tiles may not be neighbors."
            )
        
        return {
            "message": "Content moved successfully",
            "source_tile": source_tile.to_dict(),
            "target_tile": target_tile.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{tile_id}/visual")
async def update_visual_properties(
    visual_props: Dict,
    tile_id: str = Path(..., description="H3 index of the tile")
):
    """Update visual properties of a tile."""
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id)
        if tile is None:
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
        
        # Update visual properties
        for key, value in visual_props.items():
            success = tile.set_visual_property(key, value)
            if not success:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid visual property: {key}"
                )
        
        # Save the updated tile
        tile.save()
        
        return {
            "message": "Visual properties updated successfully",
            "tile": tile.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
