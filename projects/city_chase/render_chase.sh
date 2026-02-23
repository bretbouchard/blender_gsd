#!/bin/bash
# Render the 30-second car chase
# Usage: ./render_chase.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BLEND_FILE="$SCRIPT_DIR/chase_30sec.blend"
OUTPUT_DIR="$SCRIPT_DIR/output"

echo "========================================"
echo "30-SECOND CAR CHASE RENDER"
echo "========================================"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if blend file exists, if not create it
if [ ! -f "$BLEND_FILE" ]; then
    echo "Creating blend file..."
    blender -b --python "$SCRIPT_DIR/30_second_chase.py" -- -S
    # Save the file
    blender -b --python "$SCRIPT_DIR/30_second_chase.py" -- --save "$BLEND_FILE"
fi

echo ""
echo "Rendering 720 frames @ 24fps (30 seconds)..."
echo "Output: $OUTPUT_DIR/chase_####.mp4"
echo ""
echo "This will take approximately 15-30 minutes depending on your hardware."
echo ""

# Render
blender -b "$BLEND_FILE" \
    -o "$OUTPUT_DIR/chase_" \
    -F MPEG \
    -s 1 -e 720 \
    -a

echo ""
echo "========================================"
echo "RENDER COMPLETE!"
echo "Output: $OUTPUT_DIR/chase_0001-0720.mp4"
echo "========================================"
