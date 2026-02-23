"""
MSG 1998 - Period Accuracy Validator

Validates 3D assets for 1998 period accuracy.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Set

from .types import PeriodViolation, PeriodViolationSeverity


# Known period violations for 1998 NYC
PERIOD_VIOLATIONS_1998: Dict[str, Dict[str, Any]] = {
    # Technology
    "led_screens": {
        "description": "LED billboards/digital screens not common until 2000s",
        "severity": PeriodViolationSeverity.ERROR,
        "suggestion": "Use printed/illuminated signage instead"
    },
    "smartphone_stations": {
        "description": "Smartphone charging stations post-2010",
        "severity": PeriodViolationSeverity.ERROR,
        "suggestion": "Remove or replace with period pay phones"
    },
    "modern_traffic_signals": {
        "description": "LED traffic signals post-2005",
        "severity": PeriodViolationSeverity.WARNING,
        "suggestion": "Use incandescent traffic signals"
    },
    "electric_vehicle_charging": {
        "description": "EV charging stations post-2010",
        "severity": PeriodViolationSeverity.ERROR,
        "suggestion": "Remove EV infrastructure"
    },
    "wifi_hotspot_signs": {
        "description": "Public WiFi signage post-2000s",
        "severity": PeriodViolationSeverity.ERROR,
        "suggestion": "Remove WiFi-related signage"
    },

    # Architecture
    "post_1998_construction": {
        "description": "Buildings constructed after 1998",
        "severity": PeriodViolationSeverity.ERROR,
        "suggestion": "Remove or replace with period-appropriate structures"
    },
    "modern_storefronts": {
        "description": "Storefronts with contemporary branding",
        "severity": PeriodViolationSeverity.WARNING,
        "suggestion": "Use 1998-era branding and signage"
    },

    # Street Furniture
    "pay_phone_stations": {
        "description": "Should have pay phones, not smartphone stations",
        "severity": PeriodViolationSeverity.INFO,
        "suggestion": "Add period pay phones"
    },
    "newspaper_boxes": {
        "description": "Newspaper boxes common in 1998",
        "severity": PeriodViolationSeverity.INFO,
        "suggestion": "Add newspaper vending boxes"
    },
    "modern_bike_racks": {
        "description": "Contemporary bike rack designs",
        "severity": PeriodViolationSeverity.INFO,
        "suggestion": "Use 1998-era bike rack styles"
    },

    # Vehicles
    "post_1998_cars": {
        "description": "Cars manufactured after 1998",
        "severity": PeriodViolationSeverity.ERROR,
        "suggestion": "Use period-appropriate vehicle models"
    },
    "modern_taxi_design": {
        "description": "Post-2000s taxi styling",
        "severity": PeriodViolationSeverity.WARNING,
        "suggestion": "Use 1998-era NYC taxi design (Ford Crown Victoria)"
    },
    "contemporary_emergency_vehicles": {
        "description": "Modern emergency vehicle styling",
        "severity": PeriodViolationSeverity.WARNING,
        "suggestion": "Use 1998-era emergency vehicle designs"
    },

    # Advertising
    "digital_advertising": {
        "description": "Digital/LED advertising displays",
        "severity": PeriodViolationSeverity.ERROR,
        "suggestion": "Use printed billboards and posters"
    },
    "modern_branding": {
        "description": "Post-1998 corporate branding",
        "severity": PeriodViolationSeverity.WARNING,
        "suggestion": "Research 1998-era brand logos and signage"
    },

    # Fashion/Crowd
    "contemporary_fashion": {
        "description": "Post-1998 clothing styles",
        "severity": PeriodViolationSeverity.WARNING,
        "suggestion": "Use 1998-era fashion references"
    },
    "smartphones_in_crowd": {
        "description": "Characters holding smartphones",
        "severity": PeriodViolationSeverity.ERROR,
        "suggestion": "Remove or replace with period devices"
    },

    # Technology Props
    "flat_screen_monitors": {
        "description": "Flat screen monitors rare in 1998",
        "severity": PeriodViolationSeverity.WARNING,
        "suggestion": "Use CRT monitors for computers"
    },
    "laptops_post_2000": {
        "description": "Modern laptop designs",
        "severity": PeriodViolationSeverity.WARNING,
        "suggestion": "Use 1998-era laptop models (thick, bulky)"
    },
}

# Keywords that suggest modern elements
MODERN_KEYWORDS = [
    "iphone", "android", "smartphone", "tablet", "ipad",
    "led_screen", "led_display", "digital_signage",
    "wifi", "bluetooth", "usb_c",
    "tesla", "electric_vehicle", "ev_charging",
    "uber", "lyft", "airbnb",
    "instagram", "tiktok", "twitter", "facebook",
    "4k", "uhd", "hdr",
]


def validate_period_accuracy(
    blend_path: Path,
    target_year: int = 1998
) -> List[PeriodViolation]:
    """
    Check blend file for period-accurate elements.

    Args:
        blend_path: Path to blend file
        target_year: Target year for period accuracy

    Returns:
        List of detected period violations
    """
    violations = []

    if not blend_path.exists():
        return [PeriodViolation(
            element="file",
            description=f"Blend file not found: {blend_path}",
            severity=PeriodViolationSeverity.ERROR
        )]

    # Try to parse blend file for named elements
    try:
        # Blend files are binary, but we can extract some text
        with open(blend_path, 'rb') as f:
            content = f.read()

        # Try to decode as string for text analysis
        try:
            text_content = content.decode('utf-8', errors='ignore')
        except Exception:
            text_content = ""

        # Check for modern keywords in object names
        violations.extend(_check_modern_keywords(text_content, target_year))

    except Exception as e:
        violations.append(PeriodViolation(
            element="file",
            description=f"Error reading blend file: {e}",
            severity=PeriodViolationSeverity.INFO
        ))

    return violations


def validate_object_name(name: str, target_year: int = 1998) -> List[PeriodViolation]:
    """
    Validate a single object name for period accuracy.

    Args:
        name: Object name to validate
        target_year: Target year for period accuracy

    Returns:
        List of violations found in the name
    """
    violations = []
    name_lower = name.lower()

    for keyword in MODERN_KEYWORDS:
        if keyword in name_lower:
            violations.append(PeriodViolation(
                element=name,
                description=f"Modern keyword '{keyword}' detected in object name",
                severity=PeriodViolationSeverity.WARNING,
                suggestion="Consider renaming or replacing with period-appropriate element"
            ))

    return violations


def validate_materials(material_names: List[str], target_year: int = 1998) -> List[PeriodViolation]:
    """
    Validate material names for period accuracy.

    Args:
        material_names: List of material names
        target_year: Target year for period accuracy

    Returns:
        List of violations found
    """
    violations = []

    for name in material_names:
        name_lower = name.lower()

        # Check for LED/emissive materials that might be modern
        if "led" in name_lower and "screen" in name_lower:
            violations.append(PeriodViolation(
                element=name,
                description="LED screen material detected",
                severity=PeriodViolationSeverity.ERROR,
                suggestion="Use emissive material with lower intensity for period signage"
            ))

        # Check for digital display materials
        if "digital" in name_lower and "display" in name_lower:
            violations.append(PeriodViolation(
                element=name,
                description="Digital display material detected",
                severity=PeriodViolationSeverity.WARNING,
                suggestion="Use printed poster texture instead"
            ))

    return violations


def validate_texture_paths(texture_paths: List[str], target_year: int = 1998) -> List[PeriodViolation]:
    """
    Validate texture file paths for period-appropriate naming.

    Args:
        texture_paths: List of texture file paths
        target_year: Target year for period accuracy

    Returns:
        List of violations found
    """
    violations = []

    for path_str in texture_paths:
        path = Path(path_str)
        name_lower = path.stem.lower()

        for keyword in MODERN_KEYWORDS:
            if keyword in name_lower:
                violations.append(PeriodViolation(
                    element=str(path),
                    description=f"Modern keyword '{keyword}' in texture name",
                    severity=PeriodViolationSeverity.WARNING,
                    suggestion="Use period-appropriate texture naming"
                ))

    return violations


def _check_modern_keywords(text_content: str, target_year: int) -> List[PeriodViolation]:
    """
    Check text content for modern keywords.

    Args:
        text_content: Text to analyze
        target_year: Target year

    Returns:
        List of violations
    """
    violations = []
    text_lower = text_content.lower()

    for keyword in MODERN_KEYWORDS:
        # Use word boundary matching
        pattern = r'\b' + re.escape(keyword) + r'\b'
        matches = re.findall(pattern, text_lower)

        if matches:
            severity = PeriodViolationSeverity.WARNING
            if keyword in ["iphone", "smartphone", "android", "tesla"]:
                severity = PeriodViolationSeverity.ERROR

            violations.append(PeriodViolation(
                element="blend_content",
                description=f"Modern keyword '{keyword}' found {len(matches)} time(s)",
                severity=severity,
                suggestion=f"Review and replace '{keyword}' references with period-appropriate alternatives"
            ))

    return violations


def get_period_guidelines(year: int = 1998) -> Dict[str, Any]:
    """
    Get period guidelines for a specific year.

    Args:
        year: Target year

    Returns:
        Dict with guidelines for different categories
    """
    return {
        "year": year,
        "technology": {
            "smartphones": "Not available (iPhone released 2007)",
            "flat_screens": "Rare, CRT monitors standard",
            "digital_signage": "Minimal, mostly printed",
            "internet": "Dial-up common, early broadband"
        },
        "vehicles": {
            "common_cars": ["Ford Crown Victoria", "Chevy Caprice", "Toyota Camry"],
            "nyc_taxi": "Ford Crown Victoria yellow taxi",
            "emergency": "1990s styling"
        },
        "street_furniture": {
            "pay_phones": "Common on street corners",
            "newspaper_boxes": "Multiple publications",
            "bus_shelters": "1990s design",
            "trash_cans": "Wire mesh design"
        },
        "fashion": {
            "notes": "Baggy clothing, cargo pants, windbreakers common"
        }
    }
