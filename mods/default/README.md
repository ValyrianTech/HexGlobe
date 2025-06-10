# HexGlobe Default Mod

This is the default mod for HexGlobe, which serves as both the fallback experience and a template for creating new mods.

## Structure

```
default/
├── manifest.json       # Mod metadata and configuration
├── css/
│   └── theme.css       # Theme CSS that can be customized
├── js/
│   └── mod.js          # Mod logic and event handlers
└── README.md           # This documentation file
```

## How to Use This as a Template

To create a new mod based on this template:

1. Copy the entire `default` directory to a new directory with your mod name:
   ```
   cp -r mods/default mods/your_mod_name
   ```

2. Edit the `manifest.json` file to update the mod information:
   ```json
   {
     "name": "Your Mod Name",
     "version": "1.0.0",
     "description": "Description of your mod",
     "author": "Your Name",
     "theme": "css/theme.css",
     "script": "js/mod.js"
   }
   ```

3. Customize the `css/theme.css` file to change the visual appearance of hexagons and UI elements.

4. Modify the `js/mod.js` file to implement your mod's game logic and behavior.

5. Access your mod by adding the `mod_name` parameter to the URL:
   ```
   http://localhost:8000/?mod_name=your_mod_name
   ```

## Key Extension Points

The default mod.js file includes several key extension points:

- `initialize()`: Called when the mod is loaded
- `onTileSelected(tileId)`: Called when a tile is selected
- `onTileDeselected(tileId)`: Called when a tile is deselected
- `onActiveTileChanged(tileId)`: Called when the active tile changes
- `onContentChanged(tileId, content)`: Called when a tile's content changes

## API Integration

The mod can interact with the HexGlobe backend API to:

- Load tile data
- Update tile content
- Move content between tiles
- Set visual properties

All API calls will automatically include the `mod_name` parameter based on the URL.

## Example Customization

### Visual Customization

To change the hexagon appearance, modify the CSS variables in `theme.css`:

```css
:root {
    --hex-border-color: #FF0000;
    --hex-fill-color: #FFEEEE;
    --hex-selected-border-color: #00FF00;
}
```

### Behavioral Customization

To implement custom game logic, modify the event handlers in `mod.js`:

```javascript
onTileSelected(tileId) {
    console.log(`Tile selected: ${tileId}`);
    // Your custom game logic here
}
```

## Notes

- The default mod is loaded when no `mod_name` parameter is specified in the URL
- Each mod has its own separate storage for dynamic tile data
- Static H3 grid data is shared across all mods
