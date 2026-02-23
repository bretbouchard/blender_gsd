"""
Console Layout Standards - Industry-standard dimensions and spacing.

Based on:
- 19" rack standard (482.6mm width)
- 500 Series module format (API Lunchbox)
- Common console ergonomics (Neve, SSL, API)
- Research: .planning/research/CONTROL_SURFACE_DESIGN_RESEARCH.md
"""

from dataclasses import dataclass, field
from typing import Tuple, Dict, List, Optional
from enum import Enum


# =============================================================================
# RACK & PANEL STANDARDS
# =============================================================================

class RackStandard:
    """19-inch rack mounting standards."""
    WIDTH_19IN = 482.6  # mm - Standard 19" rack width
    WIDTH_19IN_METERS = 0.4826

    UNIT_HEIGHT = 44.45  # mm - 1U height
    UNIT_HEIGHT_METERS = 0.04445

    @classmethod
    def u_height(cls, units: int) -> float:
        """Get height in mm for N rack units."""
        return units * cls.UNIT_HEIGHT

    @classmethod
    def u_height_meters(cls, units: int) -> float:
        """Get height in meters for N rack units."""
        return units * cls.UNIT_HEIGHT_METERS


class FiveHundredSeries:
    """500 Series (API Lunchbox) module standards."""
    SLOT_WIDTH = 38.1  # mm - Single module width
    SLOT_HEIGHT = 133.35  # mm - 3U height
    PANEL_DEPTH = 120.0  # mm - Typical module depth

    SLOTS_PER_19IN = 10  # Standard 10-slot rack


# =============================================================================
# ELEMENT SIZE CLASSES
# =============================================================================

class ElementSize(Enum):
    """Standard element size categories."""
    XS = "xs"      # Extra Small - Eurorack, mini controls
    SM = "sm"      # Small - Pedals, compact synths
    MD = "md"      # Medium - Standard console controls
    LG = "lg"      # Large - Main controls, vintage
    XL = "xl"      # Extra Large - Master controls, signature


@dataclass
class KnobSize:
    """Knob dimensions for a size class."""
    diameter: float      # mm
    height: float        # mm
    knurl_count: int     # Number of knurl ridges

    # Derived values
    @property
    def radius(self) -> float:
        return self.diameter / 2

    @property
    def spacing(self) -> float:
        """Recommended center-to-center spacing."""
        return self.diameter + 6.0  # 6mm finger clearance


@dataclass
class ButtonSize:
    """Button dimensions for a size class."""
    diameter: float      # mm (or width for square)
    height: float        # mm
    travel: float        # mm - press depth

    @property
    def spacing(self) -> float:
        """Recommended center-to-center spacing."""
        return self.diameter + 4.0  # 4mm clearance


@dataclass
class FaderSize:
    """Fader dimensions for a size class."""
    travel_length: float  # mm - full travel distance
    knob_width: float     # mm
    knob_height: float    # mm
    track_width: float    # mm

    @property
    def total_height(self) -> float:
        """Total vertical space needed."""
        return self.travel_length + 20  # Extra for end caps


@dataclass
class LEDSize:
    """LED dimensions for a size class."""
    diameter: float      # mm
    height: float        # mm
    bezel_diameter: float  # mm

    @property
    def spacing(self) -> float:
        return self.diameter + 3.0


# =============================================================================
# SIZE DEFINITIONS BY CLASS
# =============================================================================

KNOB_SIZES: Dict[ElementSize, KnobSize] = {
    ElementSize.XS: KnobSize(diameter=10, height=8, knurl_count=20),
    ElementSize.SM: KnobSize(diameter=15, height=12, knurl_count=30),
    ElementSize.MD: KnobSize(diameter=22, height=18, knurl_count=45),
    ElementSize.LG: KnobSize(diameter=28, height=22, knurl_count=60),
    ElementSize.XL: KnobSize(diameter=38, height=30, knurl_count=80),
}

BUTTON_SIZES: Dict[ElementSize, ButtonSize] = {
    ElementSize.XS: ButtonSize(diameter=6, height=4, travel=1),
    ElementSize.SM: ButtonSize(diameter=10, height=5, travel=2),
    ElementSize.MD: ButtonSize(diameter=12, height=6, travel=2.5),
    ElementSize.LG: ButtonSize(diameter=16, height=8, travel=3),
    ElementSize.XL: ButtonSize(diameter=22, height=10, travel=4),
}

