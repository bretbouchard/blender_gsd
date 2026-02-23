"""
Style Manager

Manages style consistency across scene generation.
Defines style presets and ensures visual coherence.

Implements REQ-SO-06: Style Consistency.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class StyleCategory(Enum):
    """Style category classification."""
    REALISTIC = "realistic"
    STYLIZED = "stylized"
    CARTOON = "cartoon"
    ABSTRACT = "abstract"
    RETRO = "retro"
    FUTURISTIC = "futuristic"


@dataclass
class StyleProfile:
    """
    Complete style profile for scene generation.

    Attributes:
        style_id: Unique style identifier
        name: Style name
        category: Style category
        material_style: Material rendering style
        lighting_style: Lighting approach
        color_palette: Color palette (hex colors)
        texture_intensity: Texture detail level (0-1)
        geometry_detail: Geometry complexity (0-1)
        post_processing: Post-processing effects
        compatible_styles: Other compatible styles
    """
    style_id: str = ""
    name: str = ""
    category: str = "realistic"
    material_style: str = "pbr"
    lighting_style: str = "realistic"
    color_palette: List[str] = field(default_factory=list)
    texture_intensity: float = 1.0
    geometry_detail: float = 1.0
    post_processing: List[str] = field(default_factory=list)
    compatible_styles: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "style_id": self.style_id,
            "name": self.name,
            "category": self.category,
            "material_style": self.material_style,
            "lighting_style": self.lighting_style,
            "color_palette": self.color_palette,
            "texture_intensity": self.texture_intensity,
            "geometry_detail": self.geometry_detail,
            "post_processing": self.post_processing,
            "compatible_styles": self.compatible_styles,
        }


# =============================================================================
# STYLE PROFILES
# =============================================================================

STYLE_PROFILES: Dict[str, StyleProfile] = {
    "photorealistic": StyleProfile(
        style_id="photorealistic",
        name="Photorealistic",
        category="realistic",
        material_style="pbr",
        lighting_style="physically_based",
        color_palette=["#FFFFFF", "#F5F5F5", "#333333", "#1A1A1A"],
        texture_intensity=1.0,
        geometry_detail=1.0,
        post_processing=["color_grading", "chromatic_aberration"],
        compatible_styles=["minimalist"],
    ),
    "stylized": StyleProfile(
        style_id="stylized",
        name="Stylized",
        category="stylized",
        material_style="toon",
        lighting_style="artistic",
        color_palette=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"],
        texture_intensity=0.5,
        geometry_detail=0.7,
        post_processing=["outline", "cel_shading"],
        compatible_styles=["cartoon", "minimalist"],
    ),
    "cartoon": StyleProfile(
        style_id="cartoon",
        name="Cartoon",
        category="cartoon",
        material_style="toon",
        lighting_style="flat",
        color_palette=["#FF0000", "#00FF00", "#0000FF", "#FFFF00"],
        texture_intensity=0.2,
        geometry_detail=0.5,
        post_processing=["outline", "cel_shading", "posterize"],
        compatible_styles=["stylized"],
    ),
    "low_poly": StyleProfile(
        style_id="low_poly",
        name="Low Poly",
        category="stylized",
        material_style="flat",
        lighting_style="ambient",
        color_palette=["#E8E8E8", "#B8D4E3", "#F7DC6F", "#82E0AA"],
        texture_intensity=0.0,
        geometry_detail=0.3,
        post_processing=["ambient_occlusion"],
        compatible_styles=["minimalist", "stylized"],
    ),
    "retro": StyleProfile(
        style_id="retro",
        name="Retro",
        category="retro",
        material_style="flat",
        lighting_style="dramatic",
        color_palette=["#FF6B35", "#F7C59F", "#EFEFD0", "#004E89"],
        texture_intensity=0.7,
        geometry_detail=0.8,
        post_processing=["film_grain", "vignette", "color_grade_vintage"],
        compatible_styles=["stylized"],
    ),
    "sci_fi": StyleProfile(
        style_id="sci_fi",
        name="Sci-Fi",
        category="futuristic",
        material_style="metallic",
        lighting_style="neon",
        color_palette=["#00FFFF", "#FF00FF", "#00FF00", "#1A1A2E"],
        texture_intensity=0.8,
        geometry_detail=0.9,
        post_processing=["bloom", "glow", "chromatic_aberration"],
        compatible_styles=["futuristic"],
    ),
    "fantasy": StyleProfile(
        style_id="fantasy",
        name="Fantasy",
        category="stylized",
        material_style="painted",
        lighting_style="magical",
        color_palette=["#9B59B6", "#3498DB", "#E74C3C", "#F39C12"],
        texture_intensity=0.8,
        geometry_detail=0.9,
        post_processing=["bloom", "god_rays"],
        compatible_styles=["stylized", "retro"],
    ),
    "minimalist": StyleProfile(
        style_id="minimalist",
        name="Minimalist",
        category="realistic",
        material_style="flat",
        lighting_style="soft",
        color_palette=["#FFFFFF", "#000000", "#808080"],
        texture_intensity=0.1,
        geometry_detail=0.4,
        post_processing=[],
        compatible_styles=["photorealistic", "low_poly"],
    ),
}


class StyleManager:
    """
    Manages style consistency across scene.

    Usage:
        manager = StyleManager()
        profile = manager.get_profile("photorealistic")
        is_compatible = manager.check_compatibility("photorealistic", "stylized")
    """

    def __init__(self):
        """Initialize style manager."""
        self.profiles = STYLE_PROFILES

    def get_profile(self, style_id: str) -> Optional[StyleProfile]:
        """Get style profile by ID."""
        return self.profiles.get(style_id)

    def list_styles(self) -> List[str]:
        """List all available style IDs."""
        return list(self.profiles.keys())

    def check_compatibility(
        self,
        style1: str,
        style2: str,
    ) -> bool:
        """Check if two styles are compatible."""
        profile1 = self.get_profile(style1)
        profile2 = self.get_profile(style2)

        if not profile1 or not profile2:
            return False

        # Same style is always compatible
        if style1 == style2:
            return True

        # Check if style2 is in style1's compatible list
        if style2 in profile1.compatible_styles:
            return True

        # Check if style1 is in style2's compatible list
        if style1 in profile2.compatible_styles:
            return True

        # Check if same category
        if profile1.category == profile2.category:
            return True

        return False

    def get_compatible_styles(self, style_id: str) -> List[str]:
        """Get all styles compatible with given style."""
        compatible = []
        for other_id in self.profiles:
            if self.check_compatibility(style_id, other_id):
                compatible.append(other_id)
        return compatible

    def suggest_asset_style(
        self,
        scene_style: str,
        asset_styles: List[str],
    ) -> Optional[str]:
        """Suggest best asset style for scene."""
        scene_profile = self.get_profile(scene_style)
        if not scene_profile:
            return asset_styles[0] if asset_styles else None

        # Prefer exact match
        if scene_style in asset_styles:
            return scene_style

        # Find compatible match
        for asset_style in asset_styles:
            if self.check_compatibility(scene_style, asset_style):
                return asset_style

        # Fall back to first available
        return asset_styles[0] if asset_styles else None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "StyleCategory",
    "StyleProfile",
    "STYLE_PROFILES",
    "StyleManager",
]
