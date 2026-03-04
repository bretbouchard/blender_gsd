"""
Node Graph Generator - Generate Blender node groups from declarative definitions.

This module provides a way to create Geometry Nodes setups from patterns
defined in the knowledge base or custom definitions.

Usage:
    from lib.geometry_nodes.generator import NodeGraphGenerator, NodeDef, PatternBuilder

    # Create from a named pattern
    gen = NodeGraphGenerator()
    tree = gen.from_pattern("sdf_workflow", {"voxel_size": 0.05})

    # Build custom node graph
    builder = PatternBuilder("MyEffect")
    builder.add_input("Geometry", "geometry")
    builder.add_input("Strength", "float", default=1.0)
    builder.add_node("noise", "ShaderNodeTexNoise", x=200, y=0)
    builder.link("input.Strength", "noise.scale")
    tree = builder.build()
"""

from __future__ import annotations
import bpy
import logging
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Set up logging
logger = logging.getLogger(__name__)

# Import NodeKit for node building
try:
    from ..nodekit import NodeKit
except ImportError:
    from nodekit import NodeKit

# Import knowledge query for pattern lookup
try:
    from ..knowledge.query import KnowledgeQuery, Pattern
except ImportError:
    logger.debug("KnowledgeQuery not available, pattern lookup from knowledge base disabled")
    KnowledgeQuery = None
    Pattern = None


class SocketType(Enum):
    """Socket types for node inputs/outputs."""
    GEOMETRY = "NodeSocketGeometry"
    FLOAT = "NodeSocketFloat"
    INT = "NodeSocketInt"
    VECTOR = "NodeSocketVector"
    COLOR = "NodeSocketColor"
    BOOLEAN = "NodeSocketBool"
    STRING = "NodeSocketString"
    OBJECT = "NodeSocketObject"
    COLLECTION = "NodeSocketCollection"
    MATERIAL = "NodeSocketMaterial"
    TEXTURE = "NodeSocketTexture"


@dataclass
class SocketDef:
    """Definition of a node socket."""
    name: str
    socket_type: str
    default_value: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "socket_type": self.socket_type,
            "default_value": self.default_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "description": self.description
        }


@dataclass
class NodeDef:
    """Definition of a node to create."""
    node_type: str
    name: str
    x: float = 0.0
    y: float = 0.0
    properties: Dict[str, Any] = field(default_factory=dict)
    input_values: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": self.node_type,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "properties": self.properties,
            "input_values": self.input_values
        }


@dataclass
class LinkDef:
    """Definition of a link between nodes."""
    from_node: str
    from_socket: str
    to_node: str
    to_socket: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_node": self.from_node,
            "from_socket": self.from_socket,
            "to_node": self.to_node,
            "to_socket": self.to_socket
        }


@dataclass
class ClosureDef:
    """Definition of a reusable closure."""
    name: str
    inputs: List[SocketDef]
    outputs: List[SocketDef]
    nodes: List[NodeDef]
    links: List[LinkDef]
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "nodes": [n.to_dict() for n in self.nodes],
            "links": [l.to_dict() for l in self.links]
        }


