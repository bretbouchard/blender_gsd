"""MSG 1998 - Color Grading"""
from .types import ColorGradeConfig

def apply_color_grade(image, config: ColorGradeConfig = None):
    """Apply color grading with LUT."""
    if config is None:
        config = ColorGradeConfig()
    return {"lut": config.lut_path}

def create_kodak_lut_node(tree, lut_path):
    """Create Color Balance node with Kodak LUT."""
    return {"node_type": "color_balance", "lut": str(lut_path)}
