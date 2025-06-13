from abc import ABC, abstractmethod
import json
import os
import logging
from typing import Dict, List, Optional, Union
import h3
import math
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Base data directory
BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")

def get_static_path(h3_index: str) -> str:
    """
    Calculate the path for static tile data based on H3 index.
    
    Args:
        h3_index: The H3 index of the tile
        
    Returns:
        The absolute file path for the static data JSON file
    """
    # Get resolution from the index
    resolution = h3.h3_get_resolution(h3_index)
    
    # Create directory structure with 2-digit segments
    path_segments = []
    for i in range(0, len(h3_index) - 1, 2):
        if i + 1 < len(h3_index):
            segment = h3_index[i:i+2]
            path_segments.append(segment)
    
    # Construct the path
    static_dir = os.path.join(BASE_DATA_DIR, "static", f"res_{resolution}", *path_segments)
    os.makedirs(static_dir, exist_ok=True)
    
    return os.path.join(static_dir, f"{h3_index}.json")

def get_dynamic_path(h3_index: str, mod_name: str = "default") -> str:
    """
    Calculate the path for dynamic tile data.
    
    Args:
        h3_index: The H3 index of the tile
        mod_name: The name of the mod/application (default: "default")
        
    Returns:
        The path to the dynamic data file
    """
    resolution = h3.h3_get_resolution(h3_index)
    path_segments = [h3_index[i:i+2] for i in range(0, min(len(h3_index), 10), 2)]
    dynamic_dir = os.path.join(BASE_DATA_DIR, "dynamic", mod_name, f"res_{resolution}", *path_segments)
    return os.path.join(dynamic_dir, f"{h3_index}.json")

def get_hex_map_path(h3_index: str, timestamp: str = None) -> str:
    """
    Calculate the path for hex map image based on H3 index and optional timestamp.
    
    Args:
        h3_index: The H3 index of the tile
        timestamp: Optional timestamp for versioning
        
    Returns:
        The absolute file path for the hex map PNG file
    """
    # Get resolution from the index
    resolution = h3.h3_get_resolution(h3_index)
    
    # Create directory structure with 2-digit segments
    path_segments = []
    for i in range(0, len(h3_index) - 1, 2):
        if i + 1 < len(h3_index):
            segment = h3_index[i:i+2]
            path_segments.append(segment)
    
    # Construct the path
    hex_maps_dir = os.path.join(BASE_DATA_DIR, "hex_maps", f"res_{resolution}", *path_segments)
    os.makedirs(hex_maps_dir, exist_ok=True)
    
    # If timestamp is provided, include it in the filename
    if timestamp:
        return os.path.join(hex_maps_dir, f"{h3_index}_{timestamp}.png")
    else:
        return os.path.join(hex_maps_dir, f"{h3_index}.png")

def get_latest_hex_map_path(h3_index: str) -> str:
    """
    Get the path to the most recent hex map image for a tile.
    
    Args:
        h3_index: The H3 index of the tile
        
    Returns:
        The absolute file path for the most recent hex map PNG file
    """
    # Get the directory where map images are stored
    resolution = h3.h3_get_resolution(h3_index)
    path_segments = []
    for i in range(0, len(h3_index) - 1, 2):
        if i + 1 < len(h3_index):
            segment = h3_index[i:i+2]
            path_segments.append(segment)
    
    hex_maps_dir = os.path.join(BASE_DATA_DIR, "hex_maps", f"res_{resolution}", *path_segments)
    
    # If directory doesn't exist, return the default path
    if not os.path.exists(hex_maps_dir):
        return get_hex_map_path(h3_index)
    
    # Find all map files for this tile
    import glob
    map_files = glob.glob(os.path.join(hex_maps_dir, f"{h3_index}_*.png"))
    
    # If no timestamped files exist, check for the default file
    if not map_files:
        default_path = get_hex_map_path(h3_index)
        if os.path.exists(default_path):
            return default_path
        return None
    
    # Sort by timestamp (newest first)
    map_files.sort(reverse=True)
    
    # Return the newest file
    return map_files[0]

class VisualProperties(BaseModel):
    """Visual properties for a tile."""
    border_color: str = "#000000"
    border_thickness: int = 1
    border_style: str = "solid"
    fill_color: str = "#FFFFFF"
    fill_opacity: float = 0.5

