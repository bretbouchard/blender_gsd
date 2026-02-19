"""
Preset Loader for Cinematic System

Provides utilities for loading camera, lens, sensor, rig, and imperfection
presets from YAML configuration files.

Follows pattern from lib/cinematic/state_manager.py for YAML/JSON handling.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List

try:
    import yaml
except ImportError:
    yaml = None

# Configuration root directory
CONFIG_ROOT = Path("configs/cinematic/cameras")

# Lighting configuration root directory
LIGHTING_CONFIG_ROOT = Path("configs/cinematic/lighting")

# Backdrop configuration root directory
BACKDROP_CONFIG_ROOT = Path("configs/cinematic/backdrops")


def load_preset(path: Path) -> Dict[str, Any]:
    """
    Load any YAML preset file.

    Args:
        path: Path to the preset YAML file

    Returns:
        Dictionary containing preset data

    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Preset file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data_raw = f.read()

    if path.suffix.lower() in [".yaml", ".yml"]:
        if not yaml:
            raise RuntimeError(
                "PyYAML not available. Use JSON or install PyYAML."
            )
        return yaml.safe_load(data_raw)
    else:
        import json
        return json.loads(data_raw)


def get_lens_preset(name: str) -> Dict[str, Any]:
    """
    Load a specific lens preset by name.

    Args:
        name: Name of the lens preset (e.g., "85mm_portrait")

    Returns:
        Dictionary containing lens configuration

    Raises:
        FileNotFoundError: If lens_presets.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = CONFIG_ROOT / "lens_presets.yaml"
    data = load_preset(path)

    lenses = data.get("lenses", {})
    if name not in lenses:
        available = list(lenses.keys())
        raise ValueError(
            f"Lens preset '{name}' not found. Available: {available}"
        )

    return lenses[name]


def get_sensor_preset(name: str) -> Dict[str, Any]:
    """
    Load a specific sensor preset by name.

    Args:
        name: Name of the sensor preset (e.g., "full_frame")

    Returns:
        Dictionary containing sensor configuration

    Raises:
        FileNotFoundError: If sensor_presets.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = CONFIG_ROOT / "sensor_presets.yaml"
    data = load_preset(path)

    sensors = data.get("sensors", {})
    if name not in sensors:
        available = list(sensors.keys())
        raise ValueError(
            f"Sensor preset '{name}' not found. Available: {available}"
        )

    return sensors[name]


def get_rig_preset(name: str) -> Dict[str, Any]:
    """
    Load a specific camera rig preset by name.

    Args:
        name: Name of the rig preset (e.g., "tripod_standard")

    Returns:
        Dictionary containing rig configuration

    Raises:
        FileNotFoundError: If rig_presets.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = CONFIG_ROOT / "rig_presets.yaml"
    data = load_preset(path)

    rigs = data.get("rigs", {})
    if name not in rigs:
        available = list(rigs.keys())
        raise ValueError(
            f"Rig preset '{name}' not found. Available: {available}"
        )

    return rigs[name]


def get_imperfection_preset(name: str) -> Dict[str, Any]:
    """
    Load a specific lens imperfection preset by name.

    Args:
        name: Name of the imperfection preset (e.g., "clean", "vintage")

    Returns:
        Dictionary containing imperfection configuration

    Raises:
        FileNotFoundError: If imperfection_presets.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = CONFIG_ROOT / "imperfection_presets.yaml"
    data = load_preset(path)

    imperfections = data.get("imperfections", {})
    if name not in imperfections:
        available = list(imperfections.keys())
        raise ValueError(
            f"Imperfection preset '{name}' not found. Available: {available}"
        )

    return imperfections[name]


