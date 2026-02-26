"""Projector profile database with common models.

This module provides pre-defined profiles for common projector models
from Epson, BenQ, Optoma, Sony, and other manufacturers.

All profiles use the CORRECTED throw ratio formula:
    focal_length = sensor_width * throw_ratio
"""

from typing import Dict, List, Optional
import yaml
from pathlib import Path

from .profiles import (
    ProjectorProfile,
    ProjectorType,
    AspectRatio,
    LensShift,
    KeystoneCorrection,
)


# ============================================================================
# EPSON PROJECTORS
# ============================================================================

EPSON_HOME_CINEMA_2150 = ProjectorProfile(
    name="Epson_Home_Cinema_2150",
    manufacturer="Epson",
    model="Home Cinema 2150",
    projector_type=ProjectorType.LCD,
    native_resolution=(1920, 1080),
    aspect_ratio=AspectRatio.RATIO_16_9,
    throw_ratio=1.32,
    throw_ratio_range=(1.32, 1.32),
    has_zoom=False,
    lens_shift=LensShift(vertical=0.0, horizontal=0.0),
    keystone=KeystoneCorrection(horizontal=0.0, vertical=0.0, automatic=True),
    brightness_lumens=2500,
    contrast_ratio=70000,
    color_gamut="Rec.709",
    sensor_width=36.0,
    sensor_height=20.25,
)

EPSON_HOME_CINEMA_3800 = ProjectorProfile(
    name="Epson_Home_Cinema_3800",
    manufacturer="Epson",
    model="Home Cinema 3800",
    projector_type=ProjectorType.LCD,
    native_resolution=(1920, 1080),
    aspect_ratio=AspectRatio.RATIO_16_9,
    throw_ratio=1.32,
    throw_ratio_range=(1.32, 1.32),
    has_zoom=False,
    lens_shift=LensShift(
        vertical=0.60,
        horizontal=0.24,
        vertical_range=(-0.60, 0.60),
        horizontal_range=(-0.24, 0.24)
    ),
    keystone=KeystoneCorrection(horizontal=0.0, vertical=0.0),
    brightness_lumens=3000,
    contrast_ratio=100000,
    color_gamut="Rec.709",
    sensor_width=36.0,
    sensor_height=20.25,
)

EPSON_PRO_CINEMA_6050UB = ProjectorProfile(
    name="Epson_Pro_Cinema_6050UB",
    manufacturer="Epson",
    model="Pro Cinema 6050UB",
    projector_type=ProjectorType.LCD,
    native_resolution=(1920, 1080),
    aspect_ratio=AspectRatio.RATIO_16_9,
    throw_ratio=1.35,
    throw_ratio_range=(1.32, 2.15),
    has_zoom=True,
    lens_shift=LensShift(
        vertical=0.96,
        horizontal=0.47,
        vertical_range=(-0.96, 0.96),
        horizontal_range=(-0.47, 0.47)
    ),
    keystone=KeystoneCorrection(horizontal=30.0, vertical=30.0),
    brightness_lumens=2500,
    contrast_ratio=1000000,
    color_gamut="DCI-P3",
    sensor_width=36.0,
    sensor_height=20.25,
)

EPSON_LS12000 = ProjectorProfile(
    name="Epson_LS12000",
    manufacturer="Epson",
    model="LS12000",
    projector_type=ProjectorType.LASER,
    native_resolution=(1920, 1080),
    aspect_ratio=AspectRatio.RATIO_16_9,
    throw_ratio=1.35,
    throw_ratio_range=(1.32, 2.24),
    has_zoom=True,
    lens_shift=LensShift(
        vertical=0.60,
        horizontal=0.24,
        vertical_range=(-0.60, 0.60),
        horizontal_range=(-0.24, 0.24)
    ),
    keystone=KeystoneCorrection(horizontal=0.0, vertical=0.0),
    brightness_lumens=2700,
    contrast_ratio=2500000,
    color_gamut="Rec.2020",
    sensor_width=36.0,
    sensor_height=20.25,
)


# ============================================================================
# BENQ PROJECTORS
# ============================================================================

BENQ_MW632ST = ProjectorProfile(
    name="BenQ_MW632ST",
    manufacturer="BenQ",
    model="MW632ST",
    projector_type=ProjectorType.DLP,
    native_resolution=(1280, 800),
    aspect_ratio=AspectRatio.RATIO_16_10,
    throw_ratio=0.72,
    throw_ratio_range=(0.72, 0.72),
    has_zoom=False,
    lens_shift=LensShift(vertical=0.0, horizontal=0.0),
    keystone=KeystoneCorrection(horizontal=40.0, vertical=40.0),
    brightness_lumens=3200,
    contrast_ratio=13000,
    color_gamut="Rec.709",
    sensor_width=36.0,
    sensor_height=22.5,  # 16:10
)

