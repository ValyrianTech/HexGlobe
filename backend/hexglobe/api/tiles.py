from fastapi import APIRouter, HTTPException, Path, Query
from typing import Dict, List, Optional
import h3
import logging
from datetime import datetime
import os
import math

from ..models.tile import Tile, HexagonTile, PentagonTile, VisualProperties, get_latest_hex_map_path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/tiles",
    tags=["tiles"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{tile_id}")
async def get_tile(
    tile_id: str = Path(..., description="H3 index of the tile"),
    mod_name: str = Query("default", description="Name of the mod/application")
):
    """Get information about a specific tile."""
    logger.info(f"[{datetime.now()}] GET request received for tile: {tile_id}, mod: {mod_name}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Try to load from storage
        tile = Tile.load(tile_id, mod_name)
        
        # If not found in storage, create a new one
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new tile")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            # Save only the static data for the newly created tile
            tile.save_static()
            logger.info(f"[{datetime.now()}] New tile {tile_id} static data saved to storage")
            
            # Create all tiles within a distance of 5 to ensure grid is populated
            logger.info(f"[{datetime.now()}] Creating neighbor tiles within distance 5 of {tile_id}")
            neighbor_tiles = h3.k_ring(tile_id, 5)
            created_count = 0
            
            for neighbor_id in neighbor_tiles:
                if neighbor_id == tile_id:
                    continue  # Skip the center tile
                    
                # Check if neighbor already exists
                if Tile.load(neighbor_id, mod_name) is None:
                    # Create and save the neighbor tile (static data only)
                    if h3.h3_is_pentagon(neighbor_id):
                        neighbor_tile = PentagonTile(neighbor_id)
                    else:
                        neighbor_tile = HexagonTile(neighbor_id)
                    neighbor_tile.save_static()
                    created_count += 1
            
            logger.info(f"[{datetime.now()}] Created {created_count} new neighbor tiles for {tile_id}")
        else:
            logger.info(f"[{datetime.now()}] Tile {tile_id} loaded from storage")
        
        # Get the tile data
        tile_data = tile.to_dict()
        
        # Get the latest map image path
        latest_map_path = get_latest_hex_map_path(tile_id)
        if latest_map_path:
            # Convert to relative path for frontend use
            relative_path = os.path.relpath(latest_map_path, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            tile_data["latest_map"] = relative_path
        
        return tile_data
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error processing request for tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{tile_id}")
async def update_tile(
    tile_data: Dict,
    tile_id: str = Path(..., description="H3 index of the tile"),
    mod_name: str = Query("default", description="Name of the mod/application")
):
    """Update tile information."""
    logger.info(f"[{datetime.now()}] PUT request received to update tile: {tile_id}, mod: {mod_name}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id, mod_name)
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            # Save the static data for the newly created tile
            tile.save_static()
            logger.info(f"[{datetime.now()}] New tile {tile_id} static data saved to storage")
        
        # Update content if provided
        if "content" in tile_data:
            tile.content = tile_data["content"]
        
        # Update visual properties if provided
        if "visual_properties" in tile_data:
            visual_props = tile_data["visual_properties"]
            for prop_name, prop_value in visual_props.items():
                tile.set_visual_property(prop_name, prop_value)
        
        # Save the dynamic data since we've updated content or visual properties
        tile.save_dynamic(mod_name)
        logger.info(f"[{datetime.now()}] Updated tile {tile_id} dynamic data saved for mod {mod_name}")
        
        return {"message": "Tile updated successfully", "tile": tile.to_dict()}
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error updating tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tile_id}/neighbors")
async def get_neighbors(
    tile_id: str = Path(..., description="H3 index of the tile"),
    mod_name: str = Query("default", description="Name of the mod/application")
):
    """Get neighboring tiles with their positions."""
    logger.info(f"[{datetime.now()}] GET request received for neighbors of tile: {tile_id}, mod: {mod_name}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id, mod_name)
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            # Save the static data for the newly created tile
            tile.save_static()
            logger.info(f"[{datetime.now()}] New tile {tile_id} static data saved to storage")
        
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
                neighbor_tile = Tile.load(neighbor_id, mod_name)
                if neighbor_tile is None:
                    if h3.h3_is_pentagon(neighbor_id):
                        neighbor_tile = PentagonTile(neighbor_id)
                    else:
                        neighbor_tile = HexagonTile(neighbor_id)
                    neighbor_tile.save_static()
                
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
async def get_parent(
    tile_id: str = Path(..., description="H3 index of the tile"),
    mod_name: str = Query("default", description="Name of the mod/application")
):
    """Get parent tile."""
    logger.info(f"[{datetime.now()}] GET request received for parent of tile: {tile_id}, mod: {mod_name}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id, mod_name)
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            # Save the static data for the newly created tile
            tile.save_static()
            logger.info(f"[{datetime.now()}] New tile {tile_id} static data saved to storage")
        
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
async def get_children(
    tile_id: str = Path(..., description="H3 index of the tile"),
    mod_name: str = Query("default", description="Name of the mod/application")
):
    """Get child tiles."""
    logger.info(f"[{datetime.now()}] GET request received for children of tile: {tile_id}, mod: {mod_name}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id, mod_name)
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            # Save the static data for the newly created tile
            tile.save_static()
            logger.info(f"[{datetime.now()}] New tile {tile_id} static data saved to storage")
        
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
    target_id: str = Path(..., description="Target H3 index"),
    mod_name: str = Query("default", description="Name of the mod/application")
):
    """Move content from one tile to another."""
    logger.info(f"[{datetime.now()}] POST request received to move content from tile {tile_id} to {target_id}, mod: {mod_name}")
    try:
        # Validate the H3 indices
        if not h3.h3_is_valid(tile_id) or not h3.h3_is_valid(target_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: source={tile_id}, target={target_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the source tile
        source_tile = Tile.load(tile_id, mod_name)
        if source_tile is None:
            logger.info(f"[{datetime.now()}] Source tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                source_tile = PentagonTile(tile_id)
            else:
                source_tile = HexagonTile(tile_id)
            
            # Save the static data for the newly created tile
            source_tile.save_static()
            logger.info(f"[{datetime.now()}] New source tile {tile_id} static data saved to storage")
        
        # Load or create the target tile
        target_tile = Tile.load(target_id, mod_name)
        if target_tile is None:
            logger.info(f"[{datetime.now()}] Target tile {target_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(target_id):
                target_tile = PentagonTile(target_id)
            else:
                target_tile = HexagonTile(target_id)
            
            # Save the static data for the newly created tile
            target_tile.save_static()
            logger.info(f"[{datetime.now()}] New target tile {target_id} static data saved to storage")
        
        # Move content
        success = source_tile.move_content_to(target_tile)
        
        if not success:
            logger.warning(f"[{datetime.now()}] Content could not be moved from {tile_id} to {target_id}")
            raise HTTPException(
                status_code=400,
                detail="Content could not be moved. There may be an issue with the target tile."
            )
        
        logger.info(f"[{datetime.now()}] Content successfully moved from {tile_id} to {target_id}")
        return {
            "message": "Content moved successfully",
            "source_tile": {
                "id": source_tile.id,
                "content": source_tile.content
            },
            "target_tile": {
                "id": target_tile.id,
                "content": target_tile.content
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error moving content from {tile_id} to {target_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{tile_id}/visual")
async def update_visual_properties(
    visual_props: Dict,
    tile_id: str = Path(..., description="H3 index of the tile"),
    mod_name: str = Query("default", description="Name of the mod/application")
):
    """Update visual properties of a tile."""
    logger.info(f"[{datetime.now()}] PUT request received to update visual properties of tile: {tile_id}, mod: {mod_name}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id, mod_name)
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            # Save the static data for the newly created tile
            tile.save_static()
            logger.info(f"[{datetime.now()}] New tile {tile_id} static data saved to storage")
        
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
        
        # Save the dynamic data since we've updated visual properties
        tile.save_dynamic(mod_name)
        logger.info(f"[{datetime.now()}] Visual properties updated for tile {tile_id} and saved for mod {mod_name}")
        
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
    height: int = 5,
    mod_name: str = Query("default", description="Name of the mod/application")
):
    """
    Get a grid of H3 indexes centered around the specified tile.
    
    Args:
        tile_id: H3 index of the center tile
        width: Number of columns in the grid (used for bounds calculation)
        height: Number of rows in the grid (used for bounds calculation)
        
    Returns:
        A dictionary grid of H3 indexes with the center tile at (0,0)
    """
    logger.info(f"GET request received for grid centered on tile: {tile_id}, width: {width}, height: {height}, mod: {mod_name}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Add debug info about the tile
        resolution = h3.h3_get_resolution(tile_id)
        logger.info(f"DEBUG: Tile {tile_id} has resolution {resolution}")
        
        # Use a dictionary to store the grid with coordinate tuples as keys
        # This allows for negative indexes with the center tile at (0,0)
        grid_dict = {}
        
        # Define the standard mapping from neighbor positions to relative grid coordinates
        relative_coords_for_even_columns = {
            "bottom_middle": (-1, 0),
            "bottom_left": (-1, -1),
            "top_left": (0, -1),
            "top_middle": (1, 0),
            "top_right": (0, 1),
            "bottom_right": (-1, 1)
        }

        relative_coords_for_odd_columns = {
            "bottom_middle": (-1, 0),
            "bottom_left": (0, -1),
            "top_left": (1, -1),
            "top_middle": (1, 0),
            "top_right": (1, 1),
            "bottom_right": (0, 1)
        }

        # Define the inverse mapping for verification
        inverse_positions = {
            "bottom_middle": "top_middle",
            "bottom_left": "top_right",
            "top_left": "bottom_right",
            "top_middle": "bottom_middle",
            "top_right": "bottom_left",
            "bottom_right": "top_left"
        }
        
        # Step 2: Place center tile at (0,0)
        center_coords = (0, 0)
        grid_dict[center_coords] = tile_id

        # Load or create the center tile
        center_tile = Tile.load(tile_id, mod_name)
        if center_tile is None:
            logger.info(f"DEBUG: Center tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                center_tile = PentagonTile(tile_id)
            else:
                center_tile = HexagonTile(tile_id)
            center_tile.save_static()
        else:
            logger.info(f"DEBUG: Center tile {tile_id} loaded from storage")
        
        # Debug: Check if the center tile has neighbors
        logger.info(f"DEBUG: Center tile neighbor_ids: {center_tile.neighbor_ids}")
        
        # Debug: Check if H3 library can find neighbors directly
        direct_neighbors = h3.k_ring(tile_id, 1)
        direct_neighbors = [n for n in direct_neighbors if n != tile_id]
        logger.info(f"DEBUG: Direct H3 neighbors: {direct_neighbors}")
        logger.info(f"DEBUG: Number of direct neighbors: {len(direct_neighbors)}")
        
        # Fix for resolution 15 tiles: If neighbor_ids is empty but H3 can find neighbors,
        # update the neighbor_ids and save the tile
        if not center_tile.neighbor_ids and direct_neighbors:
            logger.info(f"DEBUG: Fixing empty neighbor_ids for resolution {resolution} tile")
            # Use the _get_positioned_neighbors method to get proper position labels
            center_tile.neighbor_ids = center_tile._get_positioned_neighbors(tile_id)
            logger.info(f"DEBUG: Updated neighbor_ids: {center_tile.neighbor_ids}")
            # Save the updated static data
            center_tile.save_static()
            logger.info(f"DEBUG: Saved updated static data with neighbor_ids")
        
        # Check if we need to use the geographic coordinate-based algorithm
        # We'll use it if the center tile is a pentagon or if we detect pentagons in the k-ring
        use_geographic_algorithm = h3.h3_is_pentagon(tile_id)
        
        if not use_geographic_algorithm:
            # Check if there are any pentagons in the k-ring
            k_ring_size = max(width, height) // 2 + 1
            k_ring = h3.k_ring(tile_id, k_ring_size)
            for h3_index in k_ring:
                if h3.h3_is_pentagon(h3_index):
                    use_geographic_algorithm = True
                    logger.info(f"DEBUG: Pentagon detected in k-ring: {h3_index}")
                    break
        
        logger.info(f"DEBUG: Using geographic algorithm: {use_geographic_algorithm}")
        
        if use_geographic_algorithm:
            # Geographic coordinate-based algorithm for grids with pentagons
            logger.info(f"Pentagon detected in grid. Using geographic coordinate-based algorithm.")
            
            # Get the k-ring of tiles around the center
            k_ring_size = max(width, height) // 2 + 1
            k_ring = h3.k_ring(tile_id, k_ring_size)
            
            # Get geographic coordinates for all tiles in the k-ring
            tile_coords = {}
            for h3_index in k_ring:
                lat, lng = h3.h3_to_geo(h3_index)
                tile_coords[h3_index] = (lat, lng)
            
            # Get center tile coordinates
            center_lat, center_lng = tile_coords[tile_id]
            
            # Group tiles by latitude (rows)
            # First, sort all tiles by latitude
            sorted_by_lat = sorted(tile_coords.items(), key=lambda x: x[1][0], reverse=False)  # reverse=False for south-to-north
            
            # Calculate the ideal number of rows based on square root of total tiles
            total_tiles = len(sorted_by_lat)
            ideal_rows = max(int(math.sqrt(total_tiles)), 1)
            
            # Ensure we don't exceed the requested height
            num_rows = min(ideal_rows, height * 2)
            
            logger.info(f"Geographic algorithm: Total tiles: {total_tiles}, Ideal rows: {ideal_rows}, Using rows: {num_rows}")
            
            # Calculate the latitude range
            min_lat = min(lat for _, (lat, _) in sorted_by_lat)
            max_lat = max(lat for _, (lat, _) in sorted_by_lat)
            lat_range = max_lat - min_lat
            
            logger.info(f"Latitude range: {min_lat} to {max_lat} (range: {lat_range})")
            
            # Create latitude buckets with approximately equal number of tiles per bucket
            lat_buckets = []
            if lat_range > 0 and num_rows > 1:
                # Distribute tiles evenly across buckets
                tiles_per_bucket = total_tiles // num_rows
                if tiles_per_bucket < 1:
                    tiles_per_bucket = 1
                
                for i in range(num_rows):
                    start_idx = i * tiles_per_bucket
                    end_idx = min((i + 1) * tiles_per_bucket, total_tiles)
                    
                    # If this is the last bucket, include all remaining tiles
                    if i == num_rows - 1:
                        end_idx = total_tiles
                    
                    # Skip empty buckets
                    if start_idx >= end_idx:
                        continue
                    
                    # Get min and max latitude for this bucket
                    bucket_tiles = sorted_by_lat[start_idx:end_idx]
                    bucket_min_lat = min(lat for _, (lat, _) in bucket_tiles)
                    bucket_max_lat = max(lat for _, (lat, _) in bucket_tiles)
                    
                    # Add a small buffer to avoid edge cases
                    buffer = (lat_range * 0.01)
                    if i > 0:  # Not the first bucket
                        bucket_min_lat -= buffer
                    if i < num_rows - 1:  # Not the last bucket
                        bucket_max_lat += buffer
                    
                    lat_buckets.append((bucket_min_lat, bucket_max_lat))
                    logger.info(f"Bucket {i}: {bucket_min_lat} to {bucket_max_lat} with {len(bucket_tiles)} tiles")
            else:
                # If all tiles have the same latitude or only one row, create a single bucket
                lat_buckets.append((min_lat, max_lat))
            
            # Assign tiles to buckets
            rows = [[] for _ in range(len(lat_buckets))]
            for h3_index, (lat, lng) in tile_coords.items():
                assigned = False
                for i, (bucket_min, bucket_max) in enumerate(lat_buckets):
                    if bucket_min <= lat <= bucket_max or (i == 0 and lat < bucket_min) or (i == len(lat_buckets) - 1 and lat > bucket_max):
                        rows[i].append((h3_index, lng))
                        assigned = True
                        break
                if not assigned:
                    logger.warning(f"Tile {h3_index} with lat {lat} not assigned to any bucket!")
            
            # Log the number of tiles in each row
            for i, row in enumerate(rows):
                logger.info(f"Row {i} has {len(row)} tiles")
            
            # Sort tiles within each row by longitude (west to east)
            for i in range(len(rows)):
                rows[i].sort(key=lambda x: x[1])
            
            # Log the sorted rows
            for i, row in enumerate(rows):
                if row:
                    logger.info(f"Row {i} after sorting: {[h3_idx for h3_idx, _ in row]}")
            
            # Calculate grid coordinates
            center_row_idx = None
            center_col_idx = None
            
            # Find the row and column of the center tile
            for row_idx, row in enumerate(rows):
                for col_idx, (h3_index, _) in enumerate(row):
                    if h3_index == tile_id:
                        center_row_idx = row_idx
                        center_col_idx = col_idx
                        logger.info(f"Found center tile at row {row_idx}, col {col_idx}")
                        break
                if center_row_idx is not None:
                    break
            
            # If center tile wasn't found in any row, default to middle position
            if center_row_idx is None:
                center_row_idx = len(rows) // 2
                center_col_idx = 0
                logger.warning(f"Center tile not found in any row. Using default position: row {center_row_idx}, col {center_col_idx}")
                
            # Verify that the center tile will be at (0,0)
            test_grid_row = center_row_idx - center_row_idx
            test_grid_col = center_col_idx - center_col_idx
            if test_grid_row != 0 or test_grid_col != 0:
                logger.error(f"Center tile calculation error! Would be at ({test_grid_row}, {test_grid_col}) instead of (0,0)")
                
            # Assign grid coordinates to each tile
            for row_idx, row in enumerate(rows):
                for col_idx, (h3_index, _) in enumerate(row):
                    grid_row = row_idx - center_row_idx
                    grid_col = col_idx - center_col_idx
                    grid_dict[(grid_row, grid_col)] = h3_index
                    logger.info(f"Assigned tile {h3_index} to grid position ({grid_row}, {grid_col})")
            
            # Double-check that the center tile is at (0,0)
            if tile_id != grid_dict.get((0, 0)):
                logger.error(f"Center tile {tile_id} not at (0,0)! Found {grid_dict.get((0, 0))} instead.")
                # Force the center tile to be at (0,0)
                grid_dict[(0, 0)] = tile_id
        else:
            # Original algorithm for regular hexagonal grids
            # Track which tiles have been placed and their positions
            position_map = {tile_id: center_coords}
            
            # Step 3: Place immediate neighbors of the center tile
            # This establishes the center tile as the single source of truth
            logger.info(f"DEBUG: Placing immediate neighbors of center tile")
            for position, neighbor_id in center_tile.neighbor_ids.items():
                logger.info(f"DEBUG: Processing neighbor at position {position}: {neighbor_id}")
                if neighbor_id == "pentagon":
                    logger.info(f"DEBUG: Skipping pentagon placeholder at position {position}")
                    continue
                    
                if position in relative_coords_for_even_columns:
                    row_offset, col_offset = relative_coords_for_even_columns[position]
                    neighbor_coords = (center_coords[0] + row_offset, center_coords[1] + col_offset)
                    logger.info(f"DEBUG: Placing neighbor {neighbor_id} at coordinates {neighbor_coords}")
                    
                    # Place the neighbor in the grid
                    grid_dict[neighbor_coords] = neighbor_id
                    position_map[neighbor_id] = neighbor_coords
                else:
                    logger.warning(f"DEBUG: Position {position} not found in relative_coords_for_even_columns")

            # Step 4: Initialize processing
            done_tiles = {(0, 0)}  # Set of processed tile coordinates
            logger.info(f"DEBUG: Initial done_tiles: {done_tiles}")

            n_rings = int(max([width, height]) + 1)
            logger.info(f"DEBUG: Processing {n_rings} rings")

            # Step 5: Process neighbors
            for i in range(n_rings):
                logger.info(f"DEBUG: Processing ring {i+1} of {n_rings}")
                # Go over all placed tiles but skip the ones that are done
                for coords, current_id in list(grid_dict.items()):
                    logger.info(f"DEBUG: Processing tile {current_id} at coordinates {coords}")

                    if coords in done_tiles:
                        # Skip already processed tiles
                        logger.info(f"DEBUG: Skipping already processed tile {current_id} at {coords}")
                        continue

                    # Load the current tile
                    current_tile = Tile.load(current_id, mod_name)

                    if current_tile is None:
                        logger.info(f"[{datetime.now()}] Tile {current_id} not found in storage, creating new one")
                        if h3.h3_is_pentagon(current_id):
                            current_tile = PentagonTile(current_id)
                        else:
                            current_tile = HexagonTile(current_id)

                        # Save the static data for the newly created tile
                        current_tile.save_static()
                        logger.info(f"[{datetime.now()}] New tile {current_id} static data saved to storage")
                    
                    # Debug: Check if the current tile has neighbors
                    logger.info(f"DEBUG: Current tile {current_id} neighbor_ids: {current_tile.neighbor_ids}")

                    # Process each neighbor
                    error=False
                    for position, neighbor_id in current_tile.neighbor_ids.items():
                        logger.info(f"DEBUG: Processing neighbor at position {position}: {neighbor_id}")
                        # Skip pentagon placeholders
                        if neighbor_id == "pentagon":
                            logger.info(f"DEBUG: Skipping pentagon placeholder at position {position}")
                            continue

                        # Find the relative coordinates
                        if coords[1] % 2 == 0:  # Even column
                            relative_coords = (coords[0]+relative_coords_for_even_columns[position][0],
                                            coords[1]+relative_coords_for_even_columns[position][1])
                            logger.info(f"DEBUG: Using even column offset for position {position}: {relative_coords_for_even_columns[position]}")
                        else:  # Odd column
                            relative_coords = (coords[0] + relative_coords_for_odd_columns[position][0],
                                            coords[1] + relative_coords_for_odd_columns[position][1])
                            logger.info(f"DEBUG: Using odd column offset for position {position}: {relative_coords_for_odd_columns[position]}")
                        
                        logger.info(f"DEBUG: Calculated relative coordinates for neighbor {neighbor_id}: {relative_coords}")

                        # Place the neighbor in the grid
                        if relative_coords in grid_dict and grid_dict[relative_coords] != neighbor_id:
                            logger.error(f'ERROR: trying to overwrite existing tile {relative_coords} with new data {neighbor_id}')
                            error=True
                            break

                        grid_dict[relative_coords] = neighbor_id
                        logger.info(f"DEBUG: Added neighbor {neighbor_id} to grid at position {relative_coords}")

                    if error:
                        logger.error(f"DEBUG: Error detected, breaking out of neighbor processing loop")
                        break

                    # Mark the current tile as done
                    done_tiles.add(coords)
                    logger.info(f"DEBUG: Marked tile {current_id} at {coords} as done")
        
        # Identify pentagon positions
        pentagon_positions = []
        for coords, grid_tile_id in grid_dict.items():
            if grid_tile_id is not None and h3.h3_is_pentagon(grid_tile_id):
                pentagon_positions.append(list(coords))
        
        logger.info(f"Grid created successfully with center tile and immediate neighbors only")
        logger.info(f"Found {len(pentagon_positions)} pentagons in the grid")
        
        # Count filled cells for logging
        filled_count = len(grid_dict)
        logger.info(f"Grid stats: {filled_count} filled cells")
        
        # Convert dictionary keys from tuples to strings for JSON serialization
        serializable_grid = {}
        for coords, grid_tile_id in grid_dict.items():
            # Convert tuple key to string key "row,col"
            key = f"{coords[0]},{coords[1]}"
            serializable_grid[key] = grid_tile_id
        
        # Calculate the bounds of the grid
        min_row = min(coords[0] for coords in grid_dict.keys())
        max_row = max(coords[0] for coords in grid_dict.keys())
        min_col = min(coords[1] for coords in grid_dict.keys())
        max_col = max(coords[1] for coords in grid_dict.keys())
        
        response = {
            "center_tile_id": tile_id,
            "grid": serializable_grid,
            "pentagon_positions": pentagon_positions,
            "bounds": {
                "min_row": min_row,
                "max_row": max_row,
                "min_col": min_col,
                "max_col": max_col
            }
        }
        
        # Add tile data for all tiles in the grid
        tile_data = {}
        for h3_index in set(serializable_grid.values()):
            if h3_index is not None:
                # Load the tile data
                grid_tile = Tile.load(h3_index, mod_name)
                if grid_tile:
                    # Get the tile data
                    grid_tile_data = grid_tile.to_dict()
                    
                    # Get the latest map path
                    latest_map_path = get_latest_hex_map_path(h3_index)
                    if latest_map_path:
                        # Convert to relative path for frontend use
                        relative_path = os.path.relpath(latest_map_path, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
                        grid_tile_data["latest_map"] = relative_path
                    
                    # Add to the tile data dictionary
                    tile_data[h3_index] = grid_tile_data
        
        # Add the tile data to the response
        response["tile_data"] = tile_data
        
        return response
    
    except Exception as e:
        logger.error(f"Error creating grid for tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tile_id}/resolutions")
async def get_resolutions(
    tile_id: str = Path(..., description="H3 index of the tile"),
    mod_name: str = Query("default", description="Name of the mod/application")
):
    """Get all resolution IDs for a specific tile."""
    logger.info(f"[{datetime.now()}] GET request received for resolutions of tile: {tile_id}, mod: {mod_name}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Load or create the tile
        tile = Tile.load(tile_id, mod_name)
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new one")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            # Save the static data for the newly created tile
            tile.save_static()
            logger.info(f"[{datetime.now()}] New tile {tile_id} static data saved to storage")
        
        # Return resolution IDs
        logger.info(f"[{datetime.now()}] Returning {len(tile.resolution_ids)} resolution IDs for tile {tile_id}")
        return {
            "tile_id": tile_id,
            "resolution_ids": tile.resolution_ids
        }
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error getting resolutions for tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{tile_id}/generate-map")
async def generate_map(
    tile_id: str = Path(..., description="H3 index of the tile to generate map for")
):
    """Generate a map image for a specific tile."""
    logger.info(f"[{datetime.now()}] POST request received to generate map for tile: {tile_id}")
    try:
        # Validate the H3 index
        if not h3.h3_is_valid(tile_id):
            logger.warning(f"[{datetime.now()}] Invalid H3 index: {tile_id}")
            raise HTTPException(status_code=400, detail="Invalid H3 index")
        
        # Try to load the tile
        tile = Tile.load(tile_id)
        
        # If not found in storage, create a new one
        if tile is None:
            logger.info(f"[{datetime.now()}] Tile {tile_id} not found in storage, creating new tile")
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            # Save the static data for the newly created tile
            tile.save_static()
        
        # Generate the map
        logger.info(f"[{datetime.now()}] Generating map for tile: {tile_id}")
        tile.generate_hex_map()
        
        return {"status": "success", "message": f"Map generated for tile {tile_id}"}
    
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error generating map for tile {tile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating map: {str(e)}")

def _calculate_distance(point1, point2):
    """
    Calculate the squared distance between two points (lat, lng).
    Using squared distance to avoid unnecessary sqrt calculations.
    """
    return (point1[0] - point2[0])**2 + (point1[1] - point2[1])**2
