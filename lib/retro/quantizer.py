"""
Color Quantization for Pixel Art

Advanced color quantization algorithms for reducing image colors
while preserving visual quality.

Methods:
- median_cut: Classic fast algorithm
- kmeans: K-means clustering (slower, better quality)
- octree: Octree quantization (fast, good quality)
- palette_match: Match to specific palette
"""

from __future__ import annotations
from typing import Tuple, List, Optional, Any, Dict
import time
import math

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def quantize_colors(
    image: Any,
    color_count: int,
    method: str = "median_cut"
) -> Any:
    """
    Reduce image to specified number of colors.

    Args:
        image: PIL Image to quantize
        color_count: Maximum number of colors
        method: Quantization method (median_cut, kmeans, octree)

    Returns:
        PIL Image with reduced colors
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    # Convert to RGB if needed
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    if method == "median_cut":
        return median_cut_quantize(image, color_count)
    elif method == "kmeans":
        return kmeans_quantize(image, color_count)
    elif method == "octree":
        return octree_quantize(image, color_count)
    else:
        # Default to PIL's built-in
        return image.quantize(colors=color_count, method=Image.MEDIANCUT)


def quantize_to_palette(
    image: Any,
    palette: List[Tuple[int, int, int]]
) -> Any:
    """
    Reduce image to specific palette.

    Args:
        image: PIL Image to quantize
        palette: List of RGB color tuples

    Returns:
        PIL Image quantized to palette
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    if not palette:
        return image

    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    if HAS_NUMPY:
        return _fast_palette_match(image, palette)
    else:
        return _slow_palette_match(image, palette)


def extract_palette(
    image: Any,
    count: int = 16,
    method: str = "median_cut"
) -> List[Tuple[int, int, int]]:
    """
    Extract dominant colors from image.

    Args:
        image: PIL Image to analyze
        count: Number of colors to extract
        method: Extraction method

    Returns:
        List of RGB color tuples
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required for image processing")

    if isinstance(image, str):
        image = Image.open(image)

    # Convert to RGB if needed
    if image.mode != "RGB":
        image = image.convert("RGB")

    if method == "median_cut":
        return _median_cut_extract(image, count)
    elif method == "kmeans" and HAS_NUMPY:
        return _kmeans_extract(image, count)
    else:
        # Fallback to PIL quantization
        quantized = image.quantize(colors=count, method=Image.MEDIANCUT)
        palette = quantized.getpalette()
        if palette is None:
            return []

        colors = []
        for i in range(count):
            r = palette[i * 3]
            g = palette[i * 3 + 1]
            b = palette[i * 3 + 2]
            colors.append((r, g, b))

        return colors


# =============================================================================
# Median Cut Quantization
# =============================================================================

def median_cut_quantize(image: Any, num_colors: int) -> Any:
    """
    Median cut color quantization.

    Divides the color space into boxes and averages colors within each box.

    Args:
        image: PIL Image to quantize
        num_colors: Target number of colors

    Returns:
        Quantized PIL Image
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required")

    palette = _median_cut_extract(image, num_colors)
    return quantize_to_palette(image, palette)


def _median_cut_extract(image: Any, num_colors: int) -> List[Tuple[int, int, int]]:
    """Extract palette using median cut algorithm."""
    if not HAS_NUMPY:
        # Fallback to PIL
        quantized = image.quantize(colors=num_colors, method=Image.MEDIANCUT)
        palette = quantized.getpalette()
        if palette is None:
            return [(128, 128, 128)]
        return [(palette[i*3], palette[i*3+1], palette[i*3+2]) for i in range(num_colors)]

    # Get pixel data
    img_array = np.array(image)
    pixels = img_array.reshape(-1, 3)

    # Build color boxes
    class ColorBox:
        def __init__(self, colors):
            self.colors = colors
            self._get_min_max()

        def _get_min_max(self):
            if len(self.colors) == 0:
                self.min_channel = np.array([0, 0, 0])
                self.max_channel = np.array([255, 255, 255])
                return
            self.min_channel = np.min(self.colors, axis=0)
            self.max_channel = np.max(self.colors, axis=0)

        def largest_dimension(self):
            return np.argmax(self.max_channel - self.min_channel)

        def split(self):
            dim = self.largest_dimension()
            values = self.colors[:, dim]
            median = np.median(values)

            left = self.colors[values <= median]
            right = self.colors[values > median]

            return ColorBox(left), ColorBox(right)

        def average_color(self):
            if len(self.colors) == 0:
                return (128, 128, 128)
            avg = np.mean(self.colors, axis=0).astype(int)
            return tuple(avg)

    # Start with all pixels in one box
    boxes = [ColorBox(pixels)]

    # Split until we have enough boxes
    while len(boxes) < num_colors:
        # Find box with largest range
        max_range = -1
        split_idx = 0

        for i, box in enumerate(boxes):
            if len(box.colors) > 1:
                range_val = np.max(box.max_channel - box.min_channel)
                if range_val > max_range:
                    max_range = range_val
                    split_idx = i

        if max_range <= 0:
            break

        # Split the box
        left, right = boxes[split_idx].split()
        boxes.pop(split_idx)

        if len(left.colors) > 0:
            boxes.append(left)
        if len(right.colors) > 0:
            boxes.append(right)

    # Get average colors
    return [box.average_color() for box in boxes]


