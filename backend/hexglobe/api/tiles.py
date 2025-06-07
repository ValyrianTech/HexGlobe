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
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new tile")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            # Save the newly created tile
            tile.save()
            logger.info(f"[{datetime.now()}] New tile {tile_id} saved to storage")
            
            # Create all tiles within a distance of 5 to ensure grid is populated
            logger.info(f"[{datetime.now()}] Creating neighbor tiles within distance 5 of {tile_id}")
            neighbor_tiles = h3.k_ring(tile_id, 5)
            created_count = 0
            
            for neighbor_id in neighbor_tiles:
                if neighbor_id == tile_id:
                    continue  # Skip the center tile
                    
                # Check if neighbor already exists
                if Tile.load(neighbor_id) is None:
                    # Create and save the neighbor tile
                    if h3.h3_is_pentagon(neighbor_id):
                        neighbor_tile = PentagonTile(neighbor_id)
                    else:
                        neighbor_tile = HexagonTile(neighbor_id)
                    neighbor_tile.save()
                    created_count += 1
            
            logger.info(f"[{datetime.now()}] Created {created_count} new neighbor tiles for {tile_id}")
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
    logger.info(f"GET request received for grid centered on tile: {tile_id}, width: {width}, height: {height}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Define grid bounds for center-based coordinates
        min_row = -height // 2
        max_row = height // 2 + (1 if height % 2 == 1 else 0)
        min_col = -width // 2
        max_col = width // 2 + (1 if width % 2 == 1 else 0)
        
        # Use a dictionary-based grid for center-based coordinates
        grid_dict = {}
        
        # Center position is (0, 0) in the new coordinate system
        center_row, center_col = 0, 0
        
        # Define the standard mapping from neighbor positions to relative grid coordinates
        # This is the core of our topological approach
        position_to_relative_coords = {
            "bottom_middle": (-1, 0),
            "bottom_left": (-1, -1),
            "top_left": (0, -1),
            "top_middle": (1, 0),
            "top_right": (0, 1),
            "bottom_right": (-1, 1)
        }
        
        # Place the center tile
        grid_dict[(center_row, center_col)] = tile_id
        
        # Load or create the center tile
        center_tile = Tile.load(tile_id)
        if center_tile is None:
            if h3.h3_is_pentagon(tile_id):
                center_tile = PentagonTile(tile_id)
            else:
                center_tile = HexagonTile(tile_id)
            center_tile.save()
        
        # Track which tiles have been placed and their positions
        position_map = {tile_id: (center_row, center_col)}
        
        # Track which tiles we've visited (processed all neighbors)
        visited = set()
        
        # Queue for BFS traversal - store (tile_id, row, col) tuples
        queue = [(tile_id, center_row, center_col)]
        
        # BFS to fill the grid
        while queue:
            current_id, current_row, current_col = queue.pop(0)
            
            # Skip if we've already processed this tile
            if current_id in visited:
                continue
                
            # Mark as visited
            visited.add(current_id)
            
            # Load the current tile
            current_tile = Tile.load(current_id)
            if current_tile is None:
                # This shouldn't happen if the tile was properly created
                logger.warning(f"Could not load tile {current_id}")
                continue
            
            # Process each neighbor
            for position, neighbor_id in current_tile.neighbor_ids.items():
                # Skip pentagon placeholders
                if neighbor_id == "pentagon":
                    continue
                
                # Calculate the neighbor's position based on the relative coordinates
                if position in position_to_relative_coords:
                    row_offset, col_offset = position_to_relative_coords[position]
                    neighbor_row = current_row + row_offset
                    neighbor_col = current_col + col_offset
                    
                    # Check if the position is within grid bounds
                    if min_row <= neighbor_row <= max_row and min_col <= neighbor_col <= max_col:
                        # Check if this position is already filled
                        if (neighbor_row, neighbor_col) in grid_dict:
                            # If filled with a different tile, we have a conflict
                            if grid_dict[(neighbor_row, neighbor_col)] != neighbor_id:
                                logger.warning(f"Grid position conflict at ({neighbor_row}, {neighbor_col}): "
                                              f"Existing={grid_dict[(neighbor_row, neighbor_col)]}, New={neighbor_id}")
                                # Keep the existing placement (first one wins)
                        else:
                            # Place the neighbor in the grid
                            grid_dict[(neighbor_row, neighbor_col)] = neighbor_id
                            position_map[neighbor_id] = (neighbor_row, neighbor_col)
                            
                            # Add to queue for further processing if not already visited or in queue
                            # Include the position information in the queue
                            if neighbor_id not in visited:
                                queue.append((neighbor_id, neighbor_row, neighbor_col))
        
        # Check for any empty cells that need to be filled
        empty_cells = []
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                if (row, col) not in grid_dict:
                    empty_cells.append((row, col))
        
        # If we have empty cells, try to fill them by expanding from neighbors
        if empty_cells:
            # Keep trying to fill empty cells until no more progress is made
            progress = True
            while progress and empty_cells:
                progress = False
                remaining_empty = []
                
                for row, col in empty_cells:
                    # Check all adjacent cells (including diagonals)
                    filled = False
                    for r_offset in [-1, 0, 1]:
                        for c_offset in [-1, 0, 1]:
                            if r_offset == 0 and c_offset == 0:
                                continue  # Skip the cell itself
                                
                            adj_row, adj_col = row + r_offset, col + c_offset
                            
                            # Check if adjacent cell is within bounds and has a tile
                            if ((min_row <= adj_row <= max_row and min_col <= adj_col <= max_col) and 
                                (adj_row, adj_col) in grid_dict):
                                
                                # Load the adjacent tile
                                adj_tile_id = grid_dict[(adj_row, adj_col)]
                                adj_tile = Tile.load(adj_tile_id)
                                
                                if adj_tile is not None:
                                    # Check if any of its neighbors can fill our empty cell
                                    for pos, n_id in adj_tile.neighbor_ids.items():
                                        if n_id != "pentagon" and n_id not in position_map:
                                            # Found an unplaced neighbor, use it
                                            grid_dict[(row, col)] = n_id
                                            position_map[n_id] = (row, col)
                                            filled = True
                                            progress = True
                                            break
                                            
                                if filled:
                                    break
                        if filled:
                            break
                            
                    if not filled:
                        remaining_empty.append((row, col))
                        
                empty_cells = remaining_empty
        
        # Convert dictionary-based grid to 2D array for API response
        final_grid = [[None for _ in range(width)] for _ in range(height)]
        pentagon_positions = []
        
        # Map from center-based to array-based coordinates
        for (row, col), tile_id in grid_dict.items():
            # Transform coordinates: (0,0) center-based -> (height//2, width//2) array-based
            array_row = row + height // 2
            array_col = col + width // 2
            
            if 0 <= array_row < height and 0 <= array_col < width:
                final_grid[array_row][array_col] = tile_id
                
                # Check for pentagons
                if h3.h3_is_pentagon(tile_id):
                    pentagon_positions.append([array_row, array_col])
        
        logger.info(f"Grid created successfully using topological approach")
        logger.info(f"Found {len(pentagon_positions)} pentagons in the grid")
        
        # Count filled and empty cells for logging
        filled_count = sum(1 for row in final_grid for cell in row if cell is not None)
        empty_count = width * height - filled_count
        logger.info(f"Grid stats: {filled_count} filled cells, {empty_count} empty cells")
        
        return {
            "center_tile_id": tile_id,
            "width": width,
            "height": height,
            "grid": final_grid,
            "pentagon_positions": pentagon_positions
        }
    
    except Exception as e:
        logger.error(f"Error creating grid for tile {tile_id}: {str(e)}")
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

def _calculate_distance(point1, point2):
    """
    Calculate the squared distance between two points (lat, lng).
    Using squared distance to avoid unnecessary sqrt calculations.
    """
    return (point1[0] - point2[0])**2 + (point1[1] - point2[1])**2
