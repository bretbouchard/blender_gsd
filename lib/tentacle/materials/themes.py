"""
Tentacle Material Themes

Horror theme presets for procedural tentacle skin materials.
"""

from typing import Dict, Tuple, Any

from .types import (
    MaterialTheme,
    WetnessLevel,
    SSSConfig,
    WetnessConfig,
    VeinConfig,
    RoughnessConfig,
    ThemePreset,
)


# Theme preset definitions
THEME_PRESETS: Dict[MaterialTheme, ThemePreset] = {
    # Rotting - Classic zombie, necrotic flesh
    MaterialTheme.ROTTING: ThemePreset(
        name="Rotting",
        theme=MaterialTheme.ROTTING,
        description="Classic zombie with gray-green necrotic flesh, strong red SSS, yellow-brown slime",
        base_color=(0.42, 0.48, 0.35),  # Gray-green
        sss=SSSConfig(
            radius=2.5,
            color=(1.0, 0.15, 0.15),  # Strong red
            weight=1.0,
            anisotropy=0.2,
            ior=1.4,
        ),
        wetness=WetnessConfig(
            level=WetnessLevel.SLIMY,
            intensity=0.7,
            roughness_modifier=0.4,
            specular_boost=0.6,
            clearcoat=0.2,
        ),
        veins=VeinConfig(
            enabled=True,
            color=(0.3, 0.1, 0.3),  # Dark purple
            density=0.6,
            scale=0.08,
            depth=0.015,
            glow=False,
            glow_color=(0.0, 0.0, 0.0),
            glow_intensity=0.0,
        ),
        roughness=RoughnessConfig(
            base=0.6,
            variation=0.15,
            metallic=0.0,
            normal_strength=0.6,
        ),
        emission_color=(0.0, 0.0, 0.0),
        emission_strength=0.0,
    ),

    # Parasitic - Living, infested flesh
    MaterialTheme.PARASITIC: ThemePreset(
        name="Parasitic",
        theme=MaterialTheme.PARASITIC,
        description="Living infested flesh with pink tones, red veins, clear slime",
        base_color=(0.91, 0.71, 0.72),  # Flesh pink
        sss=SSSConfig(
            radius=1.2,
            color=(1.0, 0.4, 0.4),  # Medium pink
            weight=0.8,
            anisotropy=0.1,
            ior=1.4,
        ),
        wetness=WetnessConfig(
            level=WetnessLevel.MOIST,
            intensity=0.5,
            roughness_modifier=0.25,
            specular_boost=0.4,
            clearcoat=0.1,
        ),
        veins=VeinConfig(
            enabled=True,
            color=(0.8, 0.1, 0.1),  # Red
            density=0.7,
            scale=0.06,
            depth=0.01,
            glow=False,
            glow_color=(0.0, 0.0, 0.0),
            glow_intensity=0.0,
        ),
        roughness=RoughnessConfig(
            base=0.45,
            variation=0.1,
            metallic=0.0,
            normal_strength=0.7,
        ),
        emission_color=(0.0, 0.0, 0.0),
        emission_strength=0.0,
    ),

    # Demonic - Hellish, corrupted
    MaterialTheme.DEMONIC: ThemePreset(
        name="Demonic",
        theme=MaterialTheme.DEMONIC,
        description="Hellish corrupted flesh with deep red base, black veins, black oil",
        base_color=(0.55, 0.0, 0.0),  # Deep red
        sss=SSSConfig(
            radius=2.0,
            color=(1.0, 0.1, 0.1),  # Strong red
            weight=1.0,
            anisotropy=0.3,
            ior=1.4,
        ),
        wetness=WetnessConfig(
            level=WetnessLevel.SLIMY,
            intensity=0.6,
            roughness_modifier=0.35,
            specular_boost=0.5,
            clearcoat=0.3,
        ),
        veins=VeinConfig(
            enabled=True,
            color=(0.1, 0.1, 0.1),  # Black
            density=0.5,
            scale=0.1,
            depth=0.02,
            glow=False,
            glow_color=(0.0, 0.0, 0.0),
            glow_intensity=0.0,
        ),
        roughness=RoughnessConfig(
            base=0.4,
            variation=0.2,
            metallic=0.1,
            normal_strength=0.5,
        ),
        emission_color=(0.0, 0.0, 0.0),
        emission_strength=0.0,
    ),

    # Mutated - Pale, alien, radioactive
    MaterialTheme.MUTATED: ThemePreset(
        name="Mutated",
        theme=MaterialTheme.MUTATED,
        description="Pale alien flesh with bioluminescent veins, green slime, cyan glow",
        base_color=(0.96, 0.90, 0.83),  # Pale flesh
        sss=SSSConfig(
            radius=0.8,
            color=(0.2, 0.8, 0.8),  # Cyan
            weight=0.6,
            anisotropy=0.0,
            ior=1.4,
        ),
        wetness=WetnessConfig(
            level=WetnessLevel.DRIPPING,
            intensity=0.8,
            roughness_modifier=0.5,
            specular_boost=0.7,
            clearcoat=0.4,
        ),
        veins=VeinConfig(
            enabled=True,
            color=(0.2, 0.8, 0.4),  # Bioluminescent
            density=0.4,
            scale=0.07,
            depth=0.01,
            glow=True,
            glow_color=(0.2, 1.0, 0.5),  # Cyan glow
            glow_intensity=0.7,
        ),
        roughness=RoughnessConfig(
            base=0.35,
            variation=0.15,
            metallic=0.05,
            normal_strength=0.8,
        ),
        emission_color=(0.2, 1.0, 0.5),  # Cyan emission
        emission_strength=0.5,
    ),

    # Decayed - Skeletal, ancient
    MaterialTheme.DECAYED: ThemePreset(
        name="Decayed",
        theme=MaterialTheme.DECAYED,
        description="Skeletal ancient appearance with bone white base, no veins, brown ichor",
        base_color=(0.91, 0.89, 0.85),  # Bone white
        sss=SSSConfig(
            radius=0.4,
            color=(0.9, 0.7, 0.7),  # Weak pink
            weight=0.3,
            anisotropy=0.0,
            ior=1.4,
        ),
        wetness=WetnessConfig(
            level=WetnessLevel.MOIST,
            intensity=0.3,
            roughness_modifier=0.15,
            specular_boost=0.2,
            clearcoat=0.0,
        ),
        veins=VeinConfig(
            enabled=False,
            color=(0.0, 0.0, 0.0),
            density=0.0,
            scale=0.1,
            depth=0.0,
            glow=False,
            glow_color=(0.0, 0.0, 0.0),
            glow_intensity=0.0,
        ),
        roughness=RoughnessConfig(
            base=0.7,
            variation=0.2,
            metallic=0.0,
            normal_strength=0.4,
        ),
        emission_color=(0.0, 0.0, 0.0),
        emission_strength=0.0,
    ),
}