class PatternBuilder:
    """
    Fluent builder for creating node graph patterns.

    Usage:
        builder = PatternBuilder("MyEffect")
        builder.add_input("Geometry", "geometry")
        builder.add_input("Scale", "float", default=1.0)
        builder.add_node("noise", "ShaderNodeTexNoise", x=200)
        builder.link("input.Scale", "noise.scale")
        builder.add_output("Geometry", "geometry")
        tree = builder.build()
    """

    # Socket type mapping from shorthand to full Blender type
    SOCKET_TYPE_MAP = {
        "geometry": "NodeSocketGeometry",
        "float": "NodeSocketFloat",
        "int": "NodeSocketInt",
        "vector": "NodeSocketVector",
        "color": "NodeSocketColor",
        "bool": "NodeSocketBool",
        "boolean": "NodeSocketBool",
        "string": "NodeSocketString",
        "object": "NodeSocketObject",
        "collection": "NodeSocketCollection",
        "material": "NodeSocketMaterial",
        "texture": "NodeSocketTexture",
    }

    # Node spacing constants
    NODE_SPACING_X = 200
    NODE_SPACING_Y = 150

    def __init__(self, name: str, tree_type: str = 'GeometryNodeTree'):
        """
        Initialize the pattern builder.

        Args:
            name: Name for the node group
            tree_type: Type of node tree (GeometryNodeTree, ShaderNodeTree, CompositorNodeTree)
        """
        self.name = name
        self.tree_type = tree_type
        self._inputs: List[SocketDef] = []
        self._outputs: List[SocketDef] = []
        self._nodes: List[NodeDef] = []
        self._links: List[LinkDef] = []
        self._description: str = ""
        self._tags: List[str] = []
        self._x_offset: float = 0

    def describe(self, description: str) -> "PatternBuilder":
        """Add description to the pattern."""
        self._description = description
        return self

    def tag(self, *tags: str) -> "PatternBuilder":
        """Add tags to the pattern."""
        self._tags.extend(tags)
        return self

    def add_input(
        self,
        name: str,
        socket_type: str,
        default_value: Any = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        description: str = ""
    ) -> "PatternBuilder":
        """
        Add an input socket to the node group.

        Args:
            name: Socket name
            socket_type: Type shorthand (geometry, float, int, vector, color, bool, string)
            default_value: Default value for the socket
            min_value: Minimum value (for numeric types)
            max_value: Maximum value (for numeric types)
            description: Socket description

        Returns:
            Self for chaining
        """
        # Convert shorthand to full type
        full_type = self.SOCKET_TYPE_MAP.get(socket_type.lower(), socket_type)

        self._inputs.append(SocketDef(
            name=name,
            socket_type=full_type,
            default_value=default_value,
            min_value=min_value,
            max_value=max_value,
            description=description
        ))
        return self

    def add_output(
        self,
        name: str,
        socket_type: str,
        description: str = ""
    ) -> "PatternBuilder":
        """
        Add an output socket to the node group.

        Args:
            name: Socket name
            socket_type: Type shorthand (geometry, float, int, vector, color, bool, string)
            description: Socket description

        Returns:
            Self for chaining
        """
        full_type = self.SOCKET_TYPE_MAP.get(socket_type.lower(), socket_type)

        self._outputs.append(SocketDef(
            name=name,
            socket_type=full_type,
            description=description
        ))
        return self

    def add_node(
        self,
        name: str,
        node_type: str,
        x: Optional[float] = None,
        y: float = 0.0,
        **properties
    ) -> "PatternBuilder":
        """
        Add a node to the pattern.

        Args:
            name: Unique name for this node in the pattern
            node_type: Blender node type (e.g., "GeometryNodeTransform")
            x: X position (auto-incremented if None)
            y: Y position
            **properties: Node properties to set

        Returns:
            Self for chaining
        """
        if x is None:
            x = self._x_offset
            self._x_offset += self.NODE_SPACING_X

        # Separate input values from properties
        input_values = {}
        node_props = {}

        for key, value in properties.items():
            if key.startswith('input_'):
                input_values[key[6:]] = value
            else:
                node_props[key] = value

        self._nodes.append(NodeDef(
            node_type=node_type,
            name=name,
            x=x,
            y=y,
            properties=node_props,
            input_values=input_values
        ))
        return self

    def link(
        self,
        from_path: str,
        to_path: str
    ) -> "PatternBuilder":
        """
        Add a link between nodes.

        Args:
            from_path: "node_name.socket_name" or "input.socket_name"
            to_path: "node_name.socket_name" or "output.socket_name"

        Returns:
            Self for chaining
        """
        from_parts = from_path.split('.', 1)
        to_parts = to_path.split('.', 1)

        if len(from_parts) != 2 or len(to_parts) != 2:
            raise ValueError(f"Invalid link path format. Use 'node.socket' format.")

        self._links.append(LinkDef(
            from_node=from_parts[0],
            from_socket=from_parts[1],
            to_node=to_parts[0],
            to_socket=to_parts[1]
        ))
        return self

    def chain(
        self,
        *node_names: str,
        socket: str = "Geometry"
    ) -> "PatternBuilder":
        """
        Chain multiple nodes together (output to input).

        Args:
            *node_names: Names of nodes to chain
            socket: Socket name to use for linking

        Returns:
            Self for chaining
        """
        for i in range(len(node_names) - 1):
            self.link(f"{node_names[i]}.{socket}", f"{node_names[i+1]}.{socket}")
        return self

    # ========================================================================
    # Convenience Methods for Common Node Types
    # ========================================================================

    def add_noise_node(
        self,
        name: str,
        scale: float = 5.0,
        detail: float = 2.0,
        distortion: float = 0.0,
        x: Optional[float] = None,
        y: float = 0.0
    ) -> "PatternBuilder":
        """
        Add a noise texture node with common defaults.

        Args:
            name: Unique name for this node
            scale: Noise scale (default 5.0)
            detail: Detail level (default 2.0)
            distortion: Distortion amount (default 0.0)
            x: X position (auto-incremented if None)
            y: Y position

        Returns:
            Self for chaining
        """
        return self.add_node(
            name, "ShaderNodeTexNoise",
            x=x, y=y,
            input_scale=scale,
            input_detail=detail,
            input_distortion=distortion
        )

    def add_math_node(
        self,
        name: str,
        operation: str = "ADD",
        value: float = 0.0,
        value_1: Optional[float] = None,
        value_2: Optional[float] = None,
        x: Optional[float] = None,
        y: float = 0.0
    ) -> "PatternBuilder":
        """
        Add a math node with operation specified.

        Args:
            name: Unique name for this node
            operation: Math operation (ADD, SUBTRACT, MULTIPLY, DIVIDE, etc.)
            value: First value input (for single-input ops)
            value_1: First value input (for two-input ops)
            value_2: Second value input (for two-input ops)
            x: X position (auto-incremented if None)
            y: Y position

        Returns:
            Self for chaining
        """
        props = {"operation": operation.upper()}
        if value_1 is not None:
            props["input_value"] = value_1
            props["input_value_1"] = value_1
        elif value is not None:
            props["input_value"] = value
        if value_2 is not None:
            props["input_value_2"] = value_2

        return self.add_node(name, "ShaderNodeMath", x=x, y=y, **props)

    def add_vector_math_node(
        self,
        name: str,
        operation: str = "ADD",
        x: Optional[float] = None,
        y: float = 0.0
    ) -> "PatternBuilder":
        """
        Add a vector math node.

        Args:
            name: Unique name for this node
            operation: Vector operation (ADD, SUBTRACT, MULTIPLY, DOT_PRODUCT, CROSS_PRODUCT, etc.)
            x: X position (auto-incremented if None)
            y: Y position

        Returns:
            Self for chaining
        """
        return self.add_node(
            name, "ShaderNodeVectorMath",
            x=x, y=y,
            operation=operation.upper()
        )

    def add_separate_xyz(
        self,
        name: str = "separate_xyz",
        x: Optional[float] = None,
        y: float = 0.0
    ) -> "PatternBuilder":
        """
        Add a Separate XYZ node.

        Args:
            name: Unique name for this node
            x: X position (auto-incremented if None)
            y: Y position

        Returns:
            Self for chaining
        """
        return self.add_node(name, "ShaderNodeSeparateXYZ", x=x, y=y)

    def add_combine_xyz(
        self,
        name: str = "combine_xyz",
        x: Optional[float] = None,
        y: float = 0.0
    ) -> "PatternBuilder":
        """
        Add a Combine XYZ node.

        Args:
            name: Unique name for this node
            x: X position (auto-incremented if None)
            y: Y position

        Returns:
            Self for chaining
        """
        return self.add_node(name, "ShaderNodeCombineXYZ", x=x, y=y)

    def add_position_node(
        self,
        name: str = "position",
        x: Optional[float] = None,
        y: float = 0.0
    ) -> "PatternBuilder":
        """
        Add a Position input node.

        Args:
            name: Unique name for this node
            x: X position (auto-incremented if None)
            y: Y position

        Returns:
            Self for chaining
        """
        return self.add_node(name, "GeometryNodeInputPosition", x=x, y=y)

    def add_set_position(
        self,
        name: str = "set_position",
        x: Optional[float] = None,
        y: float = 0.0
    ) -> "PatternBuilder":
        """
        Add a Set Position node.

        Args:
            name: Unique name for this node
            x: X position (auto-incremented if None)
            y: Y position

        Returns:
            Self for chaining
        """
        return self.add_node(name, "GeometryNodeSetPosition", x=x, y=y)

    def add_random_value(
        self,
        name: str,
        min_val: float = 0.0,
        max_val: float = 1.0,
        seed: int = 0,
        x: Optional[float] = None,
        y: float = 0.0
    ) -> "PatternBuilder":
        """
        Add a Random Value node.

        Args:
            name: Unique name for this node
            min_val: Minimum value
            max_val: Maximum value
            seed: Random seed
            x: X position (auto-incremented if None)
            y: Y position

        Returns:
            Self for chaining
        """
        return self.add_node(
            name, "FunctionNodeRandomValue",
            x=x, y=y,
            input_min=min_val,
            input_max=max_val,
            input_seed=seed
        )

    def build(self) -> bpy.types.NodeTree:
        """
        Build the node tree.

        Returns:
            The created node tree
        """
        # Create node group
        tree = bpy.data.node_groups.new(self.name, self.tree_type)

        # Add interface sockets
        for inp in self._inputs:
            socket = tree.interface.new_socket(
                name=inp.name,
                in_out='INPUT',
                socket_type=inp.socket_type
            )
            if inp.default_value is not None:
                socket.default_value = inp.default_value
            if inp.min_value is not None:
                socket.min_value = inp.min_value
            if inp.max_value is not None:
                socket.max_value = inp.max_value

        for out in self._outputs:
            tree.interface.new_socket(
                name=out.name,
                in_out='OUTPUT',
                socket_type=out.socket_type
            )

        # Create NodeKit helper
        nk = NodeKit(tree)

        # Create nodes
        created_nodes = {}

        # Add group input/output nodes
        group_in = nk.group_input(x=0, y=0)
        group_out = nk.group_output(x=self._x_offset + self.NODE_SPACING_X, y=0)
        created_nodes['input'] = group_in
        created_nodes['output'] = group_out

        # Add defined nodes
        for node_def in self._nodes:
            node = nk.n(
                node_def.node_type,
                node_def.name,
                x=node_def.x,
                y=node_def.y
            )

            # Set properties
            for prop, value in node_def.properties.items():
                if hasattr(node, prop):
                    setattr(node, prop, value)

            # Set input values
            for socket_name, value in node_def.input_values.items():
                if socket_name in node.inputs:
                    node.inputs[socket_name].default_value = value

            created_nodes[node_def.name] = node

        # Create links
        for link_def in self._links:
            # Get source node and socket
            if link_def.from_node == 'input':
                from_node = group_in
            else:
                from_node = created_nodes.get(link_def.from_node)

            if link_def.to_node == 'output':
                to_node = group_out
            else:
                to_node = created_nodes.get(link_def.to_node)

            if from_node and to_node:
                # Find sockets
                from_socket = from_node.outputs.get(link_def.from_socket)
                to_socket = to_node.inputs.get(link_def.to_socket)

                if from_socket and to_socket:
                    nk.link(from_socket, to_socket)

        return tree

    def to_closure(self) -> ClosureDef:
        """Convert builder to a ClosureDef for storage/reuse."""
        return ClosureDef(
            name=self.name,
            description=self._description,
            inputs=self._inputs,
            outputs=self._outputs,
            nodes=self._nodes,
            links=self._links
        )