def list_lens_presets() -> List[str]:
    """
    List all available lens preset names.

    Returns:
        Sorted list of lens preset names

    Raises:
        FileNotFoundError: If lens_presets.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = CONFIG_ROOT / "lens_presets.yaml"
    data = load_preset(path)
    return sorted(data.get("lenses", {}).keys())


def list_sensor_presets() -> List[str]:
    """
    List all available sensor preset names.

    Returns:
        Sorted list of sensor preset names

    Raises:
        FileNotFoundError: If sensor_presets.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = CONFIG_ROOT / "sensor_presets.yaml"
    data = load_preset(path)
    return sorted(data.get("sensors", {}).keys())


def list_rig_presets() -> List[str]:
    """
    List all available rig preset names.

    Returns:
        Sorted list of rig preset names

    Raises:
        FileNotFoundError: If rig_presets.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = CONFIG_ROOT / "rig_presets.yaml"
    data = load_preset(path)
    return sorted(data.get("rigs", {}).keys())


def list_imperfection_presets() -> List[str]:
    """
    List all available imperfection preset names.

    Returns:
        Sorted list of imperfection preset names

    Raises:
        FileNotFoundError: If imperfection_presets.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = CONFIG_ROOT / "imperfection_presets.yaml"
    data = load_preset(path)
    return sorted(data.get("imperfections", {}).keys())


def get_aperture_preset(f_stop: float) -> Dict[str, Any]:
    """
    Get aperture configuration for a given f-stop value.

    Validates the f-stop is within the physically valid range (0.95 to 22.0)
    and returns recommended aperture blade count based on the f-stop.

    Args:
        f_stop: The f-stop value (e.g., 2.8, 4.0, 8.0)

    Returns:
        Dictionary containing:
        - f_stop: The f-stop value
        - aperture_blades: Recommended blade count
        - valid: True if within valid range

    Raises:
        ValueError: If f_stop is outside the 0.95-22.0 range
    """
    # Valid f-stop range for real lenses
    MIN_FSTOP = 0.95
    MAX_FSTOP = 22.0

    if f_stop < MIN_FSTOP:
        raise ValueError(
            f"f-stop {f_stop} is below minimum {MIN_FSTOP}. "
            f"No lens can open wider than f/{MIN_FSTOP}."
        )

    if f_stop > MAX_FSTOP:
        raise ValueError(
            f"f-stop {f_stop} is above maximum {MAX_FSTOP}. "
            f"Most lenses stop down to f/{MAX_FSTOP} at most."
        )

    # Recommend aperture blades based on f-stop
    # Wider apertures typically have more blades for rounder bokeh
    if f_stop <= 1.4:
        aperture_blades = 11  # Premium fast lenses
    elif f_stop <= 2.8:
        aperture_blades = 9   # Standard portrait lenses
    elif f_stop <= 5.6:
        aperture_blades = 7   # Standard zooms
    else:
        aperture_blades = 6   # Stopped down, shape matters less

    return {
        "f_stop": f_stop,
        "aperture_blades": aperture_blades,
        "valid": True,
    }


# =============================================================================
# Lighting System Preset Loaders
# =============================================================================


def get_lighting_rig_preset(name: str) -> Dict[str, Any]:
    """
    Load a specific lighting rig preset by name.

    Args:
        name: Name of the lighting rig preset (e.g., "three_point_soft")

    Returns:
        Dictionary containing lighting rig configuration

    Raises:
        FileNotFoundError: If rig_presets.yaml doesn't exist in lighting config
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = LIGHTING_CONFIG_ROOT / "rig_presets.yaml"
    data = load_preset(path)

    rigs = data.get("rigs", {})
    if name not in rigs:
        available = list(rigs.keys())
        raise ValueError(
            f"Lighting rig preset '{name}' not found. Available: {available}"
        )

    return rigs[name]


def get_gel_preset(name: str) -> Dict[str, Any]:
    """
    Load a specific gel/color filter preset by name.

    Args:
        name: Name of the gel preset (e.g., "cto_full", "diffusion_half")

    Returns:
        Dictionary containing gel configuration

    Raises:
        FileNotFoundError: If gel_presets.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = LIGHTING_CONFIG_ROOT / "gel_presets.yaml"
    data = load_preset(path)

    gels = data.get("gels", {})
    if name not in gels:
        available = list(gels.keys())
        raise ValueError(
            f"Gel preset '{name}' not found. Available: {available}"
        )

    return gels[name]


