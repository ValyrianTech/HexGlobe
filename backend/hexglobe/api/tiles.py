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
        
        # Get the resolution of the center tile
        resolution = h3.h3_get_resolution(tile_id)
        
        # Get the center coordinates
        center_lat, center_lng = h3.h3_to_geo(tile_id)
        logger.info(f"[{datetime.now()}] Center tile coordinates: lat={center_lat}, lng={center_lng}")
        
        # Calculate how far to search (k-ring distance)
        k = max(width, height) // 2 + 1
        logger.info(f"[{datetime.now()}] Using k-ring distance: {k}")
        
        # Get all tiles within k distance
        tiles = list(h3.k_ring(tile_id, k))
        logger.info(f"[{datetime.now()}] Found {len(tiles)} tiles in k-ring")
        
        # Get coordinates for all tiles
        tile_coords = {}
        for t in tiles:
            lat, lng = h3.h3_to_geo(t)
            tile_coords[t] = (lat, lng)
        
        # Sort tiles by latitude (north to south)
        sorted_by_lat = sorted(tiles, key=lambda t: -tile_coords[t][0])  # Negative for north-south order
        
        # Group tiles by latitude bands
        lat_bands = []
        current_band = []
        
        if sorted_by_lat:
            prev_lat = tile_coords[sorted_by_lat[0]][0]
            
            for t in sorted_by_lat:
                current_lat = tile_coords[t][0]
                # If we've moved significantly in latitude, start a new band
                # Using a small threshold to group nearby latitudes
                if abs(current_lat - prev_lat) > 0.0001:  # Threshold may need adjustment
                    if current_band:
                        lat_bands.append(current_band)
                    current_band = [t]
                    prev_lat = current_lat
                else:
                    current_band.append(t)
            
            # Add the last band
            if current_band:
                lat_bands.append(current_band)
        
        # Sort each band by longitude (west to east)
        for i in range(len(lat_bands)):
            lat_bands[i] = sorted(lat_bands[i], key=lambda t: tile_coords[t][1])
        
        # Create a grid with the specified dimensions
        grid = [[None for _ in range(width)] for _ in range(height)]
        
        # Calculate center position in the grid
        center_row = height // 2
        center_col = width // 2
        
        # Place the center tile
        grid[center_row][center_col] = tile_id
        
        # Try to fill the grid with the closest tiles from our sorted bands
        # This is a simplified approach and may need refinement
        rows_filled = 1
        top_row = center_row - 1
        bottom_row = center_row + 1
        
        # Find the center tile's band
        center_band_idx = None
        for i, band in enumerate(lat_bands):
            if tile_id in band:
                center_band_idx = i
                break
        
        if center_band_idx is not None:
            # Fill rows above center
            band_idx = center_band_idx - 1
            while band_idx >= 0 and top_row >= 0:
                if band_idx < len(lat_bands):
                    band = lat_bands[band_idx]
                    # Find center longitude
                    center_lng = tile_coords[tile_id][1]
                    # Sort band by distance from center longitude
                    band_sorted = sorted(band, key=lambda t: abs(tile_coords[t][1] - center_lng))
                    
                    # Fill the row
                    col = center_col
                    left_col = center_col - 1
                    right_col = center_col + 1
                    
                    for t in band_sorted:
                        if col == center_col:  # First tile goes in center
                            grid[top_row][col] = t
                        elif left_col >= 0:  # Then alternate left
                            grid[top_row][left_col] = t
                            left_col -= 1
                        elif right_col < width:  # Then right
                            grid[top_row][right_col] = t
                            right_col += 1
                        else:
                            break  # Row is full
                
                top_row -= 1
                band_idx -= 1
                rows_filled += 1
            
            # Fill rows below center
            band_idx = center_band_idx + 1
            while band_idx < len(lat_bands) and bottom_row < height:
                band = lat_bands[band_idx]
                # Find center longitude
                center_lng = tile_coords[tile_id][1]
                # Sort band by distance from center longitude
                band_sorted = sorted(band, key=lambda t: abs(tile_coords[t][1] - center_lng))
                
                # Fill the row
                col = center_col
                left_col = center_col - 1
                right_col = center_col + 1
                
                for t in band_sorted:
                    if col == center_col:  # First tile goes in center
                        grid[bottom_row][col] = t
                    elif left_col >= 0:  # Then alternate left
                        grid[bottom_row][left_col] = t
                        left_col -= 1
                    elif right_col < width:  # Then right
                        grid[bottom_row][right_col] = t
                        right_col += 1
                    else:
                        break  # Row is full
                
                bottom_row += 1
                band_idx += 1
                rows_filled += 1
        
        # Fill in any remaining empty cells with the closest available tiles
        # This is a simplified approach and may need refinement
        remaining_tiles = set(tiles) - {t for row in grid for t in row if t is not None}
        
        for row in range(height):
            for col in range(width):
                if grid[row][col] is None and remaining_tiles:
                    # Find the closest remaining tile to this position
                    target_lat = center_lat + (center_row - row) * 0.01  # Approximate offset
                    target_lng = center_lng + (col - center_col) * 0.01  # Approximate offset
                    
                    closest_tile = min(remaining_tiles, 
                                      key=lambda t: (tile_coords[t][0] - target_lat)**2 + 
                                                   (tile_coords[t][1] - target_lng)**2)
                    
                    grid[row][col] = closest_tile
                    remaining_tiles.remove(closest_tile)
        
        # Check for pentagons in the grid
        pentagon_positions = []
        for row in range(height):
            for col in range(width):
                if grid[row][col] and h3.h3_is_pentagon(grid[row][col]):
                    pentagon_positions.append([row, col])
        
        logger.info(f"[{datetime.now()}] Grid created successfully with {rows_filled} rows filled")
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
