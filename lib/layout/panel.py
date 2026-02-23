"""
Panel Layout System - Arrange elements on console panels.

Supports:
- Grid-based layouts
- Channel strip layouts
- Free-form positioning
- Multi-row/multi-column arrangements
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Callable
from enum import Enum
import bpy

from .standards import (
    ElementSize, ConsoleType, ConsoleConfig,
    KNOB_SIZES, BUTTON_SIZES, FADER_SIZES, LED_SIZES,
    DEFAULT_GRID, get_element_dimensions,
    calculate_row_positions, calculate_column_positions,
    CONSOLE_CONFIGS
)


class ElementType(Enum):
    """Types of UI elements."""
    KNOB = "knob"
    BUTTON = "button"
    FADER = "fader"
    LED = "led"
    LABEL = "label"
    DISPLAY = "display"


@dataclass
class ElementSpec:
    """Specification for a single UI element."""
    element_type: ElementType
    name: str
    x: float              # mm from panel origin
    y: float              # mm from panel origin (0 = top)
    size: ElementSize = ElementSize.MD
    rotation: float = 0.0  # degrees
    label: str = ""
    value: float = 0.5     # Current value (0-1)
    style: int = 0         # Style variant index
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def to_meters(self) -> Tuple[float, float]:
        """Convert mm position to meters."""
        return (self.x / 1000, self.y / 1000)


@dataclass
class RowSpec:
    """Specification for a row of elements."""
    element_type: ElementType
    names: List[str]
    y: float                    # mm from top
    start_x: float = 0.0        # mm from left
    size: ElementSize = ElementSize.MD
    spacing: Optional[float] = None  # Override default spacing
    labels: List[str] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    styles: List[int] = field(default_factory=list)

    def to_element_specs(self, grid: DEFAULT_GRID.__class__ = DEFAULT_GRID) -> List[ElementSpec]:
        """Convert row to individual element specs."""
        if self.spacing is None:
            _, _, self.spacing = get_element_dimensions(
                self.element_type.value, self.size
            )

        specs = []
        for i, name in enumerate(self.names):
            x = self.start_x + (i * self.spacing)
            label = self.labels[i] if i < len(self.labels) else ""
            value = self.values[i] if i < len(self.values) else 0.5
            style = self.styles[i] if i < len(self.styles) else 0

            specs.append(ElementSpec(
                element_type=self.element_type,
                name=name,
                x=x,
                y=self.y,
                size=self.size,
                label=label,
                value=value,
                style=style,
            ))
        return specs


@dataclass
class ColumnSpec:
    """Specification for a column of elements."""
    element_type: ElementType
    names: List[str]
    x: float                    # mm from left
    start_y: float = 0.0        # mm from top
    size: ElementSize = ElementSize.MD
    spacing: Optional[float] = None
    labels: List[str] = field(default_factory=list)
    values: List[float] = field(default_factory=list)

    def to_element_specs(self, grid: DEFAULT_GRID.__class__ = DEFAULT_GRID) -> List[ElementSpec]:
        """Convert column to individual element specs."""
        if self.spacing is None:
            _, height, _ = get_element_dimensions(
                self.element_type.value, self.size
            )
            self.spacing = height + grid.row_spacing

        specs = []
        for i, name in enumerate(self.names):
            y = self.start_y + (i * self.spacing)
            label = self.labels[i] if i < len(self.labels) else ""
            value = self.values[i] if i < len(self.values) else 0.5

            specs.append(ElementSpec(
                element_type=self.element_type,
                name=name,
                x=self.x,
                y=y,
                size=self.size,
                label=label,
                value=value,
            ))
        return specs


@dataclass
class PanelLayout:
    """
    Complete panel layout specification.

    This is the main class for defining a console panel layout.
    """
    name: str
    width: float              # mm
    height: float             # mm
    console_type: ConsoleType = ConsoleType.MIXING_CONSOLE

    # Default sizes for this panel
    default_knob_size: ElementSize = ElementSize.MD
    default_button_size: ElementSize = ElementSize.MD
    default_fader_size: ElementSize = ElementSize.MD
    default_led_size: ElementSize = ElementSize.SM

    # Grid settings
    grid: DEFAULT_GRID.__class__ = field(default_factory=lambda: DEFAULT_GRID)

    # Elements
    elements: List[ElementSpec] = field(default_factory=list)
    rows: List[RowSpec] = field(default_factory=list)
    columns: List[ColumnSpec] = field(default_factory=list)

    # Style preset
    style_preset: str = "default"

    def add_element(self, element: ElementSpec) -> 'PanelLayout':
        """Add a single element. Returns self for chaining."""
        self.elements.append(element)
        return self

    def add_row(self, row: RowSpec) -> 'PanelLayout':
        """Add a row specification. Returns self for chaining."""
        self.rows.append(row)
        return self

    def add_column(self, column: ColumnSpec) -> 'PanelLayout':
        """Add a column specification. Returns self for chaining."""
        self.columns.append(column)
        return self

    def add_knob_row(
        self,
        names: List[str],
        y: float,
        start_x: float = None,
        size: ElementSize = None,
        spacing: float = None,
        labels: List[str] = None,
        values: List[float] = None
    ) -> 'PanelLayout':
        """Convenience method to add a row of knobs."""
        if start_x is None:
            start_x = self.grid.panel_margin
        if size is None:
            size = self.default_knob_size
        if labels is None:
            labels = []
        if values is None:
            values = []

        return self.add_row(RowSpec(
            element_type=ElementType.KNOB,
            names=names,
            y=y,
            start_x=start_x,
            size=size,
            spacing=spacing,
            labels=labels,
            values=values,
        ))

    def add_button_row(
        self,
        names: List[str],
        y: float,
        start_x: float = None,
        size: ElementSize = None,
        spacing: float = None,
        labels: List[str] = None,
        styles: List[int] = None
    ) -> 'PanelLayout':
        """Convenience method to add a row of buttons."""
        if start_x is None:
            start_x = self.grid.panel_margin
        if size is None:
            size = self.default_button_size
        if labels is None:
            labels = []
        if styles is None:
            styles = []

        return self.add_row(RowSpec(
            element_type=ElementType.BUTTON,
            names=names,
            y=y,
            start_x=start_x,
            size=size,
            spacing=spacing,
            labels=labels,
            styles=styles,
        ))

    def add_fader_column(
        self,
        names: List[str],
        x: float,
        start_y: float = None,
        size: ElementSize = None,
        spacing: float = None,
        values: List[float] = None
    ) -> 'PanelLayout':
        """Convenience method to add a column of faders."""
        if start_y is None:
            start_y = self.grid.panel_margin
        if size is None:
            size = self.default_fader_size
        if values is None:
            values = []

        return self.add_column(ColumnSpec(
            element_type=ElementType.FADER,
            names=names,
            x=x,
            start_y=start_y,
            size=size,
            spacing=spacing,
            values=values,
        ))

    def get_all_elements(self) -> List[ElementSpec]:
        """Get all elements including those from rows/columns."""
        all_elements = list(self.elements)

        for row in self.rows:
            all_elements.extend(row.to_element_specs(self.grid))

        for col in self.columns:
            all_elements.extend(col.to_element_specs(self.grid))

        return all_elements

    @property
    def width_meters(self) -> float:
        return self.width / 1000

    @property
    def height_meters(self) -> float:
        return self.height / 1000


# =============================================================================
# CHANNEL STRIP BUILDER
# =============================================================================

class ChannelStripBuilder:
    """
    Build standard channel strip layouts.

    Example usage:
        builder = ChannelStripBuilder("Neve Style", width=50)
        builder.add_input_section()
        builder.add_eq_section(bands=4)
        builder.add_dynamics_section()
        builder.add_fader()
        layout = builder.build()
    """

    def __init__(
        self,
        name: str,
        width: float = 50.0,
        height: float = 350.0,
        knob_size: ElementSize = ElementSize.MD,
        button_size: ElementSize = ElementSize.SM,
        fader_size: ElementSize = ElementSize.LG,
    ):
        self.layout = PanelLayout(
            name=name,
            width=width,
            height=height,
            console_type=ConsoleType.CHANNEL_STRIP,
            default_knob_size=knob_size,
            default_button_size=button_size,
            default_fader_size=fader_size,
        )
        self._current_y = self.layout.grid.panel_margin

    def _next_row_y(self, spacing: float = None) -> float:
        """Get Y position for next row and advance."""
        y = self._current_y
        if spacing is None:
            spacing = self.layout.grid.row_spacing
        self._current_y += spacing
        return y

    def add_knob_row(
        self,
        names: List[str],
        size: ElementSize = None,
        labels: List[str] = None,
        spacing: float = None
    ) -> 'ChannelStripBuilder':
        """Add a row of knobs at current position."""
        y = self._next_row_y()
        self.layout.add_knob_row(names, y, size=size, labels=labels, spacing=spacing)
        return self

    def add_button_row(
        self,
        names: List[str],
        size: ElementSize = None,
        styles: List[int] = None
    ) -> 'ChannelStripBuilder':
        """Add a row of buttons at current position."""
        y = self._next_row_y()
        self.layout.add_button_row(names, y, size=size, styles=styles)
        return self

    def add_section_gap(self, gap: float = None) -> 'ChannelStripBuilder':
        """Add vertical gap between sections."""
        if gap is None:
            gap = self.layout.grid.section_spacing
        self._current_y += gap
        return self

    def add_label(self, text: str, y: float = None) -> 'ChannelStripBuilder':
        """Add a section label."""
        if y is None:
            y = self._current_y - 5  # Slightly above current position

        self.layout.add_element(ElementSpec(
            element_type=ElementType.LABEL,
            name=f"label_{text}",
            x=self.layout.width / 2,
            y=y,
            label=text,
        ))
        return self

    def add_fader(
        self,
        name: str = "fader",
        height_fraction: float = 0.4,
        value: float = 0.75
    ) -> 'ChannelStripBuilder':
        """Add the main channel fader."""
        # Fader takes remaining space
        fader_height = self.layout.height - self._current_y - self.layout.grid.panel_margin
        fader_y = self._current_y + (fader_height * (1 - height_fraction))

        self.layout.add_element(ElementSpec(
            element_type=ElementType.FADER,
            name=name,
            x=self.layout.width / 2,
            y=fader_y,
            size=self.layout.default_fader_size,
            value=value,
        ))
        return self

    def build(self) -> PanelLayout:
        """Return the completed layout."""
        return self.layout


# =============================================================================
# DRUM MACHINE BUILDER
# =============================================================================

class DrumMachineBuilder:
    """
    Build drum machine layouts (808/909 style).
    """

    def __init__(
        self,
        name: str,
        width: float = 480.0,
        height: float = 120.0,
        num_voices: int = 16,
    ):
        self.layout = PanelLayout(
            name=name,
            width=width,
            height=height,
            console_type=ConsoleType.DRUM_MACHINE,
            default_knob_size=ElementSize.LG,
            default_button_size=ElementSize.MD,
            default_fader_size=ElementSize.SM,
        )
        self.num_voices = num_voices
        self._voices = []

    def add_voice(
        self,
        name: str,
        knobs: List[str],
        buttons: List[str] = None,
        led: bool = True
    ) -> 'DrumMachineBuilder':
        """Add a voice/instrument section."""
        self._voices.append({
            "name": name,
            "knobs": knobs,
            "buttons": buttons or [],
            "led": led,
        })
        return self

    def build(self) -> PanelLayout:
        """Build the drum machine layout."""
        if not self._voices:
            return self.layout

        # Calculate spacing
        voice_width = self.layout.width / len(self._voices)

        for i, voice in enumerate(self._voices):
            x_center = (i * voice_width) + (voice_width / 2)

            # Add knobs vertically
            knob_size = KNOB_SIZES[self.layout.default_knob_size]
            knob_spacing = knob_size.height + 8

            for j, knob_name in enumerate(voice["knobs"]):
                y = self.layout.grid.panel_margin + (j * knob_spacing)
                self.layout.add_element(ElementSpec(
                    element_type=ElementType.KNOB,
                    name=f"{voice['name']}_{knob_name}",
                    x=x_center,
                    y=y,
                    size=self.layout.default_knob_size,
                    label=knob_name,
                ))

        return self.layout


# =============================================================================
# COMPRESSOR BUILDER
# =============================================================================

class CompressorBuilder:
    """
    Build compressor layouts (1176/LA-2A style).
    """

    def __init__(
        self,
        name: str,
        width: float = 482.6,  # 19" rack
        height: float = 88.9,  # 2U
        style: str = "1176"    # "1176" or "la2a"
    ):
        self.layout = PanelLayout(
            name=name,
            width=width,
            height=height,
            console_type=ConsoleType.COMPRESSOR,
            default_knob_size=ElementSize.LG,
            default_button_size=ElementSize.MD,
            default_fader_size=ElementSize.SM,
        )
        self.style = style

    def add_1176_layout(self) -> 'CompressorBuilder':
        """Add 1176-style layout (4 knobs + 4 buttons + meters)."""
        margin = self.layout.grid.panel_margin
        y_knobs = margin + 20
        y_buttons = self.layout.height - margin - 30

        # 4 main knobs: Input, Output, Attack, Release
        knob_names = ["Input", "Output", "Attack", "Release"]
        knob_spacing = (self.layout.width - 2 * margin) / (len(knob_names) + 1)

        for i, name in enumerate(knob_names):
            x = margin + ((i + 1) * knob_spacing)
            self.layout.add_element(ElementSpec(
                element_type=ElementType.KNOB,
                name=name,
                x=x,
                y=y_knobs,
                size=ElementSize.LG,
                label=name,
            ))

        # 4 ratio buttons
        ratio_values = ["4:1", "8:1", "12:1", "20:1"]
        button_spacing = (self.layout.width - 2 * margin) / (len(ratio_values) + 1)

        for i, ratio in enumerate(ratio_values):
            x = margin + ((i + 1) * button_spacing)
            self.layout.add_element(ElementSpec(
                element_type=ElementType.BUTTON,
                name=f"ratio_{ratio}",
                x=x,
                y=y_buttons,
                size=ElementSize.MD,
                label=ratio,
            ))

        return self

    def add_la2a_layout(self) -> 'CompressorBuilder':
        """Add LA-2A style layout (2 large knobs + meter)."""
        margin = self.layout.grid.panel_margin
        y_knobs = margin + 40

        # Left: Gain, Right: Peak Reduction
        x_gain = self.layout.width * 0.25
        x_peak = self.layout.width * 0.75

        self.layout.add_element(ElementSpec(
            element_type=ElementType.KNOB,
            name="Gain",
            x=x_gain,
            y=y_knobs,
            size=ElementSize.XL,
            label="Gain",
        ))

        self.layout.add_element(ElementSpec(
            element_type=ElementType.KNOB,
            name="Peak_Reduction",
            x=x_peak,
            y=y_knobs,
            size=ElementSize.XL,
            label="Peak Reduction",
        ))

        # VU Meter in center
        self.layout.add_element(ElementSpec(
            element_type=ElementType.DISPLAY,
            name="VU_Meter",
            x=self.layout.width / 2,
            y=self.layout.height - margin - 40,
            size=ElementSize.LG,
        ))

        return self

    def build(self) -> PanelLayout:
        """Build the compressor layout."""
        if self.style == "1176":
            self.add_1176_layout()
        elif self.style == "la2a":
            self.add_la2a_layout()
        return self.layout


# =============================================================================
# PRESET LAYOUTS
# =============================================================================

def create_neve_1073_channel() -> PanelLayout:
    """Create a Neve 1073 style channel strip layout."""
    builder = ChannelStripBuilder(
        name="Neve 1073 Channel",
        width=50.0,
        height=350.0,
        knob_size=ElementSize.LG,
        button_size=ElementSize.MD,
        fader_size=ElementSize.LG,
    )

    # Input section
    builder.add_label("INPUT")
    builder.add_knob_row(["Gain", "Trim"])
    builder.add_button_row(["48V", "Phase", "Pad"])
    builder.add_section_gap(30)

    # EQ section
    builder.add_label("EQ")
    builder.add_knob_row(["HF_Freq", "HF_Gain"])
    builder.add_knob_row(["MF_Freq", "MF_Gain"])
    builder.add_knob_row(["LF_Freq", "LF_Gain"])
    builder.add_button_row(["EQ_In"])
    builder.add_section_gap(30)

    # Fader
    builder.add_fader("Channel_Fader")

    return builder.build()


def create_808_drum_machine() -> PanelLayout:
    """Create a Roland TR-808 style drum machine layout."""
    builder = DrumMachineBuilder(
        name="Roland TR-808",
        width=480.0,
        height=120.0,
        num_voices=16,
    )

    # Add 16 voices with typical 808 controls
    voices = [
        ("Kick", ["Level", "Tone", "Decay"]),
        ("Snare", ["Level", "Tone", "Snappy"]),
        ("LoConga", ["Level", "Tone"]),
        ("HiConga", ["Level", "Tone"]),
        ("Claves", ["Level", "Tone"]),
        ("Maracas", ["Level"]),
        ("Cowbell", ["Level", "Tone"]),
        ("Cymbal", ["Level", "Tone", "Decay"]),
        ("Rimshot", ["Level", "Tone"]),
        ("Clap", ["Level", "Tone"]),
        ("LoTom", ["Level", "Tone", "Decay"]),
        ("MidTom", ["Level", "Tone", "Decay"]),
        ("HiTom", ["Level", "Tone", "Decay"]),
        ("Cl_Hat", ["Level", "Tone"]),
        ("Op_Hat", ["Level", "Tone", "Decay"]),
        ("Ride", ["Level", "Tone"]),
    ]

    for name, knobs in voices:
        builder.add_voice(name, knobs)

    return builder.build()


def create_1176_compressor() -> PanelLayout:
    """Create a UREI 1176 style compressor layout."""
    builder = CompressorBuilder(
        name="UREI 1176",
        width=482.6,
        height=88.9,
        style="1176"
    )
    return builder.build()