def get_hdri_preset(name: str) -> Dict[str, Any]:
    """
    Load a specific HDRI preset by name.

    Args:
        name: Name of the HDRI preset (e.g., "studio_bright", "golden_hour")

    Returns:
        Dictionary containing HDRI configuration

    Raises:
        FileNotFoundError: If hdri_presets.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = LIGHTING_CONFIG_ROOT / "hdri_presets.yaml"
    data = load_preset(path)

    hdris = data.get("hdri", {})
    if name not in hdris:
        available = list(hdris.keys())
        raise ValueError(
            f"HDRI preset '{name}' not found. Available: {available}"
        )

    return hdris[name]


def list_lighting_rig_presets() -> List[str]:
    """
    List all available lighting rig preset names.

    Returns:
        Sorted list of lighting rig preset names

    Raises:
        FileNotFoundError: If rig_presets.yaml doesn't exist in lighting config
        RuntimeError: If YAML file but PyYAML not available
    """
    path = LIGHTING_CONFIG_ROOT / "rig_presets.yaml"
    data = load_preset(path)
    return sorted(data.get("rigs", {}).keys())


def list_gel_presets() -> List[str]:
    """
    List all available gel preset names.

    Returns:
        Sorted list of gel preset names

    Raises:
        FileNotFoundError: If gel_presets.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = LIGHTING_CONFIG_ROOT / "gel_presets.yaml"
    data = load_preset(path)
    return sorted(data.get("gels", {}).keys())


def list_hdri_presets() -> List[str]:
    """
    List all available HDRI preset names.

    Returns:
        Sorted list of HDRI preset names

    Raises:
        FileNotFoundError: If hdri_presets.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = LIGHTING_CONFIG_ROOT / "hdri_presets.yaml"
    data = load_preset(path)
    return sorted(data.get("hdri", {}).keys())


# =============================================================================
# Backdrop System Preset Loaders
# =============================================================================


def get_infinite_curve_preset(name: str) -> Dict[str, Any]:
    """
    Load a specific infinite curve preset by name.

    Args:
        name: Name of the curve preset (e.g., "studio_white", "cyclorama_large")

    Returns:
        Dictionary containing curve configuration

    Raises:
        FileNotFoundError: If infinite_curves.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = BACKDROP_CONFIG_ROOT / "infinite_curves.yaml"
    data = load_preset(path)

    curves = data.get("curves", {})
    if name not in curves:
        available = list(curves.keys())
        raise ValueError(
            f"Infinite curve preset '{name}' not found. Available: {available}"
        )

    return curves[name]


def get_gradient_preset(name: str) -> Dict[str, Any]:
    """
    Load a specific gradient backdrop preset by name.

    Args:
        name: Name of the gradient preset (e.g., "sunset_fade", "studio_gradient")

    Returns:
        Dictionary containing gradient configuration

    Raises:
        FileNotFoundError: If gradients.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = BACKDROP_CONFIG_ROOT / "gradients.yaml"
    data = load_preset(path)

    gradients = data.get("gradients", {})
    if name not in gradients:
        available = list(gradients.keys())
        raise ValueError(
            f"Gradient preset '{name}' not found. Available: {available}"
        )

    return gradients[name]


def get_environment_preset(name: str) -> Dict[str, Any]:
    """
    Load a specific environment preset by name.

    Args:
        name: Name of the environment preset (e.g., "product_studio", "outdoor_natural")

    Returns:
        Dictionary containing environment configuration

    Raises:
        FileNotFoundError: If environments.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = BACKDROP_CONFIG_ROOT / "environments.yaml"
    data = load_preset(path)

    environments = data.get("environments", {})
    if name not in environments:
        available = list(environments.keys())
        raise ValueError(
            f"Environment preset '{name}' not found. Available: {available}"
        )

    return environments[name]


