"""MSG 1998 - Film Look Post-Processing"""
from .types import FilmLook1998

def apply_film_grain(image, params: FilmLook1998 = None):
    """Apply 35mm film grain."""
    if params is None:
        params = FilmLook1998()
    return {"grain_intensity": params.grain_intensity}

def apply_lens_effects(image, params: FilmLook1998 = None):
    """Apply lens distortion and chromatic aberration."""
    if params is None:
        params = FilmLook1998()
    return {
        "distortion": params.lens_distortion,
        "chromatic_aberration": params.chromatic_aberration
    }

def apply_vignette(image, params: FilmLook1998 = None):
    """Apply lens vignette."""
    if params is None:
        params = FilmLook1998()
    return {"vignette_strength": params.vignette_strength}
