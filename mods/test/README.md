# Test Mod for HexGlobe

This is a test mod with distinctive visual styles for testing the mod system. It features a purple and coral color scheme that is visibly different from the default mod.

## Purpose

This mod serves as a test case for the HexGlobe mod system, allowing developers to verify that:

1. The mod loader correctly loads different mods based on URL parameters
2. Visual styles are properly applied from the mod's CSS
3. JavaScript functionality is loaded and executed correctly
4. API calls include the correct mod_name parameter

## Usage

To use this mod, add the `mod_name=test` parameter to your URL:

```
http://localhost:8080/?mod_name=test
```

## Features

- Purple and coral color scheme
- Custom UI elements in the debug panel
- Visual indicators for selected tiles
- Test mod information display

## Implementation Details

- **CSS**: Custom theme with purple borders and light blue backgrounds
- **JavaScript**: Custom event handlers and UI elements
- **API Integration**: All API calls include the mod_name parameter

## Testing

This mod is designed to be visually distinct from the default mod, making it easy to confirm that the mod system is working correctly.