def list_infinite_curve_presets() -> List[str]:
    """
    List all available infinite curve preset names.

    Returns:
        Sorted list of infinite curve preset names

    Raises:
        FileNotFoundError: If infinite_curves.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = BACKDROP_CONFIG_ROOT / "infinite_curves.yaml"
    data = load_preset(path)
    return sorted(data.get("curves", {}).keys())


def list_gradient_presets() -> List[str]:
    """
    List all available gradient preset names.

    Returns:
        Sorted list of gradient preset names

    Raises:
        FileNotFoundError: If gradients.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = BACKDROP_CONFIG_ROOT / "gradients.yaml"
    data = load_preset(path)
    return sorted(data.get("gradients", {}).keys())


def list_environment_presets() -> List[str]:
    """
    List all available environment preset names.

    Returns:
        Sorted list of environment preset names

    Raises:
        FileNotFoundError: If environments.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = BACKDROP_CONFIG_ROOT / "environments.yaml"
    data = load_preset(path)
    return sorted(data.get("environments", {}).keys())


# =============================================================================
# Color System Preset Loaders
# =============================================================================

# Color configuration root directory
COLOR_CONFIG_ROOT = Path("configs/cinematic/color")


def get_color_preset(name: str) -> Dict[str, Any]:
    """
    Load color management preset by name.

    Args:
        name: Name of the color preset (e.g., "neutral", "high_contrast")

    Returns:
        Dictionary containing color management configuration

    Raises:
        FileNotFoundError: If color_management_presets.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = COLOR_CONFIG_ROOT / "color_management_presets.yaml"
    data = load_preset(path)

    presets = data.get("presets", {})
    if name not in presets:
        available = list(presets.keys())
        raise ValueError(
            f"Color preset '{name}' not found. Available: {available}"
        )

    return presets[name]


def get_technical_lut_preset(name: str) -> Dict[str, Any]:
    """
    Load technical LUT preset by name.

    Args:
        name: Name of the technical LUT (e.g., "rec709_to_log", "slog3")

    Returns:
        Dictionary containing technical LUT configuration

    Raises:
        FileNotFoundError: If technical_luts.yaml doesn't exist
        ValueError: If LUT name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = COLOR_CONFIG_ROOT / "technical_luts.yaml"
    data = load_preset(path)

    luts = data.get("technical", {})
    if name not in luts:
        raise ValueError(
            f"Technical LUT '{name}' not found. Available: {list(luts.keys())}"
        )

    return luts[name]


def get_film_lut_preset(name: str) -> Dict[str, Any]:
    """
    Load film LUT preset by name.

    Args:
        name: Name of the film LUT (e.g., "kodak_2383", "fuji_400h")

    Returns:
        Dictionary containing film LUT configuration

    Raises:
        FileNotFoundError: If film_luts.yaml doesn't exist
        ValueError: If LUT name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = COLOR_CONFIG_ROOT / "film_luts.yaml"
    data = load_preset(path)

    luts = data.get("film", {})
    if name not in luts:
        raise ValueError(
            f"Film LUT '{name}' not found. Available: {list(luts.keys())}"
        )

    return luts[name]


def list_color_presets() -> List[str]:
    """
    List all available color management preset names.

    Returns:
        Sorted list of color preset names

    Raises:
        FileNotFoundError: If color_management_presets.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = COLOR_CONFIG_ROOT / "color_management_presets.yaml"
    data = load_preset(path)
    return sorted(data.get("presets", {}).keys())


def list_technical_lut_presets() -> List[str]:
    """
    List all available technical LUT preset names.

    Returns:
        Sorted list of technical LUT preset names

    Raises:
        FileNotFoundError: If technical_luts.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = COLOR_CONFIG_ROOT / "technical_luts.yaml"
    data = load_preset(path)
    return sorted(data.get("technical", {}).keys())


