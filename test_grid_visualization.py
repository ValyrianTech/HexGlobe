#!/usr/bin/env python3
"""
Simple test script to visualize the hexagon grid from the grid endpoint.
"""
import sys
import requests
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import RegularPolygon
import matplotlib.colors as mcolors

def fetch_grid_data(tile_id, width=5, height=5):
    """Fetch grid data from the API endpoint."""
    url = f"http://127.0.0.1:8000/api/tiles/{tile_id}/grid"
    params = {
        "width": width,
        "height": height
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching grid data: {e}")
        sys.exit(1)

def verify_grid_positions(grid_data):
    """Verify if specific grid positions have the expected tile IDs."""
    grid = grid_data["grid"]
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    
    # Expected neighbors at specific positions as provided by the user
    expected_positions = {
        # Position: Expected ID
        (2, 2): "8a194da9a74ffff",  # Center
        (1, 2): "8a194da9a297fff",  # bottom_middle
        (1, 1): "8a194da9a667fff",  # bottom_left
        (2, 1): "8a194da9a75ffff",  # top_left
        (3, 2): "8a194da9a747fff",  # top_middle
        (2, 3): "8a194da9a76ffff",  # top_right
        (1, 3): "8a194da9a2b7fff",  # bottom_right
        
        # Additional positions from (0,0) to (4,4)
        # Fill in the expected IDs manually after running the script once
        (0, 0): "8a194da9a64ffff",  # Fill in expected ID
        (0, 1): "8a194da9a66ffff",  # Fill in expected ID
        (0, 2): "8a194da9a29ffff",  # Fill in expected ID
        (0, 3): "8a194da9a287fff",  # Fill in expected ID
        (0, 4): "8a194da9a2affff",  # Fill in expected ID
        
        (1, 0): "8a194da9a647fff",  # Fill in expected ID
        # (1, 1) already defined above
        # (1, 2) already defined above
        # (1, 3) already defined above
        (1, 4): "8a194da9a2a7fff",  # Fill in expected ID
        
        (2, 0): "8a194da9a677fff",  # Fill in expected ID
        # (2, 1) already defined above
        # (2, 2) already defined above (center)
        # (2, 3) already defined above
        (2, 4): "8a194da9a39ffff",  # Fill in expected ID
        
        (3, 0): "8a194da9a62ffff",  # Fill in expected ID
        (3, 1): "8a194da9a757fff",  # Fill in expected ID
        # (3, 2) already defined above
        (3, 3): "8a194da9a767fff",  # Fill in expected ID
        (3, 4): "8a194da9a397fff",  # Fill in expected ID
        
        (4, 0): "8a194da9a627fff",  # Fill in expected ID
        (4, 1): "8a194da9a70ffff",  # Fill in expected ID
        (4, 2): "8a194da9a777fff",  # Fill in expected ID
        (4, 3): "8a194da9a0dffff",  # Fill in expected ID
        (4, 4): "8a194da9a0cffff",  # Fill in expected ID
    }
    
    print("\nChecking grid positions:")
    print("------------------------")
    
    all_match = True
    
    # First, print the actual grid for reference
    print("\nActual grid contents:")
    print("-------------------")
    for row in range(height):
        row_values = []
        for col in range(width):
            if grid[row][col]:
                row_values.append(f"({row},{col}): {grid[row][col]}")
        print(", ".join(row_values))
    
    print("\nPosition verification:")
    print("--------------------")
    for (row, col), expected_id in expected_positions.items():
        if 0 <= row < height and 0 <= col < width:
            actual_id = grid[row][col]
            
            # Skip empty expected IDs (to be filled in manually)
            if not expected_id:
                print(f"? Position ({row}, {col}): Expected=<not specified>, Actual={actual_id}")
                continue
                
            match = actual_id == expected_id
            status = "✓" if match else "✗"
            print(f"{status} Position ({row}, {col}): Expected={expected_id}, Actual={actual_id}")
            if not match:
                all_match = False
        else:
            print(f"✗ Position ({row}, {col}) is out of grid bounds")
            all_match = False
    
    print("\nGrid position check:", "PASSED" if all_match else "FAILED")
    return all_match

def draw_hexagon_grid(grid_data):
    """Draw a hexagon grid with IDs in the center of each tile."""
    grid = grid_data["grid"]
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    pentagon_positions = grid_data.get("pentagon_positions", [])
    
    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(15, 12))
    ax.set_aspect('equal')
    
    # Define colors
    normal_color = 'lightblue'
    pentagon_color = 'salmon'
    center_color = 'lightgreen'
    
    # Size of hexagons
    hex_size = 1.0
    
    # Horizontal and vertical spacing
    horiz_spacing = 1.5 * hex_size
    vert_spacing = np.sqrt(3) * hex_size
    
    # Track which positions have pentagons
    pentagon_coords = {tuple(pos) for pos in pentagon_positions}
    
    # Center tile position - now explicitly set to (2,2) as per user's verification
    center_row = 2
    center_col = 2
    
    # Draw hexagons
    for row in range(height):
        for col in range(width):
            if grid[row][col] is None:
                continue
                
            # Calculate position (offset every other row)
            x = col * horiz_spacing
            y = row * vert_spacing
            if col % 2 == 1:
                y += vert_spacing / 2
                
            # Determine color based on type
            if row == center_row and col == center_col:
                color = center_color
            elif (row, col) in pentagon_coords:
                color = pentagon_color
            else:
                color = normal_color
                
            # Create and add the hexagon to the plot - orientation=np.pi/6 for flat bottom
            hexagon = RegularPolygon((x, y), numVertices=6, radius=hex_size,
                                    orientation=np.pi/6, facecolor=color, 
                                    edgecolor='black', alpha=0.7)
            ax.add_patch(hexagon)
            
            # Add the full ID text
            tile_id = grid[row][col]
            # Use smaller font and full ID
            ax.text(x, y, tile_id, ha='center', va='center', fontsize=6)
            
            # Add row, col coordinates for debugging
            ax.text(x, y + 0.3, f"({row},{col})", ha='center', va='center', fontsize=6, color='red')
    
    # Set axis limits with some padding
    ax.set_xlim(-1, width * horiz_spacing + 1)
    ax.set_ylim(-1, height * vert_spacing + 1)
    
    # Remove axis ticks and labels
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add a title
    center_id = grid_data["center_tile_id"]
    ax.set_title(f"Hexagon Grid for Tile: {center_id}")
    
    # Add a legend
    import matplotlib.patches as mpatches
    center_patch = mpatches.Patch(color=center_color, label='Center Tile')
    normal_patch = mpatches.Patch(color=normal_color, label='Regular Hexagon')
    pentagon_patch = mpatches.Patch(color=pentagon_color, label='Pentagon')
    ax.legend(handles=[center_patch, normal_patch, pentagon_patch], loc='upper right')
    
    # Show the plot
    plt.tight_layout()
    plt.savefig('grid_visualization.png')
    print("Visualization saved as 'grid_visualization.png'")
    plt.show()

def main():
    """Main function to fetch and visualize the grid."""
    # Default tile ID and grid dimensions
    tile_id = "8a194da9a74ffff"
    width = 5
    height = 5
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        tile_id = sys.argv[1]
    if len(sys.argv) > 2:
        width = int(sys.argv[2])
    if len(sys.argv) > 3:
        height = int(sys.argv[3])
    
    print(f"Fetching grid for tile: {tile_id}, width: {width}, height: {height}")
    grid_data = fetch_grid_data(tile_id, width, height)
    print("Grid data fetched successfully")
    
    # Verify grid positions
    verify_grid_positions(grid_data)
    
    print("Drawing hexagon grid...")
    draw_hexagon_grid(grid_data)

if __name__ == "__main__":
    main()