BENQ_TH685 = ProjectorProfile(
    name="BenQ_TH685",
    manufacturer="BenQ",
    model="TH685",
    projector_type=ProjectorType.DLP,
    native_resolution=(1920, 1080),
    aspect_ratio=AspectRatio.RATIO_16_9,
    throw_ratio=1.5,
    throw_ratio_range=(1.5, 1.66),
    has_zoom=True,
    lens_shift=LensShift(vertical=0.0, horizontal=0.0),
    keystone=KeystoneCorrection(horizontal=40.0, vertical=40.0),
    brightness_lumens=3500,
    contrast_ratio=10000,
    color_gamut="Rec.709",
    sensor_width=36.0,
    sensor_height=20.25,
)

BENQ_W2700 = ProjectorProfile(
    name="BenQ_W2700",
    manufacturer="BenQ",
    model="W2700",
    projector_type=ProjectorType.DLP,
    native_resolution=(3840, 2160),
    aspect_ratio=AspectRatio.RATIO_16_9,
    throw_ratio=1.13,
    throw_ratio_range=(1.13, 1.47),
    has_zoom=True,
    lens_shift=LensShift(
        vertical=0.60,
        horizontal=0.23,
        vertical_range=(-0.60, 0.60),
        horizontal_range=(-0.23, 0.23)
    ),
    keystone=KeystoneCorrection(horizontal=30.0, vertical=30.0),
    brightness_lumens=2000,
    contrast_ratio=50000,
    color_gamut="DCI-P3",
    sensor_width=36.0,
    sensor_height=20.25,
)


# ============================================================================
# OPTOMA PROJECTORS
# ============================================================================

OPTOMA_UHD38 = ProjectorProfile(
    name="Optoma_UHD38",
    manufacturer="Optoma",
    model="UHD38",
    projector_type=ProjectorType.DLP,
    native_resolution=(3840, 2160),
    aspect_ratio=AspectRatio.RATIO_16_9,
    throw_ratio=1.5,
    throw_ratio_range=(1.5, 1.65),
    has_zoom=True,
    lens_shift=LensShift(vertical=0.0, horizontal=0.0),
    keystone=KeystoneCorrection(horizontal=40.0, vertical=40.0),
    brightness_lumens=4000,
    contrast_ratio=1000000,
    color_gamut="Rec.709",
    sensor_width=36.0,
    sensor_height=20.25,
)

OPTOMA_GT1080HDR = ProjectorProfile(
    name="Optoma_GT1080HDR",
    manufacturer="Optoma",
    model="GT1080HDR",
    projector_type=ProjectorType.DLP,
    native_resolution=(1920, 1080),
    aspect_ratio=AspectRatio.RATIO_16_9,
    throw_ratio=0.50,  # Short throw
    throw_ratio_range=(0.50, 0.50),
    has_zoom=False,
    lens_shift=LensShift(vertical=0.0, horizontal=0.0),
    keystone=KeystoneCorrection(horizontal=40.0, vertical=40.0),
    brightness_lumens=3800,
    contrast_ratio=300000,
    color_gamut="Rec.709",
    sensor_width=36.0,
    sensor_height=20.25,
)

OPTOMA_EH412 = ProjectorProfile(
    name="Optoma_EH412",
    manufacturer="Optoma",
    model="EH412",
    projector_type=ProjectorType.DLP,
    native_resolution=(1920, 1080),
    aspect_ratio=AspectRatio.RATIO_16_9,
    throw_ratio=1.94,
    throw_ratio_range=(1.94, 2.16),
    has_zoom=True,
    lens_shift=LensShift(vertical=0.0, horizontal=0.0),
    keystone=KeystoneCorrection(horizontal=40.0, vertical=40.0),
    brightness_lumens=4500,
    contrast_ratio=50000,
    color_gamut="Rec.709",
    sensor_width=36.0,
    sensor_height=20.25,
)


# ============================================================================
# SONY PROJECTORS
# ============================================================================

SONY_VPL_HW45ES = ProjectorProfile(
    name="Sony_VPL_HW45ES",
    manufacturer="Sony",
    model="VPL-HW45ES",
    projector_type=ProjectorType.LCOS,
    native_resolution=(1920, 1080),
    aspect_ratio=AspectRatio.RATIO_16_9,
    throw_ratio=1.4,
    throw_ratio_range=(1.39, 1.74),
    has_zoom=True,
    lens_shift=LensShift(
        vertical=0.71,
        horizontal=0.25,
        vertical_range=(-0.71, 0.71),
        horizontal_range=(-0.25, 0.25)
    ),
    keystone=KeystoneCorrection(horizontal=0.0, vertical=0.0),
    brightness_lumens=1800,
    contrast_ratio=120000,
    color_gamut="Rec.709",
    sensor_width=36.0,
    sensor_height=20.25,
)