def list_film_lut_presets() -> List[str]:
    """
    List all available film LUT preset names.

    Returns:
        Sorted list of film LUT preset names

    Raises:
        FileNotFoundError: If film_luts.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = COLOR_CONFIG_ROOT / "film_luts.yaml"
    data = load_preset(path)
    return sorted(data.get("film", {}).keys())


# =============================================================================
# Animation System Preset Loaders
# =============================================================================

# Animation configuration root directory
ANIMATION_CONFIG_ROOT = Path("configs/cinematic/animation")


def get_camera_move_preset(name: str) -> Dict[str, Any]:
    """
    Load camera move preset by name.

    Args:
        name: Name of the camera move preset (e.g., "orbit_360", "dolly_push_in")

    Returns:
        Dictionary containing camera move configuration

    Raises:
        FileNotFoundError: If camera_moves.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = ANIMATION_CONFIG_ROOT / "camera_moves.yaml"
    data = load_preset(path)

    moves = data.get("moves", {})
    if name not in moves:
        available = list(moves.keys())
        raise ValueError(
            f"Camera move preset '{name}' not found. Available: {available}"
        )

    return moves[name]


def get_easing_preset(name: str) -> Dict[str, Any]:
    """
    Load easing curve preset by name.

    Args:
        name: Name of the easing preset (e.g., "linear", "ease_in_out", "exponential")

    Returns:
        Dictionary containing easing curve configuration

    Raises:
        FileNotFoundError: If easing_curves.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = ANIMATION_CONFIG_ROOT / "easing_curves.yaml"
    data = load_preset(path)

    curves = data.get("easing", {})
    if name not in curves:
        available = list(curves.keys())
        raise ValueError(
            f"Easing preset '{name}' not found. Available: {available}"
        )

    return curves[name]


def get_turntable_preset(name: str) -> Dict[str, Any]:
    """
    Load turntable rotation preset by name.

    Args:
        name: Name of the turntable preset (e.g., "product_standard", "product_slow")

    Returns:
        Dictionary containing turntable configuration

    Raises:
        FileNotFoundError: If turntable_presets.yaml doesn't exist
        ValueError: If preset name not found
        RuntimeError: If YAML file but PyYAML not available
    """
    path = ANIMATION_CONFIG_ROOT / "turntable_presets.yaml"
    data = load_preset(path)

    presets = data.get("turntables", {})
    if name not in presets:
        available = list(presets.keys())
        raise ValueError(
            f"Turntable preset '{name}' not found. Available: {available}"
        )

    return presets[name]


def list_camera_move_presets() -> List[str]:
    """
    List all available camera move preset names.

    Returns:
        Sorted list of camera move preset names

    Raises:
        FileNotFoundError: If camera_moves.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = ANIMATION_CONFIG_ROOT / "camera_moves.yaml"
    data = load_preset(path)
    return sorted(data.get("moves", {}).keys())


def list_easing_presets() -> List[str]:
    """
    List all available easing preset names.

    Returns:
        Sorted list of easing preset names

    Raises:
        FileNotFoundError: If easing_curves.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = ANIMATION_CONFIG_ROOT / "easing_curves.yaml"
    data = load_preset(path)
    return sorted(data.get("easing", {}).keys())


def list_turntable_presets() -> List[str]:
    """
    List all available turntable preset names.

    Returns:
        Sorted list of turntable preset names

    Raises:
        FileNotFoundError: If turntable_presets.yaml doesn't exist
        RuntimeError: If YAML file but PyYAML not available
    """
    path = ANIMATION_CONFIG_ROOT / "turntable_presets.yaml"
    data = load_preset(path)
    return sorted(data.get("turntables", {}).keys())
