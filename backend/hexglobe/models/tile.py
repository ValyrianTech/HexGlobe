from abc import ABC, abstractmethod
import json
import os
import logging
from typing import Dict, List, Optional, Union
import h3
import math
from pydantic import BaseModel

# Set up logging
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
        str: The full path to the dynamic data JSON file
    """
    resolution = h3.h3_get_resolution(h3_index)
    path_segments = [h3_index[i:i+2] for i in range(0, len(h3_index) - 1, 2)]
    dynamic_dir = os.path.join(BASE_DATA_DIR, "dynamic", mod_name, f"res_{resolution}", *path_segments)
    
    # Note: We don't create directories here anymore
    # Directories will be created only when actually saving data
    
    return os.path.join(dynamic_dir, f"{h3_index}.json")

# Data directory for tile storage
DATA_DIR = os.path.join(BASE_DATA_DIR, "tiles")
os.makedirs(DATA_DIR, exist_ok=True)
logger.info(f"Data directory set to: {DATA_DIR}")

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
            
            self.parent_id = h3.h3_to_parent(id, self.resolution - 1) if self.resolution > 0 else None
            self.children_ids = list(h3.h3_to_children(id, self.resolution + 1))
            
            # Get neighbor IDs with position labels
            self.neighbor_ids = self._get_positioned_neighbors(id)
            
            # Get different resolution IDs
            self.resolution_ids = {}
            current_res = self.resolution
            
            # Get IDs for lower resolutions (parent hierarchy)
            temp_id = id
            for res in range(current_res - 1, -1, -1):
                temp_id = h3.h3_to_parent(temp_id, res)
                self.resolution_ids[str(res)] = temp_id
            
            # Get IDs for higher resolutions (child at center)
            lat, lng = h3.h3_to_geo(id)
            for res in range(current_res + 1, 16):  # H3 supports resolutions 0-15
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
    
    def move_content_to(self, target_id: str) -> bool:
        """Move content to another tile."""
        # Check if target is a neighbor
        if target_id not in self.neighbor_ids.values():
            return False
        
        target_tile = None
        for position, idx in self.neighbor_ids.items():
            if idx == target_id:
                if h3.h3_is_pentagon(idx):
                    target_tile = PentagonTile(idx)
                else:
                    target_tile = HexagonTile(idx)
                break
        
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
        """Persists tile data to storage (legacy method)."""
        try:
            file_path = os.path.join(DATA_DIR, f"{self.id}.json")
            logger.info(f"Attempting to save tile {self.id} to {file_path}")
            
            # Check if directory exists
            if not os.path.exists(DATA_DIR):
                logger.warning(f"Data directory {DATA_DIR} does not exist, creating it")
                os.makedirs(DATA_DIR, exist_ok=True)
            
            # Convert to dict and save
            tile_data = self.to_dict()
            logger.info(f"Tile data to save: {tile_data}")
            
            with open(file_path, 'w') as f:
                json.dump(tile_data, f, indent=2)
                
            logger.info(f"Successfully saved tile {self.id} to {file_path}")
            
            # Verify file was created
            if os.path.exists(file_path):
                logger.info(f"Verified file exists: {file_path}")
            else:
                logger.error(f"File was not created: {file_path}")
                
            # Also save using the new format
            self.save_static()
                
        except Exception as e:
            logger.error(f"Error saving tile {self.id}: {str(e)}")
            raise
    
    def save_split(self, mod_name: str = "default") -> None:
        """
        Persists tile data to storage using the new split format.
        
        Args:
            mod_name: The name of the mod/application (default: "default")
        """
        try:
            # Save static data
            self.save_static()
            
            # Save dynamic data
            self.save_dynamic(mod_name)
            
            logger.info(f"Successfully saved tile {self.id} in split format")
            
        except Exception as e:
            logger.error(f"Error saving tile {self.id} in split format: {str(e)}")
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
    
    @classmethod
    def load(cls, tile_id: str) -> Optional["Tile"]:
        """Load a tile from storage (legacy method)."""
        file_path = os.path.join(DATA_DIR, f"{tile_id}.json")
        if not os.path.exists(file_path):
            # Try loading from the new format
            return cls.load_split(tile_id)
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Create the appropriate tile type
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            # Load data
            tile.content = data.get("content")
            
            if "visual_properties" in data:
                tile.visual_properties = VisualProperties(**data["visual_properties"])
            
            tile.parent_id = data.get("parent_id")
            tile.children_ids = data.get("children_ids", [])
            
            # Handle both list and dict formats for backward compatibility
            neighbor_ids = data.get("neighbor_ids", {})
            if isinstance(neighbor_ids, list):
                # Convert old list format to new dict format
                tile.neighbor_ids = tile._get_positioned_neighbors(tile_id)
            else:
                tile.neighbor_ids = neighbor_ids
            
            tile.resolution_ids = data.get("resolution_ids", {})
            
            # Load resolution or calculate it if not present in the data
            if "resolution" in data:
                tile.resolution = data["resolution"]
            else:
                # For backward compatibility with existing tiles
                tile.resolution = h3.h3_get_resolution(tile_id)
            
            return tile
        except Exception as e:
            logger.error(f"Error loading tile {tile_id}: {str(e)}")
            return None
    
    @classmethod
    def load_split(cls, tile_id: str, mod_name: str = "default") -> Optional["Tile"]:
        """
        Load a tile from storage using the new split format.
        
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
            else:
                logger.info(f"Dynamic data file not found for tile {tile_id}, using default values")
            
            return tile
        except Exception as e:
            logger.error(f"Error loading tile {tile_id} from split format: {str(e)}")
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