FADER_SIZES: Dict[ElementSize, FaderSize] = {
    ElementSize.XS: FaderSize(travel_length=30, knob_width=8, knob_height=10, track_width=4),
    ElementSize.SM: FaderSize(travel_length=45, knob_width=10, knob_height=14, track_width=5),
    ElementSize.MD: FaderSize(travel_length=60, knob_width=12, knob_height=18, track_width=6),
    ElementSize.LG: FaderSize(travel_length=100, knob_width=16, knob_height=22, track_width=8),
    ElementSize.XL: FaderSize(travel_length=120, knob_width=20, knob_height=28, track_width=10),
}

LED_SIZES: Dict[ElementSize, LEDSize] = {
    ElementSize.XS: LEDSize(diameter=3, height=2, bezel_diameter=4),
    ElementSize.SM: LEDSize(diameter=5, height=3, bezel_diameter=7),
    ElementSize.MD: LEDSize(diameter=8, height=4, bezel_diameter=10),
    ElementSize.LG: LEDSize(diameter=10, height=5, bezel_diameter=13),
    ElementSize.XL: LEDSize(diameter=15, height=6, bezel_diameter=18),
}


# =============================================================================
# GRID & SPACING STANDARDS
# =============================================================================

@dataclass
class GridSpacing:
    """Grid spacing standards for console layouts."""
    # Horizontal spacing
    knob_horizontal: float = 25.0    # mm - between knob centers
    button_horizontal: float = 18.0  # mm - between button centers
    fader_horizontal: float = 30.0   # mm - between fader centers

    # Vertical spacing
    row_spacing: float = 30.0        # mm - between control rows
    section_spacing: float = 50.0    # mm - between major sections

    # Margins
    panel_margin: float = 15.0       # mm - from panel edge
    label_height: float = 8.0        # mm - space for labels

    # Channel strip
    channel_width: float = 50.0      # mm - standard channel strip width
    channel_spacing: float = 2.0     # mm - between channels


DEFAULT_GRID = GridSpacing()


# =============================================================================
# CONSOLE TYPE DEFINITIONS
# =============================================================================

class ConsoleType(Enum):
    """Types of console/equipment layouts."""
    MIXING_CONSOLE = "mixing_console"
    DRUM_MACHINE = "drum_machine"
    COMPRESSOR = "compressor"
    EQUALIZER = "equalizer"
    CHANNEL_STRIP = "channel_strip"
    SYNTHESIZER = "synthesizer"
    PEDAL = "pedal"
    EURORACK = "eurorack"


@dataclass
class ConsoleConfig:
    """Configuration for a console type."""
    name: str
    console_type: ConsoleType
    width: float                    # mm
    height: float                   # mm
    default_knob_size: ElementSize
    default_button_size: ElementSize
    default_fader_size: ElementSize
    grid: GridSpacing = field(default_factory=GridSpacing)

    @property
    def width_meters(self) -> float:
        return self.width / 1000

    @property
    def height_meters(self) -> float:
        return self.height / 1000


# =============================================================================
# PREDEFINED CONSOLE CONFIGURATIONS
# =============================================================================

