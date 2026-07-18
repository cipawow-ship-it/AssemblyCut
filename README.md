# AssemblyCut

Cut multiple **PartDesign::Body** objects in an assembly with a single sketch.

## Features

- **Auto-detection**: Automatically detects which bodies are intersected by the sketch
- **Reorder**: Arrow buttons to change the order of bodies
- **Per-body control**: Each body opens its own FreeCAD Pocket dialog
- **Full parameters**: Set depth, taper, direction, through-all for each body independently
- **PartDesign native**: Works entirely within the PartDesign workbench

## Installation

### FreeCAD Addon Manager

1. Open FreeCAD
2. Go to **Tools → Addon Manager**
3. Search for **AssemblyCut**
4. Click **Install**
5. Restart FreeCAD

### Manual Installation

1. Download or clone this repository
2. Copy the `AssemblyCut` folder into your FreeCAD Mod directory:
   - **Windows**: `%APPDATA%\FreeCAD\v1-1\Mod\`
   - **Linux**: `~/.local/share/FreeCAD/v1-1/Mod/`
   - **macOS**: `~/Library/Application Support/FreeCAD/v1-1/Mod/`
3. Restart FreeCAD

## Usage

1. Open an assembly with PartDesign::Body objects
2. Create a sketch on any plane (this is the cutting profile)
3. **Select the sketch** in the model
4. Press the **AssemblyCut** button in the PartDesign toolbar
5. A dialog shows all bodies in the document:
   - Bodies hit by the sketch are **pre-selected** and listed first
   - Use **arrows** next to each body to reorder
   - Check/uncheck bodies as needed
6. Press **Cut Bodies**
7. A **FreeCAD Pocket dialog** opens for each selected body
   - Set depth, taper, direction, etc.
   - Press OK to confirm and move to the next body
8. After all bodies are processed, each Pocket is ready
   - Double-click any Pocket in the tree to adjust it later

## Requirements

- FreeCAD 1.1 or later
- No external dependencies

## License

LGPL-2.1-or-later
