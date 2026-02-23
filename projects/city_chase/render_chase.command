#!/bin/bash
# Quick render script - opens Blender with the chase scene loaded
# Then just press Ctrl+F12 (Cmd+F12 on Mac) to render

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Opening Blender with 30-second chase scene..."
echo ""
echo "INSTRUCTIONS:"
echo "1. Wait for scene to load"
echo "2. Press SPACE to preview animation in viewport"
echo "3. Press Ctrl+F12 (or Cmd+F12 on Mac) to render animation"
echo "4. Output will be saved to /tmp/chase_output/"
echo ""

# Open Blender with the script
blender --python "$SCRIPT_DIR/30_second_chase.py"
