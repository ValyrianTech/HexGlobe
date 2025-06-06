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

# Data directory for tile storage
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "tiles")
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
    neighbor_ids: List[str] = []  # New field for neighbor IDs
    resolution_ids: Dict[str, str] = {}  # New field for different resolution IDs (resolution -> h3 index)

class Tile(ABC):
    """Base class for all tiles."""
    
    def __init__(self, id: str, content: Optional[str] = None):
        """Initialize a tile with an H3 index ID."""
        self.id = id
        self.content = content
        self.visual_properties = VisualProperties()
        
        # Get parent and children from H3
        try:
            self.parent_id = h3.h3_to_parent(id, h3.h3_get_resolution(id) - 1) if h3.h3_get_resolution(id) > 0 else None
            self.children_ids = h3.h3_to_children(id, h3.h3_get_resolution(id) + 1)
            
            # Get neighbor IDs in clockwise order
            self.neighbor_ids = self._get_ordered_neighbors(id)
            
            # Get different resolution IDs
            self.resolution_ids = {}
            current_res = h3.h3_get_resolution(id)
            
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
            self.neighbor_ids = []
            self.resolution_ids = {}
    
    def _get_ordered_neighbors(self, tile_id: str) -> List[str]:
        """
        Get neighbor IDs in a consistent clockwise order.
        
        For hexagons:
        - Determine which edge is closest to the equator
        - Use that as reference for ordering (bottom edge for northern hemisphere, top edge for southern)
        - Order neighbors clockwise starting from a consistent position
        
        For pentagons:
        - Similar approach but with 5 neighbors
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
        neighbor_coords = []
        for n_id in neighbors:
            n_lat, n_lng = h3.h3_to_geo(n_id)
            bearing = self._calculate_bearing(center_lat, center_lng, n_lat, n_lng)
            
            # Adjust bearing relative to reference bearing
            rel_bearing = (bearing - ref_bearing) % 360
            neighbor_coords.append((n_id, rel_bearing))
        
        # Sort neighbors by relative bearing (clockwise)
        neighbor_coords.sort(key=lambda x: x[1])
        
        # Extract just the IDs in clockwise order
        return [n[0] for n in neighbor_coords]
    
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
        for idx in self.neighbor_ids:
            if h3.h3_is_pentagon(idx):
                neighbors.append(PentagonTile(idx))
            else:
                neighbors.append(HexagonTile(idx))
        
        return neighbors
    
    def move_content_to(self, target_tile: "Tile") -> bool:
        """Moves content to a neighboring tile."""
        if target_tile.id not in self.neighbor_ids:
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
        """Convert tile to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "visual_properties": self.visual_properties.dict(),
            "parent_id": self.parent_id,
            "children_ids": list(self.children_ids),  # Convert set to list for JSON serialization
            "neighbor_ids": list(self.neighbor_ids),  # Convert set to list for JSON serialization
            "resolution_ids": self.resolution_ids  # Add resolution IDs to the dictionary
        }
    
    def save(self) -> None:
        """Persists tile data to storage."""
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
                
        except Exception as e:
            logger.error(f"Error saving tile {self.id}: {str(e)}")
            raise
    
    @classmethod
    def load(cls, tile_id: str) -> Optional["Tile"]:
        """Loads tile data from storage."""
        file_path = os.path.join(DATA_DIR, f"{tile_id}.json")
        
        if not os.path.exists(file_path):
            logger.info(f"Tile file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded tile data from {file_path}")
            
            if h3.h3_is_pentagon(tile_id):
                tile = PentagonTile(tile_id)
            else:
                tile = HexagonTile(tile_id)
            
            tile.content = data.get("content")
            
            # Load visual properties
            visual_props = data.get("visual_properties", {})
            for key, value in visual_props.items():
                if hasattr(tile.visual_properties, key):
                    setattr(tile.visual_properties, key, value)
            
            # Load neighbor_ids and resolution_ids if they exist in the data
            if "neighbor_ids" in data:
                tile.neighbor_ids = data.get("neighbor_ids", [])
            
            if "resolution_ids" in data:
                tile.resolution_ids = data.get("resolution_ids", {})
            
            return tile
        except Exception as e:
            logger.error(f"Error loading tile {tile_id}: {str(e)}")
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
