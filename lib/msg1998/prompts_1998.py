"""
MSG 1998 - 1998 Film Aesthetic Prompts

Prompts for SD generation with 1998 film aesthetic.
"""

from typing import Dict


# Base prompts for 1998 film aesthetic
POSITIVE_BASE = """
1998 film stock, Kodak Vision3 500T 5219,
35mm anamorphic lens, 2.39:1 aspect ratio,
film grain, organic texture, practical lighting,
period accurate 1998 New York City,
Matthew Libatique cinematography style,
handheld camera, documentary feel,
no digital artifacts, no modern elements
"""

NEGATIVE_BASE = """
digital, clean, sharp, 4K, modern,
2020s, smartphones, LED screens,
CGI look, video game aesthetic,
over-processed, HDR, flat lighting,
anamorphic lens blur on edges,
modern cars, contemporary fashion
"""

# Scene-specific modifiers
SCENE_PROMPTS: Dict[str, str] = {
    "msg_exterior": "Madison Square Garden exterior, daytime, establishing shot, NYC skyline",
    "msg_interior": "arena concourse, fluorescent lighting, crowd, indoor sports venue",
    "subway_platform": "underground, tile walls, fluorescent, 1998 graffiti state, NYC subway",
    "subway_car": "MTA subway car interior, 1998 rolling stock, metal seats, advertising",
    "night_exterior": "neon signs, wet pavement, streetlights, urban night, film noir lighting",
    "hospital": "fluorescent hospital lighting, sterile, clinical, medical equipment",
    "apartment": "warm interior, cozy, golden hour through window, lived-in space",
    "office": "fluorescent office lighting, cubicles, CRT monitors, 1990s decor",
    "courthouse": "marble floors, wood paneling, formal, legal drama aesthetic",
    "street_day": "busy NYC street, yellow taxis, pedestrians, storefronts, daytime",
    "alley": "urban alley, fire escapes, brick walls, shadows, gritty",
}

# Layer-specific additions
LAYER_PROMPTS: Dict[str, str] = {
    "background": "distant buildings, sky, atmospheric perspective, cityscape",
    "midground": "main subject, detailed architecture, primary action",
    "foreground": "street level details, pedestrians, period cars, close elements",
}


def build_prompt(
    base: str,
    scene_type: str,
    layer: str
) -> str:
    """
    Build complete prompt for generation.

    Args:
        base: Base positive prompt
        scene_type: Type of scene (key from SCENE_PROMPTS)
        layer: Layer name (key from LAYER_PROMPTS)

    Returns:
        Complete prompt string
    """
    parts = [base.strip()]

    # Add scene-specific prompt
    if scene_type in SCENE_PROMPTS:
        parts.append(SCENE_PROMPTS[scene_type])

    # Add layer-specific prompt
    if layer in LAYER_PROMPTS:
        parts.append(LAYER_PROMPTS[layer])

    return ", ".join(parts)


def get_prompt_variations(scene_type: str) -> Dict[str, str]:
    """
    Get all layer prompts for a scene type.

    Args:
        scene_type: Type of scene

    Returns:
        Dict of layer -> prompt
    """
    return {
        layer: build_prompt(POSITIVE_BASE, scene_type, layer)
        for layer in LAYER_PROMPTS.keys()
    }


def create_negative_prompt(additions: list = None) -> str:
    """
    Create negative prompt with optional additions.

    Args:
        additions: Additional negative prompt terms

    Returns:
        Complete negative prompt
    """
    parts = [NEGATIVE_BASE.strip()]

    if additions:
        parts.extend(additions)

    return ", ".join(parts)


# Period-specific negative prompts
PERIOD_NEGATIVE_ADDITIONS = [
    "iphone",
    "smartphone",
    "LED billboard",
    "Tesla car",
    "modern signage",
    "2010s fashion",
    "2020s fashion",
    "digital watch",
    "flat screen TV",
    "USB cable",
]


def get_period_negative_prompt() -> str:
    """Get negative prompt with period-specific additions."""
    return create_negative_prompt(PERIOD_NEGATIVE_ADDITIONS)


# Time-of-day modifiers
TIME_MODIFIERS = {
    "golden_hour": "warm golden light, long shadows, sunset glow",
    "blue_hour": "cool blue light, twilight, soft shadows",
    "midday": "harsh sunlight, strong shadows, bright",
    "overcast": "diffused light, soft shadows, gray sky",
    "night": "artificial lighting, neon, streetlights, dark",
}


def add_time_modifier(prompt: str, time_of_day: str) -> str:
    """
    Add time-of-day modifier to prompt.

    Args:
        prompt: Existing prompt
        time_of_day: Time key from TIME_MODIFIERS

    Returns:
        Modified prompt
    """
    if time_of_day in TIME_MODIFIERS:
        return f"{prompt}, {TIME_MODIFIERS[time_of_day]}"
    return prompt


# Weather modifiers
WEATHER_MODIFIERS = {
    "clear": "clear sky, sunny day",
    "rain": "wet surfaces, rain, reflections, puddles",
    "snow": "snow covered, winter, cold atmosphere",
    "fog": "foggy, misty, reduced visibility, atmospheric",
}


def add_weather_modifier(prompt: str, weather: str) -> str:
    """
    Add weather modifier to prompt.

    Args:
        prompt: Existing prompt
        weather: Weather key from WEATHER_MODIFIERS

    Returns:
        Modified prompt
    """
    if weather in WEATHER_MODIFIERS:
        return f"{prompt}, {WEATHER_MODIFIERS[weather]}"
    return prompt