def get_theme_preset(theme: MaterialTheme) -> ThemePreset:
    """
    Get a theme preset by theme enum.

    Args:
        theme: The theme to retrieve

    Returns:
        ThemePreset for the requested theme

    Raises:
        KeyError: If theme is not found
    """
    if theme not in THEME_PRESETS:
        raise KeyError(f"Unknown theme: {theme}. Available: {list(THEME_PRESETS.keys())}")

    return THEME_PRESETS[theme]


def get_theme_preset_by_name(name: str) -> ThemePreset:
    """
    Get a theme preset by name string.

    Args:
        name: Theme name (e.g., 'rotting', 'parasitic', 'demonic', 'mutated', 'decayed')

    Returns:
        ThemePreset for the requested theme

    Raises:
        KeyError: If theme name is not found
    """
    # Try to match by name
    for theme, preset in THEME_PRESETS.items():
        if preset.name.lower() == name.lower():
            return preset

    # Try to match by enum value
    try:
        theme_enum = MaterialTheme(name.lower())
        return get_theme_preset(theme_enum)
    except ValueError:
        pass

    raise KeyError(
        f"Unknown theme: {name}. "
        f"Available: {[p.name for p in THEME_PRESETS.values()]}"
    )


def list_theme_presets() -> Dict[str, str]:
    """
    List all available theme presets.

    Returns:
        Dictionary mapping theme names to descriptions
    """
    return {
        preset.name: preset.description
        for preset in THEME_PRESETS.values()
    }