class NodeGraphGenerator:
    """
    Generate Geometry Nodes setups from patterns or definitions.

    This is the main interface for creating node graphs from the
    knowledge base patterns or custom definitions.
    """

    # Built-in pattern generators
    PATTERN_GENERATORS: Dict[str, Callable] = {}

    def __init__(self):
        """Initialize the node graph generator."""
        self._closures: Dict[str, ClosureDef] = {}
        self._knowledge = KnowledgeQuery() if KnowledgeQuery else None

    def from_pattern(
        self,
        pattern_name: str,
        params: Optional[Dict[str, Any]] = None
    ) -> bpy.types.NodeTree:
        """
        Create a node tree from a named pattern.

        Args:
            pattern_name: Name of the pattern (from knowledge base)
            params: Parameters to customize the pattern

        Returns:
            The created node tree
        """
        params = params or {}

        # Check built-in generators first
        if pattern_name in self.PATTERN_GENERATORS:
            return self.PATTERN_GENERATORS[pattern_name](params)

        # Look up pattern in knowledge base
        if self._knowledge:
            pattern = self._knowledge.get_pattern(pattern_name)
            if pattern:
                return self._build_from_knowledge_pattern(pattern, params)

        raise ValueError(f"Pattern '{pattern_name}' not found in knowledge base or generators")

    def _build_from_knowledge_pattern(
        self,
        pattern: "Pattern",
        params: Dict[str, Any]
    ) -> bpy.types.NodeTree:
        """
        Build a node tree from a knowledge base Pattern object.

        If the pattern lacks concrete node definitions, a documentation tree
        is created that shows the workflow steps as annotated reroute nodes.

        Args:
            pattern: Pattern object from knowledge base
            params: Parameters to customize the pattern

        Returns:
            The created node tree (full implementation or documentation tree)
        """
        builder = PatternBuilder(pattern.name)
        builder.describe(pattern.description)
        builder.tag(*pattern.tags)

        # Check if pattern has usable node information
        if not pattern.nodes:
            # Create a documentation tree instead of crashing
            logger.info(
                f"Pattern '{pattern.name}' has no node definitions. "
                f"Creating documentation tree. Register a generator with "
                f"register_pattern('{pattern.name}', func) for full functionality."
            )
            return self._create_documentation_tree(pattern)

        # Add inputs from pattern
        for inp in getattr(pattern, 'inputs', []):
            builder.add_input(
                name=inp.get('name', 'Input'),
                socket_type=inp.get('type', 'float'),
                default_value=inp.get('default'),
                min_value=inp.get('min'),
                max_value=inp.get('max')
            )

        # If no inputs defined, add default geometry
        if not getattr(pattern, 'inputs', []):
            builder.add_input("Geometry", "geometry")

        # Add nodes from pattern
        for node_def in pattern.nodes:
            node_type = node_def.get('type') or node_def.get('node_type')
            if node_type:
                builder.add_node(
                    name=node_def.get('name', 'Node'),
                    node_type=node_type,
                    x=node_def.get('x'),
                    y=node_def.get('y', 0),
                    **node_def.get('properties', {})
                )

        # Add outputs from pattern
        for out in getattr(pattern, 'outputs', []):
            builder.add_output(
                name=out.get('name', 'Output'),
                socket_type=out.get('type', 'geometry')
            )

        # If no outputs defined, add default geometry
        if not getattr(pattern, 'outputs', []):
            builder.add_output("Geometry", "geometry")

        # Add links from pattern
        for link_def in getattr(pattern, 'links', []):
            builder.link(
                f"{link_def['from_node']}.{link_def['from_socket']}",
                f"{link_def['to_node']}.{link_def['to_socket']}"
            )

        return builder.build()

    def _create_documentation_tree(self, pattern: "Pattern") -> bpy.types.NodeTree:
        """
        Create a node tree that documents a pattern's workflow.

        This is used when a pattern exists in the knowledge base but
        lacks concrete node definitions. The tree shows the workflow
        as a series of annotation nodes (reroutes with labels).

        Args:
            pattern: Pattern object with workflow description

        Returns:
            A node tree with labeled reroute nodes showing the workflow steps
        """
        builder = PatternBuilder(f"Docs_{pattern.name}")
        builder.describe(f"Documentation: {pattern.description}")

        builder.add_input("Geometry", "geometry")

        # Parse workflow steps from pattern.workflow
        if pattern.workflow:
            # Split on arrow and clean up
            steps = [s.strip() for s in pattern.workflow.replace('→', '->').split('->') if s.strip()]
        else:
            steps = ["No workflow defined", "Register a generator", "for full functionality"]

        # Add annotation nodes showing workflow steps
        for i, step in enumerate(steps):
            # Truncate long labels
            label = step[:40] + "..." if len(step) > 40 else step
            builder.add_node(
                f"step_{i}",
                "NodeReroute",
                x=i * 200,
                y=0,
                label=label
            )

        builder.add_output("Geometry", "geometry")

        # Chain the reroutes
        if len(steps) > 1:
            for i in range(len(steps) - 1):
                builder.link(f"step_{i}.output", f"step_{i+1}.input")

        return builder.build()

    def closure(
        self,
        name: str,
        inputs: List[Dict[str, Any]],
        outputs: List[Dict[str, Any]],
        logic: Optional[Callable[['PatternBuilder'], None]] = None
    ) -> ClosureDef:
        """
        Define a reusable closure.

        Args:
            name: Closure name
            inputs: List of input definitions
            outputs: List of output definitions
            logic: Function that adds nodes/links to a builder

        Returns:
            The created ClosureDef
        """
        builder = PatternBuilder(name)

        for inp in inputs:
            builder.add_input(**inp)

        for out in outputs:
            builder.add_output(**out)

        if logic:
            logic(builder)

        closure = builder.to_closure()
        self._closures[name] = closure
        return closure

    def invoke_closure(
        self,
        closure_name: str,
        tree: bpy.types.NodeTree,
        x: float = 0,
        y: float = 0
    ) -> bpy.types.Node:
        """
        Invoke a closure in a node tree.

        Args:
            closure_name: Name of the closure to invoke
            tree: Node tree to add the closure to
            x: X position for the node group
            y: Y position for the node group

        Returns:
            The created node group instance
        """
        if closure_name not in self._closures:
            raise ValueError(f"Closure '{closure_name}' not found")

        closure = self._closures[closure_name]

        # Build the closure tree if not already built
        group_name = f"Closure_{closure_name}"
        if group_name not in bpy.data.node_groups:
            builder = PatternBuilder(group_name)
            for inp in closure.inputs:
                builder.add_input(**inp.to_dict())
            for out in closure.outputs:
                builder.add_output(**out.to_dict())
            for node in closure.nodes:
                builder.add_node(
                    node.name,
                    node.node_type,
                    x=node.x,
                    y=node.y,
                    **node.properties,
                    **{f"input_{k}": v for k, v in node.input_values.items()}
                )
            for link in closure.links:
                builder.link(
                    f"{link.from_node}.{link.from_socket}",
                    f"{link.to_node}.{link.to_socket}"
                )
            builder.build()

        # Add node group to target tree
        nk = NodeKit(tree)
        node = nk.n("GeometryNodeGroup", group_name, x=x, y=y)
        node.node_tree = bpy.data.node_groups[group_name]

        return node

    def register_pattern(
        self,
        name: str,
        generator: Callable[[Dict[str, Any]], bpy.types.NodeTree]
    ) -> None:
        """
        Register a custom pattern generator.

        Args:
            name: Pattern name
            generator: Function that takes params dict and returns a NodeTree
        """
        self.PATTERN_GENERATORS[name] = generator

    def list_patterns(self) -> List[str]:
        """List all available pattern names."""
        patterns = list(self.PATTERN_GENERATORS.keys())
        if self._knowledge:
            patterns.extend([p["name"] for p in self._knowledge.list_patterns()])
        return list(set(patterns))


