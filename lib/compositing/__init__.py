"""
Compositing Module

Provides compositing systems for multi-pass rendering, cryptomatte
extraction, and post-processing chains.

Implements REQ-CP-01: Cryptomatte Pass System.
Implements REQ-CP-02: Multi-Pass Render Pipeline.
Implements REQ-CP-03: EXR Output Strategy.
Implements REQ-CP-04: Post-Processing Chain.
"""

from .cryptomatte import (
    # Enums
    CryptomatteLayer,
    MatteType,
    # Data classes
    CryptomatteConfig,
    CryptomattePass,
    MatteData,
    # Classes
    CryptomatteManager,
    # Functions
    create_cryptomatte_config,
    extract_matte_from_manifest,
)

from .multi_pass import (
    # Enums
    PassType,
    PassCategory,
    OutputFormat,
    # Data classes
    RenderPass,
    PassConfig,
    MultiPassSetup,
    # Constants
    STANDARD_PASSES,
    BEAUTY_PASSES,
    UTILITY_PASSES,
    DATA_PASSES,
    # Classes
    MultiPassManager,
    # Functions
    create_pass_config,
    create_standard_setup,
)

from .post_process import (
    # Enums
    EffectType,
    ColorSpace,
    ToneMapper,
    # Data classes
    PostEffect,
    ColorGradeConfig,
    PostProcessChain,
    # Constants
    DEFAULT_COLOR_GRADE,
    GLARE_PRESETS,
    COLOR_CORRECTION_DEFAULTS,
    # Classes
    PostProcessManager,
    # Functions
    create_color_grade,
    create_glare_effect,
    create_film_grain,
)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Cryptomatte
    "CryptomatteLayer",
    "MatteType",
    "CryptomatteConfig",
    "CryptomattePass",
    "MatteData",
    "CryptomatteManager",
    "create_cryptomatte_config",
    "extract_matte_from_manifest",

    # Multi-Pass
    "PassType",
    "PassCategory",
    "OutputFormat",
    "RenderPass",
    "PassConfig",
    "MultiPassSetup",
    "STANDARD_PASSES",
    "BEAUTY_PASSES",
    "UTILITY_PASSES",
    "DATA_PASSES",
    "MultiPassManager",
    "create_pass_config",
    "create_standard_setup",

    # Post-Process
    "EffectType",
    "ColorSpace",
    "ToneMapper",
    "PostEffect",
    "ColorGradeConfig",
    "PostProcessChain",
    "DEFAULT_COLOR_GRADE",
    "GLARE_PRESETS",
    "COLOR_CORRECTION_DEFAULTS",
    "PostProcessManager",
    "create_color_grade",
    "create_glare_effect",
    "create_film_grain",
]