# =============================================================================
# K-Means Quantization
# =============================================================================

def kmeans_quantize(
    image: Any,
    num_colors: int,
    max_iterations: int = 20,
    tolerance: float = 1.0
) -> Any:
    """
    K-means color quantization.

    Iteratively clusters colors to find optimal palette.

    Args:
        image: PIL Image to quantize
        num_colors: Target number of colors
        max_iterations: Maximum iterations
        tolerance: Convergence tolerance

    Returns:
        Quantized PIL Image
    """
    if not HAS_PIL or not HAS_NUMPY:
        raise ImportError("PIL/Pillow and numpy are required for k-means")

    palette = _kmeans_extract(image, num_colors, max_iterations, tolerance)
    return quantize_to_palette(image, palette)


def _kmeans_extract(
    image: Any,
    num_colors: int,
    max_iterations: int = 20,
    tolerance: float = 1.0
) -> List[Tuple[int, int, int]]:
    """Extract palette using k-means clustering."""
    # Get pixel data
    img_array = np.array(image)
    pixels = img_array.reshape(-1, 3).astype(np.float32)

    # Initialize centroids randomly
    np.random.seed(42)  # For reproducibility
    indices = np.random.choice(len(pixels), num_colors, replace=False)
    centroids = pixels[indices].copy()

    for _ in range(max_iterations):
        # Assign pixels to nearest centroid
        distances = np.sqrt(((pixels[:, np.newaxis] - centroids) ** 2).sum(axis=2))
        labels = np.argmin(distances, axis=1)

        # Update centroids
        new_centroids = np.zeros_like(centroids)
        for k in range(num_colors):
            mask = labels == k
            if np.any(mask):
                new_centroids[k] = pixels[mask].mean(axis=0)
            else:
                new_centroids[k] = centroids[k]

        # Check convergence
        shift = np.sqrt(((new_centroids - centroids) ** 2).sum(axis=1)).max()
        centroids = new_centroids

        if shift < tolerance:
            break

    # Convert to integer tuples
    return [tuple(c.astype(int)) for c in centroids]


# =============================================================================
# Octree Quantization
# =============================================================================

class OctreeNode:
    """Node in an octree for color quantization."""

    def __init__(self, level: int, parent: Optional['OctreeNode'] = None):
        self.level = level
        self.parent = parent
        self.children: List[Optional['OctreeNode']] = [None] * 8
        self.pixel_count = 0
        self.red_sum = 0
        self.green_sum = 0
        self.blue_sum = 0
        self.is_leaf = level == 7

    def get_child_index(self, r: int, g: int, b: int) -> int:
        """Get child index for a color."""
        index = 0
        if r & (1 << (7 - self.level)):
            index |= 1
        if g & (1 << (7 - self.level)):
            index |= 2
        if b & (1 << (7 - self.level)):
            index |= 4
        return index

    def add_color(self, r: int, g: int, b: int, max_level: int = 7):
        """Add a color to the tree."""
        if self.is_leaf or self.level >= max_level:
            self.pixel_count += 1
            self.red_sum += r
            self.green_sum += g
            self.blue_sum += b
            self.is_leaf = True
            return

        index = self.get_child_index(r, g, b)
        if self.children[index] is None:
            self.children[index] = OctreeNode(self.level + 1, self)

        self.children[index].add_color(r, g, b, max_level)  # type: ignore

    def get_color(self) -> Tuple[int, int, int]:
        """Get average color for this node."""
        if self.pixel_count == 0:
            return (0, 0, 0)
        return (
            self.red_sum // self.pixel_count,
            self.green_sum // self.pixel_count,
            self.blue_sum // self.pixel_count,
        )

    def get_leaf_count(self) -> int:
        """Count leaf nodes."""
        if self.is_leaf:
            return 1
        return sum(child.get_leaf_count() for child in self.children if child is not None)

    def collect_leaves(self) -> List['OctreeNode']:
        """Collect all leaf nodes."""
        if self.is_leaf:
            return [self]

        leaves = []
        for child in self.children:
            if child is not None:
                leaves.extend(child.collect_leaves())
        return leaves


def octree_quantize(image: Any, num_colors: int) -> Any:
    """
    Octree color quantization.

    Uses an octree data structure for fast, high-quality quantization.

    Args:
        image: PIL Image to quantize
        num_colors: Target number of colors

    Returns:
        Quantized PIL Image
    """
    if not HAS_PIL:
        raise ImportError("PIL/Pillow is required")

    palette = _octree_extract(image, num_colors)
    return quantize_to_palette(image, palette)