CONSOLE_CONFIGS: Dict[str, ConsoleConfig] = {
    # Mixing Consoles
    "neve_1073_channel": ConsoleConfig(
        name="Neve 1073 Channel Strip",
        console_type=ConsoleType.CHANNEL_STRIP,
        width=50.0,
        height=350.0,
        default_knob_size=ElementSize.LG,
        default_button_size=ElementSize.MD,
        default_fader_size=ElementSize.LG,
    ),

    "ssl_4000_channel": ConsoleConfig(
        name="SSL 4000 Channel Strip",
        console_type=ConsoleType.CHANNEL_STRIP,
        width=45.0,
        height=320.0,
        default_knob_size=ElementSize.MD,
        default_button_size=ElementSize.MD,
        default_fader_size=ElementSize.LG,
    ),

    "api_500_module": ConsoleConfig(
        name="API 500 Series Module",
        console_type=ConsoleType.CHANNEL_STRIP,
        width=FiveHundredSeries.SLOT_WIDTH,
        height=FiveHundredSeries.SLOT_HEIGHT,
        default_knob_size=ElementSize.MD,
        default_button_size=ElementSize.SM,
        default_fader_size=ElementSize.SM,
    ),

    # Drum Machines
    "roland_808": ConsoleConfig(
        name="Roland TR-808",
        console_type=ConsoleType.DRUM_MACHINE,
        width=480.0,
        height=120.0,
        default_knob_size=ElementSize.LG,
        default_button_size=ElementSize.MD,
        default_fader_size=ElementSize.MD,
    ),

    "roland_909": ConsoleConfig(
        name="Roland TR-909",
        console_type=ConsoleType.DRUM_MACHINE,
        width=480.0,
        height=130.0,
        default_knob_size=ElementSize.LG,
        default_button_size=ElementSize.MD,
        default_fader_size=ElementSize.MD,
    ),

    # Compressors
    "urei_1176": ConsoleConfig(
        name="UREI 1176 Compressor",
        console_type=ConsoleType.COMPRESSOR,
        width=RackStandard.WIDTH_19IN,
        height=RackStandard.u_height(2),
        default_knob_size=ElementSize.LG,
        default_button_size=ElementSize.MD,
        default_fader_size=ElementSize.SM,
    ),

    "la2a": ConsoleConfig(
        name="Teletronix LA-2A",
        console_type=ConsoleType.COMPRESSOR,
        width=RackStandard.WIDTH_19IN,
        height=RackStandard.u_height(3),
        default_knob_size=ElementSize.XL,
        default_button_size=ElementSize.LG,
        default_fader_size=ElementSize.MD,
    ),

    # Equalizers
    "pultec_eqp1a": ConsoleConfig(
        name="Pultec EQP-1A",
        console_type=ConsoleType.EQUALIZER,
        width=RackStandard.WIDTH_19IN,
        height=RackStandard.u_height(3),
        default_knob_size=ElementSize.LG,
        default_button_size=ElementSize.MD,
        default_fader_size=ElementSize.SM,
    ),

    # Synthesizers
    "minimoog": ConsoleConfig(
        name="Moog Minimoog Model D",
        console_type=ConsoleType.SYNTHESIZER,
        width=560.0,
        height=360.0,
        default_knob_size=ElementSize.LG,
        default_button_size=ElementSize.MD,
        default_fader_size=ElementSize.SM,
    ),

    # Pedals
    "boss_compact": ConsoleConfig(
        name="Boss Compact Pedal",
        console_type=ConsoleType.PEDAL,
        width=73.0,
        height=129.0,
        default_knob_size=ElementSize.SM,
        default_button_size=ElementSize.SM,
        default_fader_size=ElementSize.XS,
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_element_dimensions(
    element_type: str,
    size: ElementSize
) -> Tuple[float, float, float]:
    """
    Get (width, height, spacing) for an element type and size.

    Args:
        element_type: 'knob', 'button', 'fader', or 'led'
        size: ElementSize enum value

    Returns:
        Tuple of (width/diameter, height, recommended_spacing) in mm
    """
    if element_type == "knob":
        s = KNOB_SIZES[size]
        return (s.diameter, s.height, s.spacing)
    elif element_type == "button":
        s = BUTTON_SIZES[size]
        return (s.diameter, s.height, s.spacing)
    elif element_type == "fader":
        s = FADER_SIZES[size]
        return (s.knob_width, s.total_height, s.knob_width + 10)
    elif element_type == "led":
        s = LED_SIZES[size]
        return (s.diameter, s.height, s.spacing)
    else:
        raise ValueError(f"Unknown element type: {element_type}")


def calculate_row_positions(
    num_rows: int,
    row_spacing: float = DEFAULT_GRID.row_spacing,
    start_y: float = 0.0
) -> List[float]:
    """Calculate Y positions for multiple rows of elements."""
    return [start_y - (i * row_spacing) for i in range(num_rows)]


def calculate_column_positions(
    num_cols: int,
    element_spacing: float,
    start_x: float = 0.0
) -> List[float]:
    """Calculate X positions for multiple columns of elements."""
    return [start_x + (i * element_spacing) for i in range(num_cols)]


def fit_elements_in_width(
    available_width: float,
    element_spacing: float,
    margin: float = DEFAULT_GRID.panel_margin
) -> int:
    """Calculate how many elements fit in a given width."""
    usable_width = available_width - (2 * margin)
    return int(usable_width / element_spacing)