# ============================================================================
# BUILT-IN PATTERN GENERATORS
# ============================================================================

def _generate_random_transform(params: Dict[str, Any]) -> bpy.types.NodeTree:
    """Generate random transform pattern."""
    rotation_range = params.get("rotation_range", (-3.14, 3.14))
    scale_range = params.get("scale_range", (0.8, 1.2))
    seed = params.get("seed", 0)

    builder = PatternBuilder("RandomTransform")
    builder.describe("Random rotation and scale for instances")

    builder.add_input("Geometry", "geometry")
    builder.add_input("Seed", "int", default=seed)
    builder.add_input("Rotation Min", "float", default=rotation_range[0])
    builder.add_input("Rotation Max", "float", default=rotation_range[1])
    builder.add_input("Scale Min", "float", default=scale_range[0])
    builder.add_input("Scale Max", "float", default=scale_range[1])

    builder.add_node("random_rot", "FunctionNodeRandomValue", x=200, y=100)
    builder.add_node("random_scale", "FunctionNodeRandomValue", x=200, y=-100)
    builder.add_node("rotate", "GeometryNodeRotateInstances", x=400, y=50)
    builder.add_node("scale", "GeometryNodeScaleInstances", x=600, y=0)

    builder.add_output("Geometry", "geometry")

    # Links
    builder.link("input.Seed", "random_rot.seed")
    builder.link("input.Seed", "random_scale.seed")
    builder.link("input.Rotation Min", "random_rot.min")
    builder.link("input.Rotation Max", "random_rot.max")
    builder.link("input.Scale Min", "random_scale.min")
    builder.link("input.Scale Max", "random_scale.max")

    builder.link("input.Geometry", "rotate.geometry")
    builder.link("random_rot.value", "rotate.rotation.z")
    builder.link("rotate.instances", "scale.geometry")
    builder.link("random_scale.value", "scale.scale")
    builder.link("scale.instances", "output.Geometry")

    return builder.build()


