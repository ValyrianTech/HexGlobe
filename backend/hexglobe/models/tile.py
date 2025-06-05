from abc import ABC, abstractmethod
import json
import os
from typing import Dict, List, Optional, Union
import h3
from pydantic import BaseModel

# Data directory for tile storage
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "tiles")
os.makedirs(DATA_DIR, exist_ok=True)

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
        except ValueError:
            self.parent_id = None
            self.children_ids = []
    
    def get_neighbors(self) -> List["Tile"]:
        """Returns neighboring tiles."""
        neighbor_indices = h3.k_ring(self.id, 1)
        # Remove self from neighbors
        neighbor_indices = [idx for idx in neighbor_indices if idx != self.id]
        
        # Create appropriate tile objects based on the type
        neighbors = []
        for idx in neighbor_indices:
            if h3.h3_is_pentagon(idx):
                neighbors.append(PentagonTile(idx))
            else:
                neighbors.append(HexagonTile(idx))
        
        return neighbors
    
    def move_content_to(self, target_tile: "Tile") -> bool:
        """Moves content to a neighboring tile."""
        if target_tile.id not in [n.id for n in self.get_neighbors()]:
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
            "children_ids": self.children_ids
        }
    
    def save(self) -> None:
        """Persists tile data to storage."""
        file_path = os.path.join(DATA_DIR, f"{self.id}.json")
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, tile_id: str) -> Optional["Tile"]:
        """Loads tile data from storage."""
        file_path = os.path.join(DATA_DIR, f"{tile_id}.json")
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
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
        
        return tile
    
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
