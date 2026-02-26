"""
Tentacle Materials Package

Procedural skin materials with horror themes for tentacle system.
"""

from .types import (
    # Enums
    MaterialTheme,
    WetnessLevel,
    # Config dataclasses
    SSSConfig,
    WetnessConfig,
    VeinConfig,
    RoughnessConfig,
    MaterialZone,
    ThemePreset,
    TentacleMaterialConfig,
    BakeConfig,
    BakeResult,
)

from .themes import (
    THEME_PRESETS,
    get_theme_preset,
    get_theme_preset_by_name,
    list_theme_presets,
    blend_themes,
)

from .skin import (
    SkinShaderGenerator,
    create_skin_material,
)

from .veins import (
    VeinPatternGenerator,
    create_bioluminescent_pattern,
)

from .baking import (
    TextureBaker,
    bake_material,
    bake_all_lods,
)

from .presets import (
    MaterialPresetLoader,
    load_theme_preset,
    load_material_config,
    load_bake_config,
    list_theme_presets as list_yaml_theme_presets,
    list_material_configs,
    clear_cache,
)


__all__ = [
    # Enums
    "MaterialTheme",
    "WetnessLevel",
    # Config dataclasses
    "SSSConfig",
    "WetnessConfig",
    "VeinConfig",
    "RoughnessConfig",
    "MaterialZone",
    "ThemePreset",
    "TentacleMaterialConfig",
    "BakeConfig",
    "BakeResult",
    # Theme presets
    "THEME_PRESETS",
    "get_theme_preset",
    "get_theme_preset_by_name",
    "list_theme_presets",
    "blend_themes",
    # Skin shader
    "SkinShaderGenerator",
    "create_skin_material",
    # Vein patterns
    "VeinPatternGenerator",
    "create_bioluminescent_pattern",
    # Baking
    "TextureBaker",
    "bake_material",
    "bake_all_lods",
    # Preset loading
    "MaterialPresetLoader",
    "load_theme_preset",
    "load_material_config",
    "load_bake_config",
    "list_yaml_theme_presets",
    "list_material_configs",
    "clear_cache",
]


# Convenience functions

def create_horror_material(
    theme: MaterialTheme,
    name: str = "TentacleMaterial",
    wetness_multiplier: float = 1.0,
) -> SkinShaderGenerator:
    """
    Create a horror-themed skin material.

    Args:
        theme: Horror theme preset
        name: Material name
        wetness_multiplier: Wetness intensity multiplier

    Returns:
        Configured SkinShaderGenerator
    """
    preset = get_theme_preset(theme)
    config = TentacleMaterialConfig(
        name=name,
        theme_preset=preset,
        global_wetness_multiplier=wetness_multiplier,
    )
    return SkinShaderGenerator(config)


def create_zombie_tentacle_material() -> SkinShaderGenerator:
    """
    Create default zombie tentacle material (rotting theme).

    Returns:
        Configured SkinShaderGenerator with rotting theme
    """
    return create_horror_material(MaterialTheme.ROTTING, "ZombieTentacle")


def create_parasite_tentacle_material() -> SkinShaderGenerator:
    """
    Create parasite tentacle material.

    Returns:
        Configured SkinShaderGenerator with parasitic theme
    """
    return create_horror_material(MaterialTheme.PARASITIC, "ParasiteTentacle")


def create_demon_tentacle_material() -> SkinShaderGenerator:
    """
    Create demon tentacle material.

    Returns:
        Configured SkinShaderGenerator with demonic theme
    """
    return create_horror_material(MaterialTheme.DEMONIC, "DemonTentacle")


def create_mutated_tentacle_material() -> SkinShaderGenerator:
    """
    Create mutated/alien tentacle material with bioluminescence.

    Returns:
        Configured SkinShaderGenerator with mutated theme
    """
    return create_horror_material(MaterialTheme.MUTATED, "MutatedTentacle")


# Add convenience functions to exports
__all__.extend([
    "create_horror_material",
    "create_zombie_tentacle_material",
    "create_parasite_tentacle_material",
    "create_demon_tentacle_material",
    "create_mutated_tentacle_material",
])