def _generate_height_scale(params: Dict[str, Any]) -> bpy.types.NodeTree:
    """Generate height-based scale pattern."""
    multiplier = params.get("multiplier", -2.0)
    offset = params.get("offset", 1.0)

    builder = PatternBuilder("HeightScale")
    builder.describe("Scale instances based on Z position (smaller at top)")

    builder.add_input("Geometry", "geometry")
    builder.add_input("Multiplier", "float", default=multiplier)
    builder.add_input("Offset", "float", default=offset)

    builder.add_node("position", "GeometryNodeInputPosition", x=200, y=100)
    builder.add_node("separate", "ShaderNodeSeparateXYZ", x=400, y=100)
    builder.add_node("multiply", "ShaderNodeMath", x=600, y=50)
    builder.add_node("add", "ShaderNodeMath", x=800, y=0)
    builder.add_node("scale", "GeometryNodeScaleInstances", x=1000, y=0)

    builder.add_output("Geometry", "geometry")

    builder.link("position.position", "separate.vector")
    builder.link("separate.z", "multiply.value")
    builder.link("input.Multiplier", "multiply.value_1")
    builder.link("multiply.value", "add.value")
    builder.link("input.Offset", "add.value_1")
    builder.link("add.value", "scale.scale")
    builder.link("input.Geometry", "scale.geometry")
    builder.link("scale.instances", "output.Geometry")

    return builder.build()


