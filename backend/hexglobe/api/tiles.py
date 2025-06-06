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
            
            # Save the newly created tile
            tile.save()
            logger.info(f"[{datetime.now()}] New tile {tile_id} saved to storage")
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
            
            # Save the newly created tile
            tile.save()
            logger.info(f"[{datetime.now()}] New tile {tile_id} saved to storage")
        
        # Update content if provided
        if "content" in tile_data:
            tile.content = tile_data["content"]
        
        # Update visual properties if provided
        if "visual_properties" in tile_data:
            for key, value in tile_data["visual_properties"].items():
                tile.set_visual_property(key, value)
        
        # Save the updated tile
        tile.save()
        logger.info(f"[{datetime.now()}] Updated tile {tile_id} saved to storage")
        
        return {"message": "Tile updated successfully", "tile": tile.to_dict()}
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error updating tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tile_id}/neighbors")
async def get_neighbors(tile_id: str = Path(..., description="H3 index of the tile")):
    """Get neighboring tiles with their positions."""
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
            
            # Save the newly created tile
            tile.save()
            logger.info(f"[{datetime.now()}] New tile {tile_id} saved to storage")
        
        # Get neighbors with positions
        neighbor_data = {}
        for position, neighbor_id in tile.neighbor_ids.items():
            if neighbor_id == "pentagon":
                # For pentagon placeholders, add special entry
                neighbor_data[position] = {
                    "id": "pentagon",
                    "is_pentagon_placeholder": True
                }
            else:
                # Load or create the neighbor tile
                neighbor_tile = Tile.load(neighbor_id)
                if neighbor_tile is None:
                    if h3.h3_is_pentagon(neighbor_id):
                        neighbor_tile = PentagonTile(neighbor_id)
                    else:
                        neighbor_tile = HexagonTile(neighbor_id)
                    neighbor_tile.save()
                
                # Add neighbor data with position
                neighbor_data[position] = neighbor_tile.to_dict()
        
        logger.info(f"[{datetime.now()}] Found {len(neighbor_data)} neighbors for tile {tile_id}")
        
        return {
            "tile_id": tile_id,
            "neighbors": neighbor_data
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
            
            # Save the newly created tile
            tile.save()
            logger.info(f"[{datetime.now()}] New tile {tile_id} saved to storage")
        
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
            
            # Save the newly created tile
            tile.save()
            logger.info(f"[{datetime.now()}] New tile {tile_id} saved to storage")
        
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
            
            # Save the newly created tile
            source_tile.save()
            logger.info(f"[{datetime.now()}] New source tile {tile_id} saved to storage")
        
        # Load or create the target tile
        target_tile = Tile.load(target_id)
        if target_tile is None:
            logger.info(f"[{datetime.now()}] Target tile {target_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(target_id):
                target_tile = PentagonTile(target_id)
            else:
                target_tile = HexagonTile(target_id)
            
            # Save the newly created tile
            target_tile.save()
            logger.info(f"[{datetime.now()}] New target tile {target_id} saved to storage")
        
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
            
            # Save the newly created tile
            tile.save()
            logger.info(f"[{datetime.now()}] New tile {tile_id} saved to storage")
        
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

@router.get("/{tile_id}/grid")
async def get_tile_grid(
    tile_id: str = Path(..., description="H3 index of the tile"),
    width: int = 5,
    height: int = 5
):
    """
    Get a 2D grid of H3 indexes centered around the specified tile.
    
    Args:
        tile_id: H3 index of the center tile
        width: Number of columns in the grid
        height: Number of rows in the grid
        
    Returns:
        A 2D grid of H3 indexes with the specified dimensions
    """
    logger.info(f"[{datetime.now()}] GET request received for grid centered on tile: {tile_id}, width: {width}, height: {height}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Initialize the grid with None values
        grid = [[None for _ in range(width)] for _ in range(height)]
        
        # Calculate center position in the grid
        center_row = height // 2
        center_col = width // 2
        
        # Define position offsets for neighbors (flat-bottom hexagon)
        position_offsets = {
            "top_left": (0, -1),      # (2,1) relative to center (2,2)
            "top_middle": (1, 0),     # (3,2) relative to center (2,2)
            "top_right": (0, 1),      # (2,3) relative to center (2,2)
            "bottom_left": (-1, -1),  # (1,1) relative to center (2,2)
            "bottom_middle": (-1, 0), # (1,2) relative to center (2,2)
            "bottom_right": (-1, 1)   # (1,3) relative to center (2,2)
        }
        
        # Set to track visited tiles
        visited = set()
        
        # Queue for BFS traversal (tile_id, row, col, distance)
        queue = [(tile_id, center_row, center_col, 0)]
        
        # Place the center tile
        grid[center_row][center_col] = tile_id
        visited.add(tile_id)
        
        # Maximum distance from center to include
        max_distance = max(width, height)
        
        # BFS traversal
        while queue:
            current_id, row, col, distance = queue.pop(0)
            
            # Skip if we're too far from center
            if distance > max_distance:
                continue
            
            # Load the current tile
            current_tile = Tile.load(current_id)
            
            # If tile doesn't exist in storage, create it
            if current_tile is None:
                if h3.h3_is_pentagon(current_id):
                    current_tile = PentagonTile(current_id)
                else:
                    current_tile = HexagonTile(current_id)
                current_tile.save()
            
            # Process each neighbor
            for position, neighbor_id in current_tile.neighbor_ids.items():
                # Skip if this is a pentagon's missing position
                if neighbor_id == "pentagon":
                    continue
                
                # Calculate grid position
                offset_row, offset_col = position_offsets.get(position, (0, 0))
                new_row = row + offset_row
                new_col = col + offset_col
                
                # Check if position is valid and not already filled
                if (0 <= new_row < height and 0 <= new_col < width and 
                    grid[new_row][new_col] is None and 
                    neighbor_id not in visited):
                    
                    # Place neighbor in grid
                    grid[new_row][new_col] = neighbor_id
                    
                    # Mark as visited
                    visited.add(neighbor_id)
                    
                    # Add to queue for further expansion
                    queue.append((neighbor_id, new_row, new_col, distance + 1))
        
        # Fill any remaining empty cells using k-ring
        empty_cells = []
        for row in range(height):
            for col in range(width):
                if grid[row][col] is None:
                    empty_cells.append((row, col))
        
        if empty_cells:
            # Calculate how far to search (k-ring distance)
            k = max(width, height)
            
            # Get all tiles within k distance that haven't been placed yet
            all_tiles = set(h3.k_ring(tile_id, k)) - visited
            
            if all_tiles:
                # For each empty cell, find the closest unplaced tile
                for row, col in empty_cells:
                    if not all_tiles:
                        break
                    
                    # Calculate approximate target coordinates
                    # (This is a fallback when BFS doesn't fill all cells)
                    center_lat, center_lng = h3.h3_to_geo(tile_id)
                    row_offset = (row - center_row) * 0.01  # Approximate offset
                    col_offset = (col - center_col) * 0.01  # Approximate offset
                    target_lat = center_lat - row_offset  # Subtract because rows increase downward
                    target_lng = center_lng + col_offset
                    
                    # Find closest tile
                    closest_tile = min(all_tiles, 
                                      key=lambda t: _calculate_distance(
                                          h3.h3_to_geo(t), 
                                          (target_lat, target_lng)
                                      ))
                    
                    grid[row][col] = closest_tile
                    all_tiles.remove(closest_tile)
        
        # Check for pentagons in the grid
        pentagon_positions = []
        for row in range(height):
            for col in range(width):
                if grid[row][col] and h3.h3_is_pentagon(grid[row][col]):
                    pentagon_positions.append([row, col])
        
        logger.info(f"[{datetime.now()}] Grid created successfully using neighbor-based approach")
        logger.info(f"[{datetime.now()}] Found {len(pentagon_positions)} pentagons in the grid")
        
        return {
            "center_tile_id": tile_id,
            "width": width,
            "height": height,
            "grid": grid,
            "pentagon_positions": pentagon_positions
        }
    
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error creating grid for tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_distance(point1, point2):
    """
    Calculate the squared distance between two points (lat, lng).
    Using squared distance to avoid unnecessary sqrt calculations.
    """
    return (point1[0] - point2[0])**2 + (point1[1] - point2[1])**2

@router.get("/{tile_id}/resolutions")
async def get_resolutions(tile_id: str = Path(..., description="H3 index of the tile")):
    """Get all resolution IDs for a specific tile."""
    logger.info(f"[{datetime.now()}] GET request received for resolutions of tile: {tile_id}")
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
            
            # Save the newly created tile
            tile.save()
            logger.info(f"[{datetime.now()}] New tile {tile_id} saved to storage")
        
        # Return resolution IDs
        logger.info(f"[{datetime.now()}] Returning {len(tile.resolution_ids)} resolution IDs for tile {tile_id}")
        return {
            "tile_id": tile_id,
            "resolution_ids": tile.resolution_ids
        }
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error getting resolutions for tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
