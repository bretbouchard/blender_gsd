"""
Module Template Generator - Generate boilerplate for new blender_gsd modules.

This module creates properly structured Python files with all the necessary
boilerplate for NodeKit, HUD classes, and registration patterns.

Usage:
    from lib.dev.templates import ModuleTemplate, create_module

    # Create a new module with all features
    template = ModuleTemplate("my_effect")
    template.add_feature("nodekit")
    template.add_feature("hud")
    template.add_feature("presets")
    code = template.generate()

    # Quick creation
    code = create_module("crystal_growth", features=["nodekit", "hud", "bake"])
"""

from __future__ import annotations
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class ModuleConfig:
    """Configuration for a new module."""
    name: str
    class_name: str
    description: str = ""
    features: Set[str] = field(default_factory=set)
    knowledge_refs: List[str] = field(default_factory=list)
    author: str = ""
    version: str = "1.0.0"


class ModuleTemplate:
    """
    Generate boilerplate for new blender_gsd modules.

    Features that can be added:
    - nodekit: NodeKit integration for building node trees
    - hud: HUD class for displaying settings/info
    - presets: Preset configurations
    - bake: Baking/caching support
    - closure: Closure definitions (Blender 5.0)
    - bundle: Bundle schema support (Blender 5.0)

    Usage:
        template = ModuleTemplate("my_effect")
        template.set_description("Creates amazing effects")
        template.add_feature("nodekit")
        template.add_feature("hud")
        template.add_knowledge_ref("Section 2: Geometric Minimalism")
        code = template.generate()
    """

    AVAILABLE_FEATURES = {
        "nodekit": "NodeKit integration for building node trees",
        "hud": "HUD class for displaying settings and information",
        "presets": "Preset configurations",
        "bake": "Baking/caching support",
        "closure": "Closure definitions (Blender 5.0)",
        "bundle": "Bundle schema support (Blender 5.0)",
    }

    def __init__(self, name: str):
        """
        Initialize module template.

        Args:
            name: Module name (snake_case, will be converted to class name)
        """
        self.config = ModuleConfig(
            name=self._to_snake_case(name),
            class_name=self._to_class_name(name)
        )

    def _to_snake_case(self, name: str) -> str:
        """Convert any name to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _to_class_name(self, name: str) -> str:
        """Convert any name to PascalCase."""
        snake = self._to_snake_case(name)
        return ''.join(word.capitalize() for word in snake.split('_'))

    def set_description(self, description: str) -> "ModuleTemplate":
        """Set module description."""
        self.config.description = description
        return self

    def set_author(self, author: str) -> "ModuleTemplate":
        """Set module author."""
        self.config.author = author
        return self

    def set_version(self, version: str) -> "ModuleTemplate":
        """Set module version."""
        self.config.version = version
        return self

    def add_feature(self, feature: str) -> "ModuleTemplate":
        """
        Add a feature to the module.

        Args:
            feature: Feature name (nodekit, hud, presets, bake, closure, bundle)

        Returns:
            Self for chaining
        """
        if feature not in self.AVAILABLE_FEATURES:
            raise ValueError(f"Unknown feature '{feature}'. Available: {list(self.AVAILABLE_FEATURES.keys())}")

        self.config.features.add(feature)

        # Add dependencies
        if feature == "hud":
            self.config.features.add("nodekit")  # HUD often needs nodekit
        if feature == "closure":
            self.config.features.add("nodekit")
        if feature == "bundle":
            pass  # Bundle can be standalone

        return self

    def add_features(self, *features: str) -> "ModuleTemplate":
        """Add multiple features."""
        for feature in features:
            self.add_feature(feature)
        return self

    def add_knowledge_ref(self, ref: str) -> "ModuleTemplate":
        """Add a knowledge base reference."""
        self.config.knowledge_refs.append(ref)
        return self

    def generate(self) -> str:
        """
        Generate the module code.

        Returns:
            Complete Python module code
        """
        sections = [
            self._generate_header(),
            self._generate_imports(),
            self._generate_main_class(),
        ]

        if "presets" in self.config.features:
            sections.append(self._generate_presets_class())

        if "hud" in self.config.features:
            sections.append(self._generate_hud_class())

        if "bake" in self.config.features:
            sections.append(self._generate_bake_support())

        if "closure" in self.config.features:
            sections.append(self._generate_closure_support())

        if "bundle" in self.config.features:
            sections.append(self._generate_bundle_support())

        sections.append(self._generate_convenience_functions())

        return "\n\n".join(sections) + "\n"

    def _generate_header(self) -> str:
        """Generate module header/docstring."""
        lines = [
            '"""',
            f'{self.config.class_name} Module',
            '',
        ]

        if self.config.description:
            lines.append(f'{self.config.description}')
            lines.append('')

        if self.config.knowledge_refs:
            lines.append('Cross-references:')
            for ref in self.config.knowledge_refs:
                lines.append(f'- {ref}')
            lines.append('')

        lines.extend([
            'Usage:',
            f'    from lib.{self.config.name} import {self.config.class_name}',
            '',
            '    # Create the effect',
            f'    effect = {self.config.class_name}.create("MyEffect")',
            '    effect.build()',
            '"""',
            '',
            'from __future__ import annotations',
        ])

        return "\n".join(lines)

    def _generate_imports(self) -> str:
        """Generate import statements."""
        imports = [
            "import bpy",
            "import math",
            "from typing import Optional, Tuple, Dict, List, Any",
            "from pathlib import Path",
        ]

        if "nodekit" in self.config.features:
            imports.extend([
                "",
                "# Import NodeKit for node building",
                "try:",
                "    from ..nodekit import NodeKit",
                "except ImportError:",
                "    from nodekit import NodeKit",
            ])

        if "bundle" in self.config.features:
            imports.extend([
                "",
                "# Import bundle support",
                "try:",
                "    from ..geometry_nodes.bundles import BundleSchema, BundleBuilder",
                "except ImportError:",
                "    pass",
            ])

        return "\n".join(imports)

    def _generate_main_class(self) -> str:
        """Generate the main effect class."""
        has_nodekit = "nodekit" in self.config.features

        lines = [
            f"class {self.config.class_name}:",
            f'    """',
            f'    {self.config.description or "Main class for " + self.config.name + " effect."}',
            f'    """',
            "",
            "    def __init__(self):",
        ]

        if has_nodekit:
            lines.extend([
                "        self.node_tree: Optional[bpy.types.NodeTree] = None",
                "        self.nk: Optional[NodeKit] = None",
            ])
        else:
            lines.extend([
                "        self._material: Optional[bpy.types.Material] = None",
            ])

        lines.extend([
            "        self._created_nodes: dict = {}",
            "",
            "    @classmethod",
            f'    def create(cls, name: str = "{self.config.class_name}") -> "{self.config.class_name}":',
            '        """',
            "        Create a new instance.",
        ])

        if has_nodekit:
            lines.extend([
                '        """',
                "        instance = cls()",
                f'        instance.node_tree = bpy.data.node_groups.new(name, \'GeometryNodeTree\')',
                "        instance._setup_interface()",
                "        return instance",
                "",
                "    @classmethod",
                "    def from_object(",
                "        cls,",
                "        obj: bpy.types.Object,",
                f'        name: str = "{self.config.class_name}"',
                f'    ) -> "{self.config.class_name}":',
                '        """',
                "        Create and attach to an object via geometry nodes modifier.",
                '        """',
                "        mod = obj.modifiers.new(name=name, type='NODES')",
                "        tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')",
                "        mod.node_group = tree",
                "",
                "        instance = cls()",
                "        instance.node_tree = tree",
                "        instance._setup_interface()",
                "        return instance",
                "",
                "    def _setup_interface(self) -> None:",
                '        """Set up the node group interface (inputs/outputs)."""',
                "        # Create interface inputs",
                '        self.node_tree.interface.new_socket(',
                '            name="Geometry", in_out=\'INPUT\', socket_type=\'NodeSocketGeometry\'',
                "        )",
                "        # Add more inputs as needed",
                "",
                "        # Create interface outputs",
                '        self.node_tree.interface.new_socket(',
                '            name="Geometry", in_out=\'OUTPUT\', socket_type=\'NodeSocketGeometry\'',
                "        )",
                "",
                "        self.nk = NodeKit(self.node_tree)",
            ])
        else:
            lines.extend([
                '        """',
                "        instance = cls()",
                "        instance._material = bpy.data.materials.new(name=name)",
                "        instance._material.use_nodes = True",
                "        return instance",
            ])

        # Add parameter setters
        class_name = self.config.class_name
        lines.extend([
            "",
            f'    def set_param(self, name: str, value: Any) -> "{class_name}":',
            '        """',
            "        Set a parameter.",
        ])

        if has_nodekit:
            lines.extend([
                '        """',
                "        # Implementation depends on parameters needed",
                "        return self",
            ])
        else:
            lines.extend([
                '        """',
                "        # Set material parameter",
                "        return self",
            ])

        # Add build method
        lines.extend([
            "",
            "    def build(self) -> bpy.types.NodeTree:",
            '        """',
            "        Build the complete setup.",
            '        """',
        ])

        if has_nodekit:
            lines.extend([
                "        if not self.nk:",
                "            raise RuntimeError(\"Call create() or from_object() first\")",
                "",
                "        nk = self.nk",
                "        x = 0",
                "",
                "        # === INPUT NODES ===",
                "        group_in = nk.group_input(x=0, y=0)",
                "        self._created_nodes['group_input'] = group_in",
                "",
                "        # === PROCESSING NODES ===",
                "        # Add your node logic here",
                "",
                "        # === OUTPUT ===",
                "        group_out = nk.group_output(x=800, y=0)",
                "        self._created_nodes['group_output'] = group_out",
                "",
                "        return self.node_tree",
            ])
        else:
            lines.extend([
                "        if not self._material:",
                "            raise RuntimeError(\"Call create() first\")",
                "",
                "        nodes = self._material.node_tree.nodes",
                "        links = self._material.node_tree.links",
                "        nodes.clear()",
                "",
                "        # Build material nodes",
                "        output = nodes.new('ShaderNodeOutputMaterial')",
                "        principled = nodes.new('ShaderNodeBsdfPrincipled')",
                "        links.new(principled.outputs['BSDF'], output.inputs['Surface'])",
                "",
                "        return self._material",
            ])

        # Add get_node method
        lines.extend([
            "",
            "    def get_node(self, name: str) -> Optional[bpy.types.Node]:",
            '        """Get a created node by name."""',
            "        return self._created_nodes.get(name)",
        ])

        return "\n".join(lines)

    def _generate_presets_class(self) -> str:
        """Generate presets class."""
        lines = [
            f"class {self.config.class_name}Presets:",
            f'    """',
            f"    Preset configurations for {self.config.class_name}.",
            f'    """',
            "",
            "    @staticmethod",
            "    def default() -> Dict:",
            '        """Default configuration."""',
            "        return {",
            '            "param1": 1.0,',
            '            "param2": 0.5,',
            '            "description": "Default preset"',
            "        }",
            "",
            "    @staticmethod",
            "    def high_quality() -> Dict:",
            '        """High quality configuration."""',
            "        return {",
            '            "param1": 2.0,',
            '            "param2": 1.0,',
            '            "description": "High quality preset"',
            "        }",
        ]

        return "\n".join(lines)

    def _generate_hud_class(self) -> str:
        """Generate HUD class."""
        hud_class = f"{self.config.class_name}HUD"

        lines = [
            f"class {hud_class}:",
            f'    """',
            f"    Heads-Up Display for {self.config.class_name} visualization.",
            f'    """',
            "",
            "    @staticmethod",
            "    def display_settings(",
        ]

        # Add common parameters
        lines.extend([
            "        param1: float = 1.0,",
            "        param2: float = 0.5,",
        ])

        lines.extend([
            "    ) -> str:",
            '        """Display current settings."""',
            '        lines = [',
            '            "╔══════════════════════════════════════╗",',
            f'            "║    {self.config.class_name.upper():^34} ║",',
            '            "╠══════════════════════════════════════╣",',
            '            f"║ Param 1:       {param1:>20.2f} ║",',
            '            f"║ Param 2:       {param2:>20.2f} ║",',
            '            "╚══════════════════════════════════════╝"',
            '        ]',
            '        return "\\n".join(lines)',
            "",
            "    @staticmethod",
            "    def display_node_flow() -> str:",
            '        """Display the node flow."""',
            '        lines = [',
            '            "╔══════════════════════════════════════╗",',
            f'            "║    {self.config.class_name.upper()} NODE FLOW        ║",',
            '            "╠══════════════════════════════════════╣",',
            '            "║                                      ║",',
            '            "║  [Group Input]                       ║",',
            '            "║       │                              ║",',
            '            "║       └──→ [Processing]              ║",',
            '            "║                 │                    ║",',
            '            "║       [Group Output]                 ║",',
            '            "╚══════════════════════════════════════╝"',
            '        ]',
            '        return "\\n".join(lines)',
            "",
            "    @staticmethod",
            "    def display_checklist() -> str:",
            '        """Display pre-flight checklist."""',
            '        lines = [',
            '            "╔══════════════════════════════════════╗",',
            f'            "║  {self.config.class_name.upper()} PRE-FLIGHT CHECKLIST ║",',
            '            "╠══════════════════════════════════════╣",',
            '            "║                                      ║",',
            '            "║  □ Parameters configured             ║",',
            '            "║  □ Input geometry ready              ║",',
            '            "║  □ Material assigned                 ║",',
            '            "╚══════════════════════════════════════╝"',
            '        ]',
            '        return "\\n".join(lines)',
        ])

        return "\n".join(lines)

    def _generate_bake_support(self) -> str:
        """Generate baking/caching support."""
        class_name = self.config.class_name
        baker_class = f"{class_name}Baker"
        lines = [
            f"class {baker_class}:",
            f'    """',
            f"    Baking support for {class_name}.",
            f'    """',
            "",
            f'    def __init__(self, effect: "{class_name}"):',
            "        self.effect = effect",
            "        self._cache_path: Optional[Path] = None",
            "",
            f'    def set_cache_path(self, path: str) -> "{baker_class}":',
            '        """Set the cache path for baked data."""',
            "        self._cache_path = Path(path)",
            "        return self",
            "",
            "    def bake(self, frame_range: Tuple[int, int]) -> bool:",
            '        """Bake the effect over the frame range."""',
            "        # Implementation",
            "        return True",
            "",
            "    def load_cache(self) -> bool:",
            '        """Load baked cache if available."""',
            "        # Implementation",
            "        return True",
        ]

        return "\n".join(lines)

    def _generate_closure_support(self) -> str:
        """Generate closure support for Blender 5.0."""
        lines = [
            f"class {self.config.class_name}Closure:",
            f'    """',
            f"    Closure definitions for {self.config.class_name} (Blender 5.0).",
            f'    """',
            "",
            "    @staticmethod",
            "    def define_closure(",
            "        name: str,",
            "        inputs: List[Dict],",
            "        outputs: List[Dict]",
            "    ) -> Dict:",
            '        """Define a reusable closure."""',
            "        return {",
            '            "name": name,',
            '            "inputs": inputs,',
            '            "outputs": outputs,',
            '            "nodes": [],  # Add node definitions',
            '            "links": [],  # Add link definitions',
            "        }",
        ]

        return "\n".join(lines)

    def _generate_bundle_support(self) -> str:
        """Generate bundle schema support for Blender 5.0."""
        class_name = self.config.class_name
        bundle_name = self.config.name.upper()
        builder_class = f"{class_name}BundleBuilder"
        lines = [
            f"# Bundle schema for {class_name}",
            f"from ..geometry_nodes.bundles import BundleSchema",
            "",
            f"{bundle_name}_BUNDLE = BundleSchema(",
            f'    name="{self.config.name}",',
            f'    description="Bundle schema for {class_name}",',
            f'    required_keys={{',
            f'        "param1": "float",',
            f'    }},',
            f'    optional_keys={{',
            f'        "param2": ("float", 0.5),',
            f'    }}',
            f")",
            "",
            "",
            f"class {builder_class}:",
            f'    """',
            f"    Bundle builder for {class_name} (Blender 5.0).",
            f'    """',
            "",
            "    def __init__(self):",
            f"        self._data: Dict[str, Any] = {bundle_name}_BUNDLE.create_default()",
            "",
            f'    def set(self, key: str, value: Any) -> "{builder_class}":',
            '        """Set a bundle value."""',
            "        self._data[key] = value",
            "        return self",
            "",
            "    def build(self) -> Dict[str, Any]:",
            '        """Build and validate the bundle."""',
            f"        is_valid, errors = {bundle_name}_BUNDLE.validate(self._data)",
            "        if not is_valid:",
            '            raise ValueError(f"Bundle validation failed: {errors}")',
            "        return self._data.copy()",
        ]

        return "\n".join(lines)

    def _generate_convenience_functions(self) -> str:
        """Generate convenience functions."""
        name = self.config.name
        class_name = self.config.class_name
        version = self.config.version
        features_repr = repr(list(self.config.features))

        lines = [
            "# Convenience functions",
            "",
            f"def create_{name}(",
        ]

        if "nodekit" in self.config.features:
            lines.extend([
                "    obj: bpy.types.Object,",
                "    **kwargs",
            ])
        else:
            lines.extend([
                f'    name: str = "{name}",',
                "    **kwargs",
            ])

        lines.extend([
            f") -> {class_name}:",
            f'    """Quick setup for {name}."""',
            f"    effect = {class_name}.create(name)",
            "    for key, value in kwargs.items():",
            "        effect.set_param(key, value)",
            "    effect.build()",
            "    return effect",
            "",
            "",
            "def get_quick_reference() -> Dict:",
            '    """Get quick reference for this module."""',
            "    return {",
            f'        "module": "{name}",',
            f'        "version": "{version}",',
            f'        "features": {features_repr},',
            '        "tip": "Customize as needed"',
            "    }",
        ])

        return "\n".join(lines)

    def write_to_file(self, path: str) -> None:
        """
        Generate and write module to file.

        Args:
            path: File path to write to
        """
        code = self.generate()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_module(
    name: str,
    features: Optional[List[str]] = None,
    description: str = "",
    knowledge_refs: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Quick creation of a new module.

    Args:
        name: Module name
        features: List of features to include
        description: Module description
        knowledge_refs: Knowledge base references
        output_path: Optional path to write the file

    Returns:
        Generated module code
    """
    template = ModuleTemplate(name)

    if description:
        template.set_description(description)

    if features:
        template.add_features(*features)

    if knowledge_refs:
        for ref in knowledge_refs:
            template.add_knowledge_ref(ref)

    code = template.generate()

    if output_path:
        template.write_to_file(output_path)

    return code


def list_features() -> Dict[str, str]:
    """List all available features."""
    return ModuleTemplate.AVAILABLE_FEATURES.copy()


def generate_hud_class(name: str) -> str:
    """Generate just a HUD class for an existing module."""
    template = ModuleTemplate(name)
    template.add_feature("hud")
    return template._generate_hud_class()


# ============================================================================
# EXAMPLE TEMPLATES
# ============================================================================

EXAMPLE_TEMPLATES = {
    "basic_geometry_nodes": {
        "features": ["nodekit"],
        "description": "Basic geometry nodes effect"
    },
    "full_featured": {
        "features": ["nodekit", "hud", "presets", "bake"],
        "description": "Full-featured module with all standard components"
    },
    "material_effect": {
        "features": ["hud", "presets"],
        "description": "Material-based effect without geometry nodes"
    },
    "blender_50_bundle": {
        "features": ["nodekit", "hud", "bundle", "closure"],
        "description": "Blender 5.0 module with bundle and closure support"
    },
}


def create_from_template(template_name: str, name: str) -> str:
    """
    Create a module from a pre-defined template.

    Args:
        template_name: Name of the template (basic_geometry_nodes, full_featured, etc.)
        name: Name for the new module

    Returns:
        Generated module code
    """
    if template_name not in EXAMPLE_TEMPLATES:
        raise ValueError(f"Unknown template '{template_name}'. Available: {list(EXAMPLE_TEMPLATES.keys())}")

    template_config = EXAMPLE_TEMPLATES[template_name]

    return create_module(
        name=name,
        features=template_config["features"],
        description=template_config["description"]
    )