def _generate_noise_displace(params: Dict[str, Any]) -> bpy.types.NodeTree:
    """Generate noise displacement pattern."""
    strength = params.get("strength", 1.0)
    scale = params.get("scale", 5.0)
    detail = params.get("detail", 2)

    builder = PatternBuilder("NoiseDisplace")
    builder.describe("Displace geometry using noise texture")

    builder.add_input("Geometry", "geometry")
    builder.add_input("Strength", "float", default=strength)
    builder.add_input("Scale", "float", default=scale)
    builder.add_input("Detail", "float", default=detail)

    builder.add_node("position", "GeometryNodeInputPosition", x=200, y=100)
    builder.add_node("noise", "ShaderNodeTexNoise", x=400, y=100)
    builder.add_node("separate", "ShaderNodeSeparateColor", x=600, y=100)
    builder.add_node("combine", "ShaderNodeCombineXYZ", x=800, y=100)
    builder.add_node("multiply", "ShaderNodeMath", x=1000, y=50)
    builder.add_node("set_pos", "GeometryNodeSetPosition", x=1200, y=0)

    builder.add_output("Geometry", "geometry")

    builder.link("position.position", "noise.vector")
    builder.link("input.Scale", "noise.scale")
    builder.link("input.Detail", "noise.detail")
    builder.link("noise.color", "separate.color")
    builder.link("separate.r", "combine.x")
    builder.link("separate.g", "combine.y")
    builder.link("separate.b", "combine.z")
    builder.link("combine.vector", "multiply.value")
    builder.link("input.Strength", "multiply.value_1")
    builder.link("multiply.value", "set_pos.offset")
    builder.link("input.Geometry", "set_pos.geometry")
    builder.link("set_pos.geometry", "output.Geometry")

    return builder.build()