class TileData(BaseModel):
    """Data model for tile storage."""
    id: str
    content: Optional[str] = None
    visual_properties: VisualProperties = VisualProperties()
    parent_id: Optional[str] = None
    children_ids: List[str] = []
    neighbor_ids: Dict[str, str] = {}  # Changed from List to Dict for position-based neighbors
    resolution_ids: Dict[str, str] = {}  # New field for different resolution IDs (resolution -> h3 index)
    resolution: int = 0  # Current resolution level of the tile

class Tile(ABC):
    """Base class for all tiles."""
    
    def __init__(self, id: str, content: Optional[str] = None):
        """Initialize a tile with an H3 index ID."""
        self.id = id
        self.content = content
        self.visual_properties = VisualProperties()
        
        # Get parent and children from H3
        try:
            # Get the resolution of the current tile
            self.resolution = h3.h3_get_resolution(id)
            logger.info(f"Initializing tile {id} with resolution {self.resolution}")
            
            self.parent_id = h3.h3_to_parent(id, self.resolution - 1) if self.resolution > 0 else None
            
            # Only get children if we're not at max resolution
            if self.resolution < 15:
                self.children_ids = list(h3.h3_to_children(id, self.resolution + 1))
            else:
                logger.info(f"Tile {id} is at max resolution 15, no children available")
                self.children_ids = []
            
            # Get neighbor IDs with position labels
            self.neighbor_ids = self._get_positioned_neighbors(id)
            
            # Get different resolution IDs for all resolutions (0-15)
            self.resolution_ids = {}
            current_res = self.resolution
            logger.info(f"Current resolution: {current_res}")
            
            # Get geographic coordinates of this location
            lat, lng = h3.h3_to_geo(id)
            logger.info(f"Calculating all resolution IDs for location ({lat}, {lng})")
            
            # Calculate IDs for all resolutions (0-15)
            for res in range(16):  # H3 supports resolutions 0-15
                if res == current_res:
                    # For current resolution, use the existing ID
                    self.resolution_ids[str(res)] = id
                else:
                    # For other resolutions, calculate the ID at this location
                    logger.info(f"Calculating resolution {res} ID")
                    self.resolution_ids[str(res)] = h3.geo_to_h3(lat, lng, res)
            
        except ValueError as e:
            logger.error(f"Error initializing tile {id}: {str(e)}")
            self.parent_id = None
            self.children_ids = []
            self.neighbor_ids = {}  # Changed from list to empty dict
            self.resolution_ids = {}
    
    def _get_positioned_neighbors(self, tile_id: str) -> Dict[str, str]:
        """
        Get neighbor IDs as a dictionary mapping position labels to H3 indexes.
        
        For hexagons with flat edge at bottom:
        - Keys: top_left, top_middle, top_right, bottom_left, bottom_middle, bottom_right
        
        For pentagons:
        - Similar approach but with 5 neighbors, with one position set to 'pentagon'
        """
        # Get all neighbors
        neighbors = h3.k_ring(tile_id, 1)
        neighbors = [idx for idx in neighbors if idx != tile_id]
        
        # Get center coordinates of the tile
        center_lat, center_lng = h3.h3_to_geo(tile_id)
        
        # Get boundary vertices
        boundary = h3.h3_to_geo_boundary(tile_id)
        
        # Determine if we're in northern or southern hemisphere
        in_northern_hemisphere = center_lat > 0
        
        # Find the edge closest to the equator
        min_lat_diff = float('inf')
        equator_edge_idx = 0
        
        for i in range(len(boundary)):
            next_i = (i + 1) % len(boundary)
            edge_lat = (boundary[i][0] + boundary[next_i][0]) / 2  # Average latitude of the edge
            lat_diff = abs(edge_lat)  # Distance from equator
            
            if lat_diff < min_lat_diff:
                min_lat_diff = lat_diff
                equator_edge_idx = i
        
        # Determine reference vertex based on hemisphere
        if in_northern_hemisphere:
            # For northern hemisphere, use the right vertex of bottom edge as reference
            ref_vertex_idx = (equator_edge_idx + 1) % len(boundary)
        else:
            # For southern hemisphere, use the right vertex of top edge as reference
            ref_vertex_idx = equator_edge_idx
        
        # Get reference vertex coordinates
        ref_lat, ref_lng = boundary[ref_vertex_idx]
        
        # Calculate bearing from center to reference vertex
        ref_bearing = self._calculate_bearing(center_lat, center_lng, ref_lat, ref_lng)
        
        # Get center coordinates of each neighbor
        neighbor_bearings = []
        for n_id in neighbors:
            n_lat, n_lng = h3.h3_to_geo(n_id)
            bearing = self._calculate_bearing(center_lat, center_lng, n_lat, n_lng)
            
            # Adjust bearing relative to reference bearing
            rel_bearing = (bearing - ref_bearing) % 360
            neighbor_bearings.append((n_id, rel_bearing))
        
        # Sort neighbors by relative bearing (clockwise)
        neighbor_bearings.sort(key=lambda x: x[1])
        
        # For a flat-bottom hexagon, map the neighbors to positions
        # The positions are assigned clockwise starting from the reference point
        is_pentagon = h3.h3_is_pentagon(tile_id)
        num_neighbors = 5 if is_pentagon else 6
        
        # Define position names in clockwise order
        position_names = [
            "bottom_middle",  # Starting position (reference vertex is at bottom-middle)
            "bottom_left", 
            "top_left", 
            "top_middle", 
            "top_right", 
            "bottom_right"
        ]
        
        # Map neighbors to positions
        positioned_neighbors = {}
        for i, (n_id, _) in enumerate(neighbor_bearings):
            if i < len(position_names):
                positioned_neighbors[position_names[i]] = n_id
        
        # For pentagons, identify the missing position and mark it
        if is_pentagon:
            for position in position_names:
                if position not in positioned_neighbors:
                    positioned_neighbors[position] = "pentagon"
                    break
        
        return positioned_neighbors
    
    def _calculate_bearing(self, lat1, lng1, lat2, lng2):
        """
        Calculate the bearing from point 1 to point 2.
        All angles in radians.
        """
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Calculate bearing
        y = math.sin(lng2 - lng1) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(lng2 - lng1)
        bearing = math.atan2(y, x)
        
        # Convert to degrees
        bearing = math.degrees(bearing)
        
        # Normalize to 0-360
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def get_neighbors(self) -> List["Tile"]:
        """Returns neighboring tiles."""
        # Create appropriate tile objects based on the type
        neighbors = []
        for position, idx in self.neighbor_ids.items():
            if idx == "pentagon":  # Skip pentagon placeholders
                continue
            if h3.h3_is_pentagon(idx):
                neighbors.append(PentagonTile(idx))
            else:
                neighbors.append(HexagonTile(idx))
        return neighbors
    
    def move_content_to(self, target_tile: "Tile") -> bool:
        """Move content to another tile."""
        # No longer checking if target is a neighbor - allow moving to any tile
        
        if target_tile is None:
            return False
        
        target_tile.content = self.content
        self.content = None
        
        # Save both tiles
        self.save()
        target_tile.save()
        
        return True
    
    def get_parent(self) -> Optional["Tile"]:
        """Returns the parent tile."""
        if self.parent_id is None:
            return None
        
        if h3.h3_is_pentagon(self.parent_id):
            return PentagonTile(self.parent_id)
        else:
            return HexagonTile(self.parent_id)
    
    def get_children(self) -> List["Tile"]:
        """Returns child tiles."""
        children = []
        for child_id in self.children_ids:
            if h3.h3_is_pentagon(child_id):
                children.append(PentagonTile(child_id))
            else:
                children.append(HexagonTile(child_id))
        
        return children
    
    def set_visual_property(self, property_name: str, value: Union[str, int, float]) -> bool:
        """Sets a visual property."""
        if not hasattr(self.visual_properties, property_name):
            return False
        
        setattr(self.visual_properties, property_name, value)
        return True
    
    def to_dict(self) -> Dict:
        """Convert tile to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "visual_properties": self.visual_properties.dict(),
            "parent_id": self.parent_id,
            "children_ids": list(self.children_ids) if isinstance(self.children_ids, set) else self.children_ids,
            "neighbor_ids": self.neighbor_ids,  # Now a dictionary with position keys
            "resolution_ids": self.resolution_ids,
            "resolution": self.resolution
        }
    
    def to_static_dict(self) -> Dict:
        """Convert tile to dictionary for static data JSON serialization."""
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "children_ids": list(self.children_ids) if isinstance(self.children_ids, set) else self.children_ids,
            "neighbor_ids": self.neighbor_ids,
            "resolution_ids": self.resolution_ids,
            "resolution": self.resolution
        }
    
    def to_dynamic_dict(self) -> Dict:
        """Convert tile to dictionary for dynamic data JSON serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "visual_properties": self.visual_properties.dict()
        }
    
    def save(self) -> None:
        """
        Persists tile data to storage.
        
        This method now uses the new split format, saving static data always
        and dynamic data only when needed.
        """
        try:
            logger.info(f"Saving tile {self.id}")
            
            # Save static data (always)
            self.save_static()
            
            # Save dynamic data (only if needed)
            self.save_dynamic()
            
            logger.info(f"Successfully saved tile {self.id}")
                
        except Exception as e:
            logger.error(f"Error saving tile {self.id}: {str(e)}")
            raise
    
    def save_static(self) -> None:
        """
        Persists static tile data to storage.
        Static data includes H3 grid information that doesn't change.
        """
        try:
            # Save static data
            static_path = get_static_path(self.id)
            logger.info(f"Saving static data for tile {self.id} to {static_path}")
            
            static_data = self.to_static_dict()
            os.makedirs(os.path.dirname(static_path), exist_ok=True)
            
            with open(static_path, 'w') as f:
                json.dump(static_data, f, indent=2)
            
            logger.info(f"Successfully saved static data for tile {self.id}")
    
        except Exception as e:
            logger.error(f"Error saving static data for tile {self.id}: {str(e)}")
            raise
    
    def save_dynamic(self, mod_name: str = "default") -> None:
        """
        Persists dynamic tile data to storage.
        Dynamic data includes content and visual properties that can change.
        Only saves if there's actual content or non-default visual properties.
        
        Args:
            mod_name: The name of the mod/application (default: "default")
        """
        try:
            # Check if there's any content or non-default visual properties
            has_content = self.content is not None and self.content.strip() != ""
            
            # Create a default visual properties object for comparison
            default_visual_props = VisualProperties()
            
            # Check if any visual property is different from default
            has_custom_visuals = False
            for prop_name, prop_value in self.visual_properties.dict().items():
                default_value = getattr(default_visual_props, prop_name)
                if prop_value != default_value:
                    has_custom_visuals = True
                    break
            
            # Only save if there's content or custom visual properties
            if has_content or has_custom_visuals:
                # Get the dynamic path
                dynamic_path = get_dynamic_path(self.id, mod_name)
                logger.info(f"Saving dynamic data for tile {self.id} to {dynamic_path}")
                
                # Create directories only when we're actually saving data
                os.makedirs(os.path.dirname(dynamic_path), exist_ok=True)
                
                dynamic_data = self.to_dynamic_dict()
                
                with open(dynamic_path, 'w') as f:
                    json.dump(dynamic_data, f, indent=2)
                
                logger.info(f"Successfully saved dynamic data for tile {self.id}")
            else:
                logger.info(f"No content or custom visual properties for tile {self.id}, skipping dynamic data save")
                
                # Check if a dynamic file already exists and delete it if it does
                dynamic_path = get_dynamic_path(self.id, mod_name)
                if os.path.exists(dynamic_path):
                    logger.info(f"Removing empty dynamic data file for tile {self.id}")
                    os.remove(dynamic_path)
            
        except Exception as e:
            logger.error(f"Error saving dynamic data for tile {self.id}: {str(e)}")
            raise
    
    def generate_hex_map(self) -> None:
        """
        Generates a hex map image for this tile using the generate_hex_map.py script.
        The image is saved in the hex_maps directory with the same structure as static/dynamic data.
        Includes a timestamp in the filename for versioning.
        """
        try:
            import subprocess
            from datetime import datetime
            
            # Generate timestamp in ISO format (with colons replaced to be filename-safe)
            timestamp = datetime.now().isoformat().replace(':', '-').replace('.', '-')
            
            # Get the path for the hex map with timestamp
            hex_map_path = get_hex_map_path(self.id, timestamp)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(hex_map_path), exist_ok=True)
            
            # Path to the generate_hex_map.py script
            script_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                "frontend", "assets", "generate_hex_map.py"
            )
            
            # Run the script to generate the hex map
            logger.info(f"Generating hex map for tile {self.id} with timestamp {timestamp}")
            result = subprocess.run(
                [
                    "python", 
                    script_path, 
                    "--h3_index", self.id, 
                    "--output", hex_map_path
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully generated hex map for tile {self.id}")
            else:
                logger.error(f"Error generating hex map for tile {self.id}: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error generating hex map for tile {self.id}: {str(e)}")
            # Don't raise the exception, as this is not critical for tile saving
    
    @classmethod
    def load(cls, tile_id: str, mod_name: str = "default") -> Optional["Tile"]:
        """
        Load a tile from storage.
        
        Args:
            tile_id: The H3 index of the tile
            mod_name: The name of the mod/application (default: "default")
            
        Returns:
            The loaded tile or None if not found
        """
        try:
            return cls.load_from_split_files(tile_id, mod_name)
        except Exception as e:
            logger.error(f"Error loading tile {tile_id}: {str(e)}")
            return None
    
    @classmethod
    def load_from_split_files(cls, tile_id: str, mod_name: str = "default") -> Optional["Tile"]:
        """
        Load a tile from storage using the split file format.
        
        Args:
            tile_id: The H3 index of the tile
            mod_name: The name of the mod/application (default: "default")
            
        Returns:
            The loaded tile or None if not found
        """
        static_path = get_static_path(tile_id)
        dynamic_path = get_dynamic_path(tile_id, mod_name)
        
        # Check if at least the static file exists
        if not os.path.exists(static_path):
            logger.info(f"Static data file not found for tile {tile_id}")
            return None
        
        try:
            # Load static data
            with open(static_path, 'r') as f:
                static_data = json.load(f)
            
            # Create the appropriate tile type
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            # Load static data
            tile.parent_id = static_data.get("parent_id")
            tile.children_ids = static_data.get("children_ids", [])
            tile.neighbor_ids = static_data.get("neighbor_ids", {})
            tile.resolution_ids = static_data.get("resolution_ids", {})
            tile.resolution = static_data.get("resolution", h3.h3_get_resolution(tile_id))
            
            # Try to load dynamic data if it exists
            if os.path.exists(dynamic_path):
                with open(dynamic_path, 'r') as f:
                    dynamic_data = json.load(f)
                
                # Load dynamic data
                tile.content = dynamic_data.get("content")
                
                if "visual_properties" in dynamic_data:
                    tile.visual_properties = VisualProperties(**dynamic_data["visual_properties"])
            
            return tile
            
        except Exception as e:
            logger.error(f"Error loading tile {tile_id} from split files: {str(e)}")
            return None
    
    @abstractmethod
    def get_geometry(self) -> List[List[float]]:
        """Returns the geometry of the tile as a list of [lat, lng] coordinates."""
        pass


class HexagonTile(Tile):
    """Hexagon tile class."""
    
    def __init__(self, id: str, content: Optional[str] = None):
        super().__init__(id, content)
        if h3.h3_is_pentagon(id):
            raise ValueError(f"ID {id} is a pentagon, not a hexagon")
    
    def get_geometry(self) -> List[List[float]]:
        """Returns the geometry of the hexagon as a list of [lat, lng] coordinates."""
        boundary = h3.h3_to_geo_boundary(self.id)
        # Convert to [lat, lng] format
        return [[lat, lng] for lat, lng in boundary]


class PentagonTile(Tile):
    """Pentagon tile class."""
    
    def __init__(self, id: str, content: Optional[str] = None):
        super().__init__(id, content)
        if not h3.h3_is_pentagon(id):
            raise ValueError(f"ID {id} is not a pentagon")
    
    def get_geometry(self) -> List[List[float]]:
        """Returns the geometry of the pentagon as a list of [lat, lng] coordinates."""
        boundary = h3.h3_to_geo_boundary(self.id)
        # Convert to [lat, lng] format
        return [[lat, lng] for lat, lng in boundary]