SONY_VPL_VW295ES = ProjectorProfile(
    name="Sony_VPL_VW295ES",
    manufacturer="Sony",
    model="VPL-VW295ES",
    projector_type=ProjectorType.LCOS,
    native_resolution=(4096, 2160),
    aspect_ratio=AspectRatio.RATIO_17_9,
    throw_ratio=1.38,
    throw_ratio_range=(1.38, 2.02),
    has_zoom=True,
    lens_shift=LensShift(
        vertical=0.85,
        horizontal=0.31,
        vertical_range=(-0.85, 0.85),
        horizontal_range=(-0.31, 0.31)
    ),
    keystone=KeystoneCorrection(horizontal=0.0, vertical=0.0),
    brightness_lumens=1500,
    contrast_ratio=200000,
    color_gamut="Rec.2020",
    sensor_width=36.0,
    sensor_height=18.91,  # 17:9
)


# ============================================================================
# BUDGET / MINI PROJECTORS
# ============================================================================

GENERIC_480P_MINI = ProjectorProfile(
    name="Generic_480P_Mini",
    manufacturer="Generic",
    model="480P Mini Projector",
    projector_type=ProjectorType.DLP,
    native_resolution=(854, 480),  # 480p (480 vertical lines)
    aspect_ratio=AspectRatio.RATIO_16_9,
    throw_ratio=1.5,  # Typical for cheap projectors
    throw_ratio_range=(1.4, 1.6),
    has_zoom=False,
    lens_shift=LensShift(vertical=0.0, horizontal=0.0),
    keystone=KeystoneCorrection(horizontal=15.0, vertical=15.0, automatic=False),
    brightness_lumens=200,  # Low brightness typical of mini projectors
    contrast_ratio=1000,    # Low contrast
    color_gamut="sRGB",     # Limited color
    sensor_width=36.0,
    sensor_height=20.25,
    calibration_notes="Generic 480p mini/portable projector. Low brightness (200-400 ANSI lumens typical). "
                      "Suitable for dark rooms only. Often marketed as '1080p supported' but native is 480p. "
                      "Examples: AAXA P300, Anker Nebula Capsule, Vamvo L4200, various Amazon budget projectors.",
)


# ============================================================================
# PROFILE REGISTRY
# ============================================================================

PROJECTOR_PROFILES: Dict[str, ProjectorProfile] = {
    # Epson
    "Epson_Home_Cinema_2150": EPSON_HOME_CINEMA_2150,
    "Epson_Home_Cinema_3800": EPSON_HOME_CINEMA_3800,
    "Epson_Pro_Cinema_6050UB": EPSON_PRO_CINEMA_6050UB,
    "Epson_LS12000": EPSON_LS12000,

    # BenQ
    "BenQ_MW632ST": BENQ_MW632ST,
    "BenQ_TH685": BENQ_TH685,
    "BenQ_W2700": BENQ_W2700,

    # Optoma
    "Optoma_UHD38": OPTOMA_UHD38,
    "Optoma_GT1080HDR": OPTOMA_GT1080HDR,
    "Optoma_EH412": OPTOMA_EH412,

    # Sony
    "Sony_VPL_HW45ES": SONY_VPL_HW45ES,
    "Sony_VPL_VW295ES": SONY_VPL_VW295ES,

    # Budget / Mini
    "Generic_480P_Mini": GENERIC_480P_MINI,
}


def get_profile(name: str) -> ProjectorProfile:
    """Get a projector profile by name.

    Args:
        name: Profile name (e.g., "Epson_Home_Cinema_2150")

    Returns:
        ProjectorProfile instance

    Raises:
        KeyError: If profile not found
    """
    if name not in PROJECTOR_PROFILES:
        available = list(PROJECTOR_PROFILES.keys())
        raise KeyError(f"Profile '{name}' not found. Available: {available}")
    return PROJECTOR_PROFILES[name]


def list_profiles(manufacturer: str = None) -> List[str]:
    """List available projector profiles.

    Args:
        manufacturer: Filter by manufacturer (optional, case-insensitive)

    Returns:
        List of profile names
    """
    if manufacturer:
        return [
            name for name, profile in PROJECTOR_PROFILES.items()
            if profile.manufacturer.lower() == manufacturer.lower()
        ]
    return list(PROJECTOR_PROFILES.keys())