# Register built-in patterns
NodeGraphGenerator.PATTERN_GENERATORS["random_transform"] = _generate_random_transform
NodeGraphGenerator.PATTERN_GENERATORS["height_scale"] = _generate_height_scale
NodeGraphGenerator.PATTERN_GENERATORS["noise_displace"] = _generate_noise_displace


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_from_pattern(pattern_name: str, **params) -> bpy.types.NodeTree:
    """Quick creation of node tree from a pattern."""
    gen = NodeGraphGenerator()
    return gen.from_pattern(pattern_name, params)


def create_closure(
    name: str,
    inputs: List[Dict[str, Any]],
    outputs: List[Dict[str, Any]],
    logic: Optional[Callable] = None
) -> ClosureDef:
    """Quick creation of a closure definition."""
    gen = NodeGraphGenerator()
    return gen.closure(name, inputs, outputs, logic)


def list_available_patterns() -> List[str]:
    """List all available pattern names."""
    gen = NodeGraphGenerator()
    return gen.list_patterns()


def quick_random_transform(
    rotation_range: Tuple[float, float] = (-3.14, 3.14),
    scale_range: Tuple[float, float] = (0.8, 1.2),
    seed: int = 0
) -> bpy.types.NodeTree:
    """Quick random transform node group."""
    return create_from_pattern(
        "random_transform",
        rotation_range=rotation_range,
        scale_range=scale_range,
        seed=seed
    )


def quick_height_scale(
    multiplier: float = -2.0,
    offset: float = 1.0
) -> bpy.types.NodeTree:
    """Quick height-based scale node group."""
    return create_from_pattern("height_scale", multiplier=multiplier, offset=offset)


def quick_noise_displace(
    strength: float = 1.0,
    scale: float = 5.0,
    detail: float = 2.0
) -> bpy.types.NodeTree:
    """Quick noise displacement node group."""
    return create_from_pattern(
        "noise_displace",
        strength=strength,
        scale=scale,
        detail=detail
    )
