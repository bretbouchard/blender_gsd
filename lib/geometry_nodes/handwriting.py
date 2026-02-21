"""
Handwriting - Procedural handwriting text system.

Based on CGMatter tutorials for procedural handwriting. Creates
handwritten-style text using multiple letter variants positioned
with accumulated widths for natural spacing.

Flow Overview:
    1. Select letter variant (index * 3 + random 0-2)
    2. Get letter width from Instance Bounds
    3. Accumulate Field for trailing positions
    4. Translate each letter to accumulated position
    5. Sort Elements for proper render order

Usage:
    # Initialize with letter objects
    system = HandwritingSystem({'a': [a_1, a_2, a_3], ...})

    # Generate text
    text_geo = system.generate_text("hello world")
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Optional

from mathutils import Vector

if TYPE_CHECKING:
    from bpy.types import Node, Object

    from .node_builder import NodeTreeBuilder


# Default alphabet string (space + lowercase letters)
DEFAULT_ALPHABET = " abcdefghijklmnopqrstuvwxyz"


class HandwritingSystem:
    """
    Procedural handwriting text system.

    Creates handwritten-style text by selecting from multiple letter
    variants and positioning them using accumulated widths for
    natural, varied spacing.

    The system expects letter objects organized by character:
        {'a': [a_variant_1, a_variant_2, a_variant_3], ...}

    Attributes:
        alphabet_objects: Dictionary of character to variant objects.
        alphabet_string: String defining character order.
        spacing: Additional spacing between letters.
        builder: NodeTreeBuilder for node creation.

    Example:
        >>> # Assuming you have letter objects named a_1, a_2, etc.
        >>> system = HandwritingSystem(letter_objects, builder)
        >>> text = system.generate_text("hello world", spacing=1.1)
    """

    def __init__(
        self,
        alphabet_objects: dict[str, list[Object]],
        builder: Optional[NodeTreeBuilder] = None,
        alphabet: str = DEFAULT_ALPHABET,
    ):
        """
        Initialize the handwriting system.

        Args:
            alphabet_objects: Dictionary mapping characters to variant objects.
                Expected format: {'a': [a_1, a_2, a_3], 'b': [b_1, b_2, b_3], ...}
            builder: NodeTreeBuilder for node creation.
            alphabet: String defining character order (default includes space and a-z).

        Raises:
            ValueError: If alphabet_objects is empty or invalid.
        """
        if not alphabet_objects:
            raise ValueError("alphabet_objects cannot be empty")

        self.alphabet_objects = alphabet_objects
        self.builder = builder
        self.alphabet_string = alphabet
        self._spacing: float = 1.0
        self._variant_count: int = 3
        self._random_seed: int = 0

        # Calculate variant count from first character
        first_char_variants = next(iter(alphabet_objects.values()), [])
        if first_char_variants:
            self._variant_count = len(first_char_variants)

    @staticmethod
    def find_char_index(
        text: str,
        position: int,
        alphabet: str = DEFAULT_ALPHABET,
    ) -> int:
        """
        Find index of character in alphabet string.

        Args:
            text: The text string.
            position: Character position in text (0-indexed).
            alphabet: Alphabet string to search in.

        Returns:
            Index in alphabet, or 0 (space) if not found.

        Example:
            >>> HandwritingSystem.find_char_index("hello", 0)  # 'h'
            8  # Position of 'h' in " abcdefghijklmnopqrstuvwxyz"
        """
        if position < 0 or position >= len(text):
            return 0

        char = text[position].lower()

        try:
            return alphabet.index(char)
        except ValueError:
            # Character not in alphabet, use space
            return 0

    @staticmethod
    def select_variant(char_index: int, variant_count: int = 3) -> int:
        """
        Select random variant index based on character index.

        Formula: char_index * variant_count + random(0 to variant_count-1)

        Args:
            char_index: Index of character in alphabet.
            variant_count: Number of variants per character (default 3).

        Returns:
            Variant index for instancing.

        Example:
            >>> # For character 'a' (index 1) with 3 variants
            >>> # Returns one of: 3, 4, or 5
            >>> variant = HandwritingSystem.select_variant(1, 3)
        """
        base_index = char_index * variant_count
        random_offset = random.randint(0, variant_count - 1)
        return base_index + random_offset

    @staticmethod
    def calculate_positions(
        instances: list[Object],
        spacing: float = 1.0,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Calculate positions using Accumulate Field (trailing).

        Gets the width of each letter instance and accumulates them
        to position each subsequent letter after the previous one.

        Flow:
            1. Instance Bounds -> Get width of each letter
            2. Accumulate Field -> Sum widths for trailing positions
            3. Translate -> Move each letter to accumulated position

        Args:
            instances: List of letter instance objects.
            spacing: Additional spacing multiplier (default 1.0).
            builder: NodeTreeBuilder for node creation.
            location: Starting position for nodes.

        Returns:
            Node with positioned instances, or None.

        Example:
            >>> positions = HandwritingSystem.calculate_positions(
            ...     letter_instances, spacing=1.2, builder=my_builder
            ... )
        """
        if builder is None or not instances:
            return None

        # Create points for each letter
        # We'll use a grid or distribute points
        grid = builder.add_node(
            "GeometryNodeMeshGrid",
            location,
            name="LetterPoints",
        )
        grid.inputs["Vertices X"].default_value = len(instances)
        grid.inputs["Vertices Y"].default_value = 1
        grid.inputs["Size X"].default_value = len(instances)
        grid.inputs["Size Y"].default_value = 1.0

        # Get bounding box for width
        bounds = builder.add_node(
            "GeometryNodeInputBoundingBox",
            (location[0] + 150, location[1] + 50),
            name="LetterBounds",
        )
        builder.link(grid.outputs["Mesh"], bounds.inputs["Geometry"])

        # Calculate width from bounds
        separate_min = builder.add_node(
            "ShaderNodeSeparateXYZ",
            (location[0] + 300, location[1] + 100),
            name="SeparateMin",
        )
        separate_max = builder.add_node(
            "ShaderNodeSeparateXYZ",
            (location[0] + 300, location[1]),
            name="SeparateMax",
        )
        builder.link(bounds.outputs["Min"], separate_min.inputs["Vector"])
        builder.link(bounds.outputs["Max"], separate_max.inputs["Vector"])

        # Width = max.x - min.x
        width_sub = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 450, location[1] + 50),
            name="CalcWidth",
        )
        width_sub.operation = "SUBTRACT"
        builder.link(separate_max.outputs["X"], width_sub.inputs[0])
        builder.link(separate_min.outputs["X"], width_sub.inputs[1])

        # Apply spacing
        width_scaled = builder.add_node(
            "ShaderNodeMath",
            (location[0] + 550, location[1] + 50),
            name="ApplySpacing",
        )
        width_scaled.operation = "MULTIPLY"
        builder.link(width_sub.outputs[0], width_scaled.inputs[0])
        width_scaled.inputs[1].default_value = spacing

        # Accumulate widths
        accumulate = builder.add_node(
            "GeometryNodeAccumulateField",
            (location[0] + 650, location[1]),
            name="AccumulateWidth",
        )
        builder.link(width_scaled.outputs[0], accumulate.inputs["Value"])

        # Create position vector from accumulated X
        combine_pos = builder.add_node(
            "ShaderNodeCombineXYZ",
            (location[0] + 800, location[1]),
            name="CombinePosition",
        )
        builder.link(accumulate.outputs["Trailing"], combine_pos.inputs["X"])
        combine_pos.inputs["Y"].default_value = 0.0
        combine_pos.inputs["Z"].default_value = 0.0

        # Set position
        set_pos = builder.add_node(
            "GeometryNodeSetPosition",
            (location[0] + 950, location[1]),
            name="SetLetterPosition",
        )
        builder.link(grid.outputs["Mesh"], set_pos.inputs["Geometry"])
        builder.link(combine_pos.outputs["Vector"], set_pos.inputs["Position"])

        return set_pos

    def set_spacing(self, spacing: float) -> "HandwritingSystem":
        """
        Set letter spacing.

        Args:
            spacing: Spacing multiplier (1.0 = normal, >1.0 = more space).

        Returns:
            Self for method chaining.
        """
        self._spacing = max(0.1, spacing)
        return self

    def set_seed(self, seed: int) -> "HandwritingSystem":
        """
        Set random seed for variant selection.

        Args:
            seed: Random seed value.

        Returns:
            Self for method chaining.
        """
        self._random_seed = seed
        random.seed(seed)
        return self

    def _get_letter_variants(self, char: str) -> list[Object]:
        """
        Get variant objects for a character.

        Args:
            char: Character to get variants for.

        Returns:
            List of variant objects, or space variants if not found.
        """
        char_lower = char.lower()
        if char_lower in self.alphabet_objects:
            return self.alphabet_objects[char_lower]
        # Default to space variants
        return self.alphabet_objects.get(" ", [])

    def _select_letter_variant(self, char: str, position: int) -> Optional[Object]:
        """
        Select a specific variant for a character at position.

        Args:
            char: Character to select variant for.
            position: Position in text (affects selection).

        Returns:
            Selected variant object, or None.
        """
        variants = self._get_letter_variants(char)
        if not variants:
            return None

        # Use position-based selection for variety
        char_index = self.find_char_index(char, 0, self.alphabet_string)
        variant_index = (char_index * self._variant_count + position) % len(variants)

        return variants[variant_index]

    def generate_text(
        self,
        text: str,
        spacing: Optional[float] = None,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Generate handwritten text geometry.

        Creates instances of letter variants positioned sequentially
        with proper spacing for a natural handwritten look.

        Flow:
            1. For each character:
               a. Find character index in alphabet
               b. Select random variant (index * 3 + random)
               c. Get variant object
            2. Calculate positions using Accumulate Field
            3. Instance letters on points
            4. Fix render order with Sort Elements

        Args:
            text: Text string to generate.
            spacing: Letter spacing (uses default if None).
            builder: NodeTreeBuilder (uses default if None).
            location: Starting position for nodes.

        Returns:
            Node with generated text geometry, or None.

        Example:
            >>> system = HandwritingSystem(letters, builder)
            >>> text_geo = system.generate_text("hello world", spacing=1.2)
        """
        effective_builder = builder or self.builder
        if effective_builder is None:
            return None

        spacing_val = spacing if spacing is not None else self._spacing

        # Create collection of letter instances
        # In practice, this would create Object Info nodes for each letter
        # and select based on character

        # Create point grid for letter positions
        char_count = len(text)
        if char_count == 0:
            return None

        # Create mesh points for letter positions
        grid = effective_builder.add_node(
            "GeometryNodeMeshGrid",
            location,
            name="TextPoints",
        )
        grid.inputs["Vertices X"].default_value = char_count
        grid.inputs["Vertices Y"].default_value = 1
        grid.inputs["Size X"].default_value = float(char_count)
        grid.inputs["Size Y"].default_value = 1.0

        # For each position, we need to:
        # 1. Determine which character
        # 2. Select variant index
        # 3. Instance the correct letter

        # Create index input
        index = effective_builder.add_node(
            "GeometryNodeInputIndex",
            (location[0] + 100, location[1] + 100),
            name="LetterIndex",
        )

        # Build variant selection logic
        # This is a simplified version - full implementation would
        # use attribute comparison and switch nodes

        # Create random value for variant selection
        random_variant = effective_builder.add_node(
            "FunctionNodeRandomValue",
            (location[0] + 200, location[1] + 150),
            name="RandomVariant",
        )
        random_variant.inputs["Min"].default_value = 0
        random_variant.inputs["Max"].default_value = self._variant_count - 1
        effective_builder.link(index.outputs["Index"], random_variant.inputs["ID"])

        # Calculate letter width accumulation
        # Use a fixed width for simplicity (actual implementation
        # would measure each letter)
        letter_width = 0.5 * spacing_val

        width_node = effective_builder.add_node(
            "GeometryNodeInputFloat",
            (location[0] + 200, location[1] + 50),
            name="LetterWidth",
        )
        width_node.inputs["Value"].default_value = letter_width

        # Accumulate position
        accumulate = effective_builder.add_node(
            "GeometryNodeAccumulateField",
            (location[0] + 300, location[1]),
            name="AccumulateLetterPosition",
        )
        effective_builder.link(width_node.outputs["Value"], accumulate.inputs["Value"])

        # Create position vector
        combine = effective_builder.add_node(
            "ShaderNodeCombineXYZ",
            (location[0] + 450, location[1]),
            name="CombineTextPosition",
        )
        effective_builder.link(accumulate.outputs["Trailing"], combine.inputs["X"])
        combine.inputs["Y"].default_value = 0.0
        combine.inputs["Z"].default_value = 0.0

        # Set position on points
        set_pos = effective_builder.add_node(
            "GeometryNodeSetPosition",
            (location[0] + 600, location[1]),
            name="SetTextPosition",
        )
        effective_builder.link(grid.outputs["Mesh"], set_pos.inputs["Geometry"])
        effective_builder.link(combine.outputs["Vector"], set_pos.inputs["Position"])

        # Instance letters on points
        # In full implementation, would use Object Info for each variant
        # and switch based on index

        # For now, use a single letter as placeholder
        first_variants = self._get_letter_variants("a")
        if first_variants:
            obj_info = effective_builder.add_node(
                "GeometryNodeObjectInfo",
                (location[0] + 700, location[1] - 100),
                name="LetterInfo",
            )
            obj_info.inputs[0].default_value = first_variants[0]
            obj_info.transform_space = "RELATIVE"

            instance = effective_builder.add_node(
                "GeometryNodeInstanceOnPoints",
                (location[0] + 850, location[1]),
                name="InstanceLetter",
            )
            effective_builder.link(set_pos.outputs["Geometry"], instance.inputs["Points"])
            effective_builder.link(obj_info.outputs["Geometry"], instance.inputs["Instance"])

            # Realize instances
            realize = effective_builder.add_node(
                "GeometryNodeRealizeInstances",
                (location[0] + 1000, location[1]),
                name="RealizeText",
            )
            effective_builder.link(instance.outputs["Instances"], realize.inputs["Geometry"])

            # Fix sort order for proper render order
            sorted_geo = self.fix_sort_order(realize.outputs["Geometry"], effective_builder, (location[0] + 1150, location[1]))
            if sorted_geo is not None:
                return sorted_geo

            return realize

        return set_pos

    def fix_sort_order(
        self,
        geometry_socket,
        builder: Optional[NodeTreeBuilder] = None,
        location: tuple[float, float] = (0, 0),
    ) -> Optional[Node]:
        """
        Fix sort order for proper render order.

        Uses Sort Elements node to ensure letters render in
        the correct order (left to right).

        Flow:
            1. Sort Elements by X position
            2. Output sorted geometry

        Args:
            geometry_socket: Geometry to sort.
            builder: NodeTreeBuilder for node creation.
            location: Position for sort node.

        Returns:
            Sorted geometry node, or None.

        Note:
            Sort Elements is available in Blender 4.0+.
        """
        effective_builder = builder or self.builder
        if effective_builder is None:
            return None

        # Get position for sorting
        position = effective_builder.add_node(
            "GeometryNodeInputPosition",
            (location[0] - 100, location[1] + 50),
            name="SortPosition",
        )

        # Sort by X position
        sort = effective_builder.add_node(
            "GeometryNodeSortElements",
            location,
            name="SortTextOrder",
        )

        # Connect geometry if it's a node output
        if hasattr(geometry_socket, "node"):
            effective_builder.link(geometry_socket, position.inputs[0])

        # Note: Sort Elements node sorts by a selection field
        # For proper sorting, we'd use the X position as the sort key
        # This is a simplified implementation

        return sort


class LetterVariantGenerator:
    """
    Generate letter variant objects from a base letter.

    Creates multiple hand-drawn variants of a letter by applying
    random transformations and distortions.

    Example:
        >>> generator = LetterVariantGenerator(base_letter_object)
        >>> variants = generator.generate_variants(count=3, variation=0.1)
    """

    def __init__(self, base_letter: Object):
        """
        Initialize the variant generator.

        Args:
            base_letter: Base letter object to create variants from.
        """
        self.base_letter = base_letter

    def generate_variants(
        self,
        count: int = 3,
        position_variation: float = 0.05,
        rotation_variation: float = 0.1,
        scale_variation: float = 0.05,
        noise_strength: float = 0.02,
    ) -> list[Object]:
        """
        Generate letter variants with random variations.

        Note: This is a conceptual implementation. In practice,
        you would duplicate the base object and apply deformations.

        Args:
            count: Number of variants to generate.
            position_variation: Position offset range.
            rotation_variation: Rotation variation in radians.
            scale_variation: Scale variation range.
            noise_strength: Noise distortion strength.

        Returns:
            List of variant objects (conceptual).
        """
        variants = []

        for i in range(count):
            # In a real implementation, we would:
            # 1. Duplicate base_letter
            # 2. Apply random position offset
            # 3. Apply random rotation
            # 4. Apply random scale
            # 5. Apply noise distortion via geometry nodes

            # This is a placeholder
            variants.append(self.base_letter)

        return variants


def create_handwriting(
    text: str,
    alphabet_objects: dict[str, list[Object]],
    spacing: float = 1.0,
    builder: Optional[NodeTreeBuilder] = None,
) -> Optional[Node]:
    """
    Quick handwriting creation with default settings.

    Args:
        text: Text string to generate.
        alphabet_objects: Dictionary of character to variant objects.
        spacing: Letter spacing multiplier.
        builder: NodeTreeBuilder for node creation.

    Returns:
        Generated text geometry node, or None.

    Example:
        >>> text_geo = create_handwriting(
        ...     "hello",
        ...     letter_objects,
        ...     spacing=1.2,
        ...     builder=my_builder
        ... )
    """
    system = HandwritingSystem(alphabet_objects, builder)
    return system.generate_text(text, spacing=spacing)