def _octree_extract(image: Any, num_colors: int) -> List[Tuple[int, int, int]]:
    """Extract palette using octree algorithm."""
    # Build octree
    root = OctreeNode(0)

    width, height = image.size
    pixels = image.load()

    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if isinstance(pixel, int):
                pixel = (pixel, pixel, pixel)
            root.add_color(pixel[0], pixel[1], pixel[2])

    # Collect leaves and reduce if needed
    leaves = root.collect_leaves()

    # If too many leaves, sort by pixel count and take top N
    if len(leaves) > num_colors:
        leaves.sort(key=lambda n: n.pixel_count, reverse=True)
        leaves = leaves[:num_colors]

    # Get colors
    return [leaf.get_color() for leaf in leaves]


# =============================================================================
# Nearest Color Matching
# =============================================================================

def nearest_color_match(
    image: Any,
    palette: List[Tuple[int, int, int]]
) -> Any:
    """
    Match each pixel to nearest palette color.

    Args:
        image: PIL Image to process
        palette: List of RGB color tuples

    Returns:
        PIL Image with colors matched to palette
    """
    return quantize_to_palette(image, palette)


def _fast_palette_match(image: Any, palette: List[Tuple[int, int, int]]) -> Any:
    """Fast numpy-based palette matching."""
    img_array = np.array(image)
    pixels = img_array.reshape(-1, 3)

    palette_array = np.array(palette)

    # Calculate distances
    distances = np.sqrt(((pixels[:, np.newaxis] - palette_array) ** 2).sum(axis=2))

    # Find nearest
    nearest_indices = np.argmin(distances, axis=1)

    # Map to colors
    new_pixels = palette_array[nearest_indices]
    new_array = new_pixels.reshape(img_array.shape)

    return Image.fromarray(new_array.astype(np.uint8))


def _slow_palette_match(image: Any, palette: List[Tuple[int, int, int]]) -> Any:
    """Slow pixel-by-pixel palette matching."""
    width, height = image.size
    pixels = image.load()

    result = Image.new("RGB", (width, height))
    result_pixels = result.load()

    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if isinstance(pixel, int):
                pixel = (pixel, pixel, pixel)

            min_dist = float('inf')
            nearest = palette[0]

            for color in palette:
                dist = sum((a - b) ** 2 for a, b in zip(pixel[:3], color))
                if dist < min_dist:
                    min_dist = dist
                    nearest = color

            result_pixels[x, y] = nearest

    return result


# =============================================================================
# Utility Functions
# =============================================================================

def build_weighted_palette(
    image: Any,
    num_colors: int,
    saturation_weight: float = 1.0,
    brightness_weight: float = 1.0
) -> List[Tuple[int, int, int]]:
    """
    Build a palette weighted by color properties.

    Prioritizes saturated and bright colors for more vibrant pixel art.

    Args:
        image: PIL Image to analyze
        num_colors: Target number of colors
        saturation_weight: Weight for saturation (0-1)
        brightness_weight: Weight for brightness (0-1)

    Returns:
        List of RGB color tuples
    """
    if not HAS_PIL or not HAS_NUMPY:
        return extract_palette(image, num_colors)

    # Get base palette
    base_palette = _kmeans_extract(image, num_colors * 2)

    # Calculate scores for each color
    scored = []
    for color in base_palette:
        r, g, b = color

        # Calculate saturation (from HSB/HSV)
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        saturation = 0 if max_val == 0 else (max_val - min_val) / max_val

        # Calculate brightness
        brightness = max_val / 255.0

        # Calculate score
        score = (saturation * saturation_weight + brightness * brightness_weight) / 2
        scored.append((color, score))

    # Sort by score and take top colors
    scored.sort(key=lambda x: x[1], reverse=True)
    return [c[0] for c in scored[:num_colors]]


def count_colors(image: Any) -> int:
    """
    Count unique colors in image.

    Args:
        image: PIL Image to analyze

    Returns:
        Number of unique colors
    """
    if not HAS_PIL:
        return 0

    if isinstance(image, str):
        image = Image.open(image)

    colors = image.getcolors(maxcolors=1000000)
    if colors is None:
        if HAS_NUMPY:
            arr = np.array(image)
            if len(arr.shape) == 3:
                return len(np.unique(arr.reshape(-1, arr.shape[2]), axis=0))
            return len(np.unique(arr))
        return 0

    return len(colors)


def get_color_histogram(
    image: Any,
    max_colors: int = 256
) -> Dict[Tuple[int, int, int], int]:
    """
    Get color frequency histogram.

    Args:
        image: PIL Image to analyze
        max_colors: Maximum colors to count

    Returns:
        Dictionary mapping RGB color to count
    """
    if not HAS_PIL:
        return {}

    if isinstance(image, str):
        image = Image.open(image)

    if image.mode != "RGB":
        image = image.convert("RGB")

    colors = image.getcolors(maxcolors=max_colors)
    if colors is None:
        return {}

    return {color: count for count, color in colors}
