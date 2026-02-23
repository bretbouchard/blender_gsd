"""
Layout System - Arrange console elements on panels.

Main components:
- standards: Industry-standard dimensions and spacing
- panel: Layout specification classes
- renderer: Generate Blender geometry from layouts
"""

from .standards import (
    # Rack standards
    RackStandard,
    FiveHundredSeries,

    # Size classes
    ElementSize,

    # Element size definitions
    KnobSize,
    ButtonSize,
    FaderSize,
    LEDSize,
    KNOB_SIZES,
    BUTTON_SIZES,
    FADER_SIZES,
    LED_SIZES,

    # Grid spacing
    GridSpacing,
    DEFAULT_GRID,

    # Console types
    ConsoleType,
    ConsoleConfig,
    CONSOLE_CONFIGS,

    # Helper functions
    get_element_dimensions,
    calculate_row_positions,
    calculate_column_positions,
    fit_elements_in_width,
)

from .panel import (
    # Element types
    ElementType,

    # Specifications
    ElementSpec,
    RowSpec,
    ColumnSpec,
    PanelLayout,

    # Builders
    ChannelStripBuilder,
    DrumMachineBuilder,
    CompressorBuilder,

    # Preset layouts
    create_neve_1073_channel,
    create_808_drum_machine,
    create_1176_compressor,
)

from .renderer import (
    LayoutRenderer,
    BatchRenderer,
    render_layout,
    render_console_row,
)


__all__ = [
    # Standards
    "RackStandard",
    "FiveHundredSeries",
    "ElementSize",
    "KnobSize",
    "ButtonSize",
    "FaderSize",
    "LEDSize",
    "KNOB_SIZES",
    "BUTTON_SIZES",
    "FADER_SIZES",
    "LED_SIZES",
    "GridSpacing",
    "DEFAULT_GRID",
    "ConsoleType",
    "ConsoleConfig",
    "CONSOLE_CONFIGS",
    "get_element_dimensions",
    "calculate_row_positions",
    "calculate_column_positions",
    "fit_elements_in_width",

    # Panel
    "ElementType",
    "ElementSpec",
    "RowSpec",
    "ColumnSpec",
    "PanelLayout",
    "ChannelStripBuilder",
    "DrumMachineBuilder",
    "CompressorBuilder",
    "create_neve_1073_channel",
    "create_808_drum_machine",
    "create_1176_compressor",

    # Renderer
    "LayoutRenderer",
    "BatchRenderer",
    "render_layout",
    "render_console_row",
]
