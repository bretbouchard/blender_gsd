"""
Compositor Effects Module - Codified from Tutorial 22

Implements compositor node setups for post-processing effects
including bloom, glare, lens distortion, and color grading.

Based on tutorial: Compositor Effects (Section 22)

Usage:
    from lib.compositing import CompositorSetup, BloomEffect

    # Setup compositor
    compositor = CompositorSetup()
    compositor.enable_nodes()
    compositor.add_bloom(threshold=0.8, intensity=0.5)
    compositor.add_glare(type='FOG_GLOW')
    compositor.add_color_grading(contrast=1.1, saturation=1.2)
"""

from __future__ import annotations
import bpy
from typing import Optional, Tuple, List, Dict
from pathlib import Path


class CompositorSetup:
    """
    Compositor node tree setup for post-processing.

    Cross-references:
    - KB Section 22: Compositor Effects
    """

    def __init__(self):
        self._scene = bpy.context.scene
        self._nodes: dict = {}
        self._links: dict = {}

    def enable_nodes(self) -> "CompositorSetup":
        """
        Enable compositing nodes on the scene.

        KB Reference: Section 22 - Node-based compositing

        Returns:
            Self for chaining
        """
        self._scene.use_nodes = True
        self._nodes = {}
        return self

    def get_node_tree(self) -> Optional[bpy.types.CompositorNodeTree]:
        """Get the compositor node tree."""
        return self._scene.node_tree

    def clear_existing(self) -> "CompositorSetup":
        """Clear existing compositor nodes."""
        if self._scene.node_tree:
            self._scene.node_tree.nodes.clear()
        self._nodes = {}
        return self

    def add_bloom(
        self,
        threshold: float = 0.8,
        intensity: float = 0.5,
        size: float = 0.5
    ) -> "CompositorSetup":
        """
        Add bloom effect using glare node.

        KB Reference: Section 22 - Bloom effect

        Args:
            threshold: Brightness threshold
            intensity: Bloom intensity
            size: Bloom size

        Returns:
            Self for chaining
        """
        tree = self.get_node_tree()
        if not tree:
            return self

        # Create glare node
        glare = tree.nodes.new('CompositorNodeGlare')
        glare.glare_type = 'BLOOM'
        glare.threshold = threshold
        glare.mix = -intensity  # Negative for additive
        glare.size = int(size * 10)  # Scale to 1-10 range

        self._nodes['bloom'] = glare
        return self

    def add_glare(
        self,
        glare_type: str = 'FOG_GLOW',
        threshold: float = 1.0,
        intensity: float = 0.3,
        streaks: int = 4
    ) -> "CompositorSetup":
        """
        Add glare effect.

        KB Reference: Section 22 - Glare types

        Args:
            glare_type: 'BLOOM', 'FOG_GLOW', 'STREAKS', 'GHOSTS'
            threshold: Brightness threshold
            intensity: Glare intensity
            streaks: Number of streaks (for STREAKS type)

        Returns:
            Self for chaining
        """
        tree = self.get_node_tree()
        if not tree:
            return self

        glare = tree.nodes.new('CompositorNodeGlare')
        glare.glare_type = glare_type
        glare.threshold = threshold
        glare.mix = -intensity

        if glare_type == 'STREAKS':
            glare.streaks = streaks

        self._nodes['glare'] = glare
        return self

    def add_color_grading(
        self,
        contrast: float = 1.0,
        saturation: float = 1.0,
        brightness: float = 0.0,
        gamma: float = 1.0,
        lift: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        gamma_color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        gain: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    ) -> "CompositorSetup":
        """
        Add color grading using color balance and curves.

        KB Reference: Section 22 - Color grading

        Args:
            contrast: Contrast multiplier
            saturation: Saturation multiplier
            brightness: Brightness offset
            gamma: Gamma correction
            lift: Lift (shadows) RGB offset
            gamma_color: Gamma (midtones) RGB multiplier
            gain: Gain (highlights) RGB multiplier

        Returns:
            Self for chaining
        """
        tree = self.get_node_tree()
        if not tree:
            return self

        # Brightness/Contrast node
        bc = tree.nodes.new('CompositorNodeBrightContrast')
        bc.bright = brightness
        bc.contrast = contrast
        self._nodes['bright_contrast'] = bc

        # Saturation (Hue Correct or Color Balance)
        # Using Color Balance for lift/gamma/gain
        color_bal = tree.nodes.new('CompositorNodeColorBalance')
        color_bal.correction_method = 'LIFT_GAMMA_GAIN'
        color_bal.lift = lift
        color_bal.gamma = gamma_color
        color_bal.gain = gain
        self._nodes['color_balance'] = color_bal

        # Gamma correction
        gamma_node = tree.nodes.new('CompositorNodeGamma')
        gamma_node.inputs[1].default_value = gamma
        self._nodes['gamma'] = gamma_node

        # Saturation (using Hue Saturation Value node)
        hsv = tree.nodes.new('CompositorNodeHueSat')
        hsv.saturation = saturation
        self._nodes['hsv'] = hsv

        return self

    def add_lens_distortion(
        self,
        distortion: float = 0.1,
        dispersion: float = 0.0
    ) -> "CompositorSetup":
        """
        Add lens distortion effect.

        KB Reference: Section 22 - Lens effects

        Args:
            distortion: Distortion amount
            dispersion: Chromatic dispersion

        Returns:
            Self for chaining
        """
        tree = self.get_node_tree()
        if not tree:
            return self

        lens = tree.nodes.new('CompositorNodeLensdist')
        lens.use_distortion = True
        lens.distortion = distortion

        if dispersion > 0:
            lens.use_jitter = True
            lens.dispersion = dispersion

        self._nodes['lens_distortion'] = lens
        return self

    def add_vignette(
        self,
        strength: float = 0.5,
        size: float = 0.5
    ) -> "CompositorSetup":
        """
        Add vignette effect.

        KB Reference: Section 22 - Vignette

        Args:
            strength: Vignette strength
            size: Vignette size (0-1)

        Returns:
            Self for chaining
        """
        tree = self.get_node_tree()
        if not tree:
            return self

        # Create vignette using ellipse mask and mix
        ellipse = tree.nodes.new('CompositorNodeEllipseMask')
        ellipse.width = size
        ellipse.height = size
        ellipse.rotation = 0.0
        self._nodes['vignette_mask'] = ellipse

        # Mix node to apply vignette
        mix = tree.nodes.new('CompositorNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        self._nodes['vignette_mix'] = mix

        return self

    def add_film_grain(
        self,
        strength: float = 0.1,
        size: float = 1.0
    ) -> "CompositorSetup":
        """
        Add film grain effect.

        KB Reference: Section 22 - Film grain

        Args:
            strength: Grain strength
            size: Grain size

        Returns:
            Self for chaining
        """
        tree = self.get_node_tree()
        if not tree:
            return self

        # Noise texture for grain
        noise = tree.nodes.new('CompositorNodeNoise')
        noise.noise_type = 'ANISO'
        noise.scale = size * 100  # Scale up for visible grain

        # Mix with original
        mix = tree.nodes.new('CompositorNodeMixRGB')
        mix.blend_type = 'OVERLAY'
        mix.fac = strength

        self._nodes['grain_noise'] = noise
        self._nodes['grain_mix'] = mix

        return self

    def add_chromatic_aberration(
        self,
        strength: float = 0.01
    ) -> "CompositorSetup":
        """
        Add chromatic aberration effect.

        KB Reference: Section 22 - Chromatic aberration

        Args:
            strength: Aberration strength

        Returns:
            Self for chaining
        """
        tree = self.get_node_tree()
        if not tree:
            return self

        # Use lens distortion with dispersion
        lens = tree.nodes.new('CompositorNodeLensdist')
        lens.use_jitter = True
        lens.dispersion = strength

        self._nodes['chromatic'] = lens
        return self

    def add_depth_of_field(
        self,
        focal_distance: float = 10.0,
        f_stop: float = 2.8,
        max_blur: float = 10.0
    ) -> "CompositorSetup":
        """
        Add depth of field blur.

        KB Reference: Section 22 - DOF in compositor

        Args:
            focal_distance: Focus distance
            f_stop: Aperture f-stop
            max_blur: Maximum blur radius

        Returns:
            Self for chaining
        """
        tree = self.get_node_tree()
        if not tree:
            return self

        # Defocus node
        defocus = tree.nodes.new('CompositorNodeDefocus')
        defocus.f_stop = f_stop
        defocus.max_blur = max_blur
        defocus.use_zbuffer = True

        self._nodes['defocus'] = defocus
        return self

    def get_node(self, name: str) -> Optional[bpy.types.Node]:
        """Get a created node by name."""
        return self._nodes.get(name)


class BloomEffect:
    """
    Standalone bloom effect setup.

    Cross-references:
    - KB Section 22: Bloom configuration
    """

    @staticmethod
    def create_bloom_setup(
        threshold: float = 0.8,
        intensity: float = 0.5,
        size: int = 5
    ) -> Dict:
        """
        Get bloom configuration.

        Args:
            threshold: Brightness threshold
            intensity: Bloom intensity
            size: Bloom kernel size (1-10)

        Returns:
            Bloom configuration dictionary
        """
        return {
            "type": "BLOOM",
            "threshold": threshold,
            "intensity": intensity,
            "size": size,
            "node": "CompositorNodeGlare"
        }

    @staticmethod
    def get_presets() -> Dict:
        """Get bloom presets."""
        return {
            "subtle": {"threshold": 0.9, "intensity": 0.2, "size": 3},
            "normal": {"threshold": 0.8, "intensity": 0.5, "size": 5},
            "strong": {"threshold": 0.6, "intensity": 0.8, "size": 8},
            "dreamy": {"threshold": 0.5, "intensity": 1.0, "size": 10}
        }


class ColorGrading:
    """
    Color grading presets and utilities.

    Cross-references:
    - KB Section 22: Color grading
    """

    @staticmethod
    def get_look_presets() -> Dict:
        """Get color grading look presets."""
        return {
            "cinematic": {
                "contrast": 1.1,
                "saturation": 0.9,
                "lift": (0.02, 0.01, 0.0),  # Slightly warm shadows
                "gamma": (1.0, 0.98, 0.95),  # Slightly cool midtones
                "gain": (1.05, 1.0, 0.95)   # Warm highlights
            },
            "vintage": {
                "contrast": 0.95,
                "saturation": 0.8,
                "lift": (0.05, 0.02, -0.02),
                "gamma": (0.95, 0.9, 0.85),
                "gain": (1.0, 0.95, 0.9)
            },
            "high_contrast": {
                "contrast": 1.3,
                "saturation": 1.1,
                "lift": (-0.05, -0.05, -0.05),
                "gamma": (1.0, 1.0, 1.0),
                "gain": (1.1, 1.1, 1.1)
            },
            "bleach_bypass": {
                "contrast": 1.2,
                "saturation": 0.7,
                "lift": (0.0, 0.0, 0.0),
                "gamma": (1.0, 1.0, 1.0),
                "gain": (1.0, 1.0, 1.0)
            },
            "teal_orange": {
                "contrast": 1.1,
                "saturation": 1.1,
                "lift": (0.0, 0.02, 0.05),  # Teal shadows
                "gamma": (1.0, 0.95, 0.9),
                "gain": (1.05, 0.95, 0.85)  # Orange highlights
            }
        }


class GlareTypes:
    """
    Glare type reference and presets.

    Cross-references:
    - KB Section 22: Glare types
    """

    @staticmethod
    def get_glare_types() -> Dict:
        """Get available glare types and their characteristics."""
        return {
            "BLOOM": {
                "description": "Soft, even glow around bright areas",
                "use_case": "General glow, dreamy look",
                "settings": ["threshold", "mix", "size"]
            },
            "FOG_GLOW": {
                "description": "Atmospheric glow with soft edges",
                "use_case": "Outdoor scenes, atmosphere",
                "settings": ["threshold", "mix", "size"]
            },
            "STREAKS": {
                "description": "Horizontal/vertical light streaks",
                "use_case": "Anamorphic look, lenses",
                "settings": ["threshold", "mix", "streaks", "angle_offset"]
            },
            "GHOSTS": {
                "description": "Multiple ghost images of bright spots",
                "use_case": "Lens flare effect",
                "settings": ["threshold", "mix", "size"]
            }
        }

    @staticmethod
    def get_anamorphic_preset() -> Dict:
        """Get anamorphic streak preset."""
        return {
            "type": "STREAKS",
            "threshold": 0.9,
            "streaks": 4,
            "angle_offset": 0,
            "mix": 0.3,
            "description": "Classic anamorphic lens streaks"
        }


class CompositorWorkflow:
    """
    Complete compositor workflow setup.

    Cross-references:
    - KB Section 22: Full workflow
    """

    @staticmethod
    def setup_basic_post() -> "CompositorSetup":
        """
        Setup basic post-processing stack.

        KB Reference: Section 22 - Basic workflow

        Returns:
            Configured CompositorSetup
        """
        compositor = CompositorSetup()
        compositor.enable_nodes()
        compositor.add_bloom(threshold=0.8, intensity=0.3)
        compositor.add_color_grading(contrast=1.05, saturation=1.0)
        compositor.add_vignette(strength=0.3, size=0.6)
        return compositor

    @staticmethod
    def setup_cinematic() -> "CompositorSetup":
        """
        Setup cinematic post-processing.

        KB Reference: Section 22 - Cinematic look

        Returns:
            Configured CompositorSetup
        """
        compositor = CompositorSetup()
        compositor.enable_nodes()

        # Color grading
        cinematic = ColorGrading.get_look_presets()["cinematic"]
        compositor.add_color_grading(
            contrast=cinematic["contrast"],
            saturation=cinematic["saturation"],
            lift=cinematic["lift"],
            gamma_color=cinematic["gamma"],
            gain=cinematic["gain"]
        )

        # Subtle bloom
        compositor.add_bloom(threshold=0.85, intensity=0.2)

        # Film grain
        compositor.add_film_grain(strength=0.05)

        # Vignette
        compositor.add_vignette(strength=0.4, size=0.5)

        # Slight chromatic aberration
        compositor.add_chromatic_aberration(strength=0.005)

        return compositor

    @staticmethod
    def get_node_order() -> List[str]:
        """Get recommended node order in compositor."""
        return [
            "1. Render Layers (input)",
            "2. Color Balance / Lift Gamma Gain",
            "3. Brightness/Contrast",
            "4. Curves (if needed)",
            "5. Glare/Bloom",
            "6. Lens Distortion",
            "7. Chromatic Aberration",
            "8. Film Grain",
            "9. Vignette",
            "10. Composite (output)"
        ]


# Convenience functions
def setup_basic_compositing() -> CompositorSetup:
    """Quick setup for basic post-processing."""
    return CompositorWorkflow.setup_basic_post()


def setup_cinematic_compositing() -> CompositorSetup:
    """Quick setup for cinematic look."""
    return CompositorWorkflow.setup_cinematic()


def add_bloom(threshold: float = 0.8, intensity: float = 0.5) -> CompositorSetup:
    """Quick add bloom effect."""
    compositor = CompositorSetup()
    compositor.enable_nodes()
    compositor.add_bloom(threshold, intensity)
    return compositor


def get_quick_reference() -> Dict:
    """Get quick reference for compositing."""
    return {
        "essential_nodes": ["Glare", "Color Balance", "Curves"],
        "bloom_defaults": {"threshold": 0.8, "intensity": 0.5},
        "grading_order": "Lift → Gamma → Gain",
        "output": "Always end with Composite node"
    }


class CompositorHUD:
    """
    Heads-Up Display for compositor node visualization.

    Cross-references:
    - KB Section 22: Node order visualization
    """

    @staticmethod
    def display_node_pipeline() -> str:
        """
        Display the recommended compositor node pipeline.

        KB Reference: Section 22 - Node order

        Returns:
            Formatted pipeline display
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'COMPOSITOR NODE PIPELINE':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        pipeline = [
            ("INPUT", "Render Layers", "Source image data"),
            ("COLOR", "Color Balance", "Lift/Gamma/Gain correction"),
            ("COLOR", "Brightness/Contrast", "Tonal adjustments"),
            ("COLOR", "Curves", "Fine-tuned control (optional)"),
            ("EFFECT", "Glare/Bloom", "Light bloom effect"),
            ("EFFECT", "Lens Distortion", "Barrel/pincushion distortion"),
            ("EFFECT", "Chromatic Aberration", "Color fringing"),
            ("EFFECT", "Film Grain", "Add texture/noise"),
            ("EFFECT", "Vignette", "Edge darkening"),
            ("OUTPUT", "Composite", "Final output"),
        ]

        current_stage = None
        for stage, node, desc in pipeline:
            if stage != current_stage:
                if current_stage is not None:
                    lines.append("├" + "─" * 48 + "┤")
                lines.append(f"║ [{stage}]")
                current_stage = stage

            lines.append(f"║   → {node:<20} - {desc:<20}│")

        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)

    @staticmethod
    def display_effect_comparison() -> str:
        """
        Display effect comparison table.

        KB Reference: Section 22 - Effect types

        Returns:
            Formatted comparison table
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'COMPOSITOR EFFECTS COMPARISON':^48}│")
        lines.append("├" + "─" + "─" * 15 + "─" + "─" * 28 + "┤")

        effects = [
            ("Bloom", "Soft glow", "Dreamy, ethereal look"),
            ("Fog Glow", "Atmospheric", "Outdoor, hazy scenes"),
            ("Streaks", "Anamorphic", "Lens flare, cinematic"),
            ("Ghosts", "Multi-image", "Strong lens effects"),
            ("Vignette", "Edge darkening", "Focus to center"),
            ("Film Grain", "Texture", "Vintage, organic feel"),
            ("Chromatic", "Color fringe", "Lens imperfection"),
        ]

        for effect, desc, use in effects:
            lines.append(f"│ {effect:<15} │ {desc:<12} │ {use:<13}│")

        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_color_grading_wheel() -> str:
        """
        Display color grading adjustment reference.

        KB Reference: Section 22 - Color grading

        Returns:
            Formatted color grading reference
        """
        lines = []
        lines.append("┌" + "─" * 48 + "┐")
        lines.append(f"│{'COLOR GRADING REFERENCE':^48}│")
        lines.append("├" + "─" * 48 + "┤")

        adjustments = [
            ("LIFT (Shadows)", [
                "• Increases: Darker shadows, more contrast",
                "• Color tint: Affects shadow color",
                "• Typical: Slight blue/teal for cool look"
            ]),
            ("GAMMA (Midtones)", [
                "• Increases: Brighter midtones",
                "• Color tint: Affects overall color balance",
                "• Typical: Neutral or slight adjustment"
            ]),
            ("GAIN (Highlights)", [
                "• Increases: Brighter highlights",
                "• Color tint: Affects highlight color",
                "• Typical: Slight warm (orange/yellow)"
            ]),
        ]

        for name, tips in adjustments:
            lines.append(f"│ {name}:")
            for tip in tips:
                lines.append(f"│   {tip:<44}│")
            lines.append("│" + " " * 48 + "│")

        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_presets_overview() -> str:
        """
        Display available presets overview.

        KB Reference: Section 22 - Presets

        Returns:
            Formatted presets overview
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'COMPOSITOR PRESETS':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        presets = [
            ("Bloom", ["subtle", "normal", "strong", "dreamy"]),
            ("Color Grading", ["cinematic", "vintage", "high_contrast",
                               "bleach_bypass", "teal_orange"]),
        ]

        for category, preset_list in presets:
            lines.append(f"║ {category}:")
            for preset in preset_list:
                lines.append(f"║   • {preset}")
            lines.append("║" + " " * 50 + "║")

        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """
        Display compositor setup checklist.

        KB Reference: Section 22 - Setup checklist

        Returns:
            Formatted checklist
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'COMPOSITOR SETUP CHECKLIST':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        checklist = [
            ("Setup", [
                "☐ Enable Use Nodes in compositor",
                "☐ Check Render Layers connected",
                "☐ Verify Composite output exists",
            ]),
            ("Color", [
                "☐ Set white balance / temperature",
                "☐ Adjust contrast if needed",
                "☐ Check saturation levels",
            ]),
            ("Effects", [
                "☐ Add bloom for highlights (if needed)",
                "☐ Add vignette for focus",
                "☐ Consider film grain for texture",
            ]),
            ("Output", [
                "☐ Verify final Composite node",
                "☐ Check render resolution",
                "☐ Test with different scenes",
            ]),
        ]

        for category, items in checklist:
            lines.append(f"║ {category}:")
            for item in items:
                lines.append(f"║   {item}")
            lines.append("║" + " " * 50 + "║")

        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)


def print_node_pipeline() -> None:
    """Print compositor node pipeline to console."""
    print(CompositorHUD.display_node_pipeline())


def print_effect_comparison() -> None:
    """Print effect comparison table to console."""
    print(CompositorHUD.display_effect_comparison())