def blend_themes(
    theme1: MaterialTheme,
    theme2: MaterialTheme,
    blend_factor: float = 0.5
) -> ThemePreset:
    """
    Blend two themes together.

    Args:
        theme1: First theme
        theme2: Second theme
        blend_factor: How much to blend (0.0 = all theme1, 1.0 = all theme2)

    Returns:
        New ThemePreset with blended values
    """
    if blend_factor <= 0.0:
        return get_theme_preset(theme1)
    if blend_factor >= 1.0:
        return get_theme_preset(theme2)

    preset1 = get_theme_preset(theme1)
    preset2 = get_theme_preset(theme2)

    def lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    return ThemePreset(
        name=f"{preset1.name}_{preset2.name}_Blend",
        theme=theme1,  # Use first theme as primary
        description=f"Blend of {preset1.name} and {preset2.name}",
        base_color=tuple(
            lerp(c1, c2, blend_factor)
            for c1, c2 in zip(preset1.base_color, preset2.base_color)
        ),
        sss=SSSConfig(
            radius=lerp(preset1.sss.radius, preset2.sss.radius, blend_factor),
            color=tuple(
                lerp(c1, c2, blend_factor)
                for c1, c2 in zip(preset1.sss.color, preset2.sss.color)
            ),
            weight=lerp(preset1.sss.weight, preset2.sss.weight, blend_factor),
            anisotropy=lerp(preset1.sss.anisotropy, preset2.sss.anisotropy, blend_factor),
            ior=lerp(preset1.sss.ior, preset2.sss.ior, blend_factor),
        ),
        wetness=WetnessConfig(
            level=preset1.wetness.level if blend_factor < 0.5 else preset2.wetness.level,
            intensity=lerp(preset1.wetness.intensity, preset2.wetness.intensity, blend_factor),
            roughness_modifier=lerp(preset1.wetness.roughness_modifier, preset2.wetness.roughness_modifier, blend_factor),
            specular_boost=lerp(preset1.wetness.specular_boost, preset2.wetness.specular_boost, blend_factor),
            clearcoat=lerp(preset1.wetness.clearcoat, preset2.wetness.clearcoat, blend_factor),
        ),
        veins=VeinConfig(
            enabled=preset1.veins.enabled or preset2.veins.enabled,
            color=tuple(
                lerp(c1, c2, blend_factor)
                for c1, c2 in zip(preset1.veins.color, preset2.veins.color)
            ) if preset1.veins.enabled or preset2.veins.enabled else (0.0, 0.0, 0.0),
            density=lerp(preset1.veins.density, preset2.veins.density, blend_factor),
            scale=lerp(preset1.veins.scale, preset2.veins.scale, blend_factor),
            depth=lerp(preset1.veins.depth, preset2.veins.depth, blend_factor),
            glow=preset1.veins.glow or preset2.veins.glow,
            glow_color=tuple(
                lerp(c1, c2, blend_factor)
                for c1, c2 in zip(preset1.veins.glow_color, preset2.veins.glow_color)
            ),
            glow_intensity=lerp(preset1.veins.glow_intensity, preset2.veins.glow_intensity, blend_factor),
        ),
        roughness=RoughnessConfig(
            base=lerp(preset1.roughness.base, preset2.roughness.base, blend_factor),
            variation=lerp(preset1.roughness.variation, preset2.roughness.variation, blend_factor),
            metallic=lerp(preset1.roughness.metallic, preset2.roughness.metallic, blend_factor),
            normal_strength=lerp(preset1.roughness.normal_strength, preset2.roughness.normal_strength, blend_factor),
        ),
        emission_color=tuple(
            lerp(c1, c2, blend_factor)
            for c1, c2 in zip(preset1.emission_color, preset2.emission_color)
        ),
        emission_strength=lerp(preset1.emission_strength, preset2.emission_strength, blend_factor),
    )