def get_profiles_by_throw_ratio(
    min_ratio: float = None,
    max_ratio: float = None
) -> List[ProjectorProfile]:
    """Get profiles filtered by throw ratio range.

    Args:
        min_ratio: Minimum throw ratio (inclusive)
        max_ratio: Maximum throw ratio (inclusive)

    Returns:
        List of matching profiles
    """
    results = []
    for profile in PROJECTOR_PROFILES.values():
        ratio = profile.throw_ratio
        if min_ratio is not None and ratio < min_ratio:
            continue
        if max_ratio is not None and ratio > max_ratio:
            continue
        results.append(profile)
    return results


def get_profiles_by_resolution(
    min_width: int = None,
    min_height: int = None
) -> List[ProjectorProfile]:
    """Get profiles filtered by minimum resolution.

    Args:
        min_width: Minimum horizontal resolution (inclusive)
        min_height: Minimum vertical resolution (inclusive)

    Returns:
        List of matching profiles
    """
    results = []
    for profile in PROJECTOR_PROFILES.values():
        width, height = profile.native_resolution
        if min_width is not None and width < min_width:
            continue
        if min_height is not None and height < min_height:
            continue
        results.append(profile)
    return results


def get_short_throw_profiles(ratio_threshold: float = 0.8) -> List[ProjectorProfile]:
    """Get short-throw projector profiles.

    Args:
        ratio_threshold: Maximum throw ratio to consider "short throw"

    Returns:
        List of short-throw profiles
    """
    return get_profiles_by_throw_ratio(max_ratio=ratio_threshold)


def get_4k_profiles() -> List[ProjectorProfile]:
    """Get 4K (UHD) projector profiles.

    Returns:
        List of 4K profiles
    """
    return get_profiles_by_resolution(min_width=3840)


# Alias for get_profile (convenience function)
def load_profile(name: str) -> ProjectorProfile:
    """Load a projector profile by name.

    This is an alias for get_profile() provided for convenience.

    Args:
        name: Profile name (e.g., "Epson_Home_Cinema_2150")

    Returns:
        ProjectorProfile instance

    Raises:
        KeyError: If profile not found
    """
    return get_profile(name)


def load_profile_from_yaml(yaml_path: str, profile_name: str) -> ProjectorProfile:
    """Load a projector profile from a YAML file.

    Args:
        yaml_path: Path to YAML configuration file
        profile_name: Name of profile to load

    Returns:
        ProjectorProfile instance

    Raises:
        FileNotFoundError: If YAML file not found
        KeyError: If profile not found in file
    """
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")

    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    profiles = data.get('profiles', {})
    if profile_name not in profiles:
        raise KeyError(f"Profile '{profile_name}' not found in {yaml_path}")

    p = profiles[profile_name]

    # Parse lens shift
    lens_shift_data = p.get('lens_shift', {})
    lens_shift = LensShift(
        vertical=lens_shift_data.get('vertical', 0.0),
        horizontal=lens_shift_data.get('horizontal', 0.0),
    )

    # Parse keystone
    keystone_data = p.get('keystone', {})
    keystone = KeystoneCorrection(
        horizontal=keystone_data.get('horizontal', 0.0),
        vertical=keystone_data.get('vertical', 0.0),
        automatic=keystone_data.get('automatic', False),
    )

    # Parse aspect ratio
    ar_str = p.get('aspect_ratio', '16/9')
    if '/' in ar_str:
        num, den = map(int, ar_str.split('/'))
        aspect_value = num / den
    else:
        aspect_value = float(ar_str)

    # Find matching AspectRatio enum
    aspect_ratio = AspectRatio.RATIO_16_9  # default
    for ar in AspectRatio:
        if abs(ar.value[0] / ar.value[1] - aspect_value) < 0.01:
            aspect_ratio = ar
            break

    return ProjectorProfile(
        name=profile_name,
        manufacturer=p.get('manufacturer', 'Unknown'),
        model=p.get('model', ''),
        projector_type=ProjectorType(p.get('type', 'dlp').lower()),
        native_resolution=tuple(p.get('resolution', [1920, 1080])),
        aspect_ratio=aspect_ratio,
        throw_ratio=p.get('throw_ratio', 1.32),
        throw_ratio_range=tuple(p.get('throw_ratio_range', [1.32, 1.32])),
        has_zoom=p.get('has_zoom', False),
        lens_shift=lens_shift,
        keystone=keystone,
        brightness_lumens=p.get('brightness_lumens', 2500),
        contrast_ratio=p.get('contrast_ratio', 10000),
        color_gamut=p.get('color_gamut', 'Rec.709'),
        sensor_width=p.get('sensor_width', 36.0),
        sensor_height=p.get('sensor_height', 20.25),
    )
