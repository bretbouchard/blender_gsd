"""
L-System Road Generator

Implements L-system string rewriting for procedural road network generation.
Runs in Python (not GN) because it requires string rewriting rules and
context-sensitive evaluation that Geometry Nodes cannot handle.

Output: JSON road network consumed by GN Road Builder.

Architecture:
    LSystemRoads.generate(axiom, iterations)
        ↓
    String rewriting with production rules
        ↓
    Parse string to graph structure
        ↓
    RoadNetwork with nodes and edges

Implements REQ-UR-01: Road Network Generator (L-system).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List, Callable
from enum import Enum
import random
import math
import re

from .types import (
    RoadNetwork,
    RoadNode,
    RoadEdge,
    LaneConfig,
    NodeType,
    EdgeType,
    RoadType,
)


@dataclass
class LSystemRule:
    """
    L-system production rule.

    Attributes:
        predecessor: Symbol to replace
        successor: Replacement string
        probability: Probability of applying (for stochastic rules)
        condition: Optional condition function
    """
    predecessor: str = ""
    successor: str = ""
    probability: float = 1.0
    condition: Optional[Callable[[str, int], bool]] = None

    def matches(self, symbol: str, context: str, iteration: int) -> bool:
        """Check if rule matches."""
        if symbol != self.predecessor:
            return False
        if self.condition and not self.condition(context, iteration):
            return False
        return True


@dataclass
class LSystemConfig:
    """
    L-system configuration.

    Attributes:
        angle: Default turn angle in degrees
        segment_length: Default road segment length
        road_width: Default road width
        variation: Random variation factor (0-1)
        max_iterations: Maximum iterations
        branching_probability: Probability of creating branch
    """
    angle: float = 90.0
    segment_length: float = 20.0
    road_width: float = 10.0
    variation: float = 0.1
    max_iterations: int = 5
    branching_probability: float = 0.3


# Default rule sets for different road patterns
ROAD_RULE_SETS: Dict[str, List[LSystemRule]] = {
    # Grid pattern - simple expansion
    "grid": [
        LSystemRule(predecessor="R", successor="R+R"),  # Straight with turn
        LSystemRule(predecessor="+", successor="+R+R", probability=0.3),  # Branch
    ],

    # Organic/curved roads
    "organic": [
        LSystemRule(predecessor="R", successor="R~R"),  # Add curve
        LSystemRule(predecessor="~", successor="~R~R", probability=0.4),
        LSystemRule(predecessor="R", successor="R[R]R", probability=0.2),  # Branch
    ],

    # Suburban cul-de-sac pattern
    "suburban": [
        LSystemRule(predecessor="R", successor="R-R", probability=0.4),
        LSystemRule(predecessor="R", successor="R[R]R", probability=0.3),
        LSystemRule(predecessor="-", successor="-R.", probability=0.5),  # Dead end
    ],

    # Highway/radial pattern
    "highway": [
        LSystemRule(predecessor="H", successor="HH"),  # Straight highway
        LSystemRule(predecessor="H", successor="H+R+H", probability=0.2),  # Exit
        LSystemRule(predecessor="R", successor="R~R", probability=0.5),  # Curved ramp
    ],

    # Downtown dense grid
    "downtown": [
        LSystemRule(predecessor="R", successor="R+R-R", probability=0.6),
        LSystemRule(predecessor="R", successor="R[R]R[R]R", probability=0.3),
    ],
}

# Symbol meanings
SYMBOL_MEANINGS = {
    "R": "road_forward",
    "H": "highway_forward",
    "+": "turn_left",
    "-": "turn_right",
    "~": "curve",
    "[": "push_state (branch start)",
    "]": "pop_state (branch end)",
    ".": "dead_end",
}


class TurtleState:
    """Turtle graphics state for road drawing."""

    def __init__(self, x: float = 0.0, y: float = 0.0, angle: float = 0.0):
        self.x = x
        self.y = y
        self.angle = angle  # In degrees

    def copy(self) -> "TurtleState":
        return TurtleState(self.x, self.y, self.angle)

    def move(self, distance: float) -> Tuple[float, float]:
        """Move forward and return new position."""
        rad = math.radians(self.angle)
        self.x += distance * math.cos(rad)
        self.y += distance * math.sin(rad)
        return (self.x, self.y)

    def turn(self, degrees: float) -> None:
        """Turn by degrees (positive = left, negative = right)."""
        self.angle += degrees


class LSystemRoads:
    """
    L-system road network generator.

    Generates procedural road networks using string rewriting rules.
    The turtle interpretation creates the actual road geometry.

    Usage:
        generator = LSystemRoads(seed=42)
        network = generator.generate(axiom="R", iterations=3, pattern="grid")
        json_output = network.to_json()
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        config: Optional[LSystemConfig] = None,
    ):
        """
        Initialize L-system generator.

        Args:
            seed: Random seed for reproducibility
            config: L-system configuration
        """
        self.seed = seed
        self.config = config or LSystemConfig()
        self._rng = random.Random(seed)
        self._node_counter = 0
        self._edge_counter = 0

    def generate(
        self,
        axiom: str,
        iterations: int,
        pattern: str = "grid",
        dimensions: Tuple[float, float] = (200.0, 200.0),
        start_position: Optional[Tuple[float, float]] = None,
    ) -> RoadNetwork:
        """
        Generate road network from axiom.

        Args:
            axiom: Starting string
            iterations: Number of rewrite iterations
            pattern: Rule set pattern name
            dimensions: Network dimensions
            start_position: Starting position (defaults to center)

        Returns:
            RoadNetwork with nodes and edges
        """
        # Reset counters
        self._node_counter = 0
        self._edge_counter = 0
        self._rng = random.Random(self.seed)

        # Get rules for pattern
        rules = ROAD_RULE_SETS.get(pattern, ROAD_RULE_SETS["grid"])

        # Apply string rewriting
        result = axiom
        for i in range(iterations):
            result = self._apply_rules(result, rules, i)

        # Parse string to graph
        if start_position is None:
            start_position = (dimensions[0] / 2, dimensions[1] / 2)

        network = self._parse_to_network(
            result,
            start_position,
            dimensions
        )

        network.style = pattern
        return network

    def _apply_rules(
        self,
        string: str,
        rules: List[LSystemRule],
        iteration: int
    ) -> str:
        """Apply production rules to string."""
        result = []

        for i, symbol in enumerate(string):
            # Get context
            context = string[max(0, i-1):min(len(string), i+2)]

            # Find matching rule
            replaced = False
            for rule in rules:
                if rule.matches(symbol, context, iteration):
                    # Stochastic application
                    if self._rng.random() <= rule.probability:
                        result.append(rule.successor)
                        replaced = True
                        break

            if not replaced:
                result.append(symbol)

        return "".join(result)

    def _parse_to_network(
        self,
        string: str,
        start_position: Tuple[float, float],
        dimensions: Tuple[float, float]
    ) -> RoadNetwork:
        """Parse L-system string to road network."""
        nodes: List[RoadNode] = []
        edges: List[RoadEdge] = []
        node_positions: Dict[str, Tuple[float, float]] = {}

        # Stack for branching
        state_stack: List[TurtleState] = []

        # Current turtle state
        turtle = TurtleState(start_position[0], start_position[1], 0.0)

        # Current road being built
        current_road_points: List[Tuple[float, float]] = [start_position]
        current_road_type = "local"

        # Create initial node
        start_node = self._create_node(start_position, "intersection_4way")
        nodes.append(start_node)
        node_positions[start_node.id] = start_position
        last_node_id = start_node.id

        # Process each symbol
        for symbol in string:
            if symbol == "R":
                # Road segment
                length = self.config.segment_length * (1 + self._rng.uniform(
                    -self.config.variation, self.config.variation
                ))
                new_pos = turtle.move(length)

                # Check bounds
                if self._in_bounds(new_pos, dimensions):
                    current_road_points.append(new_pos)
                else:
                    # Hit boundary, create dead end
                    if len(current_road_points) > 1:
                        edge = self._create_edge(
                            last_node_id,
                            None,
                            current_road_points,
                            "local"
                        )
                        edges.append(edge)

                        # Create dead end node
                        dead_node = self._create_node(new_pos, "dead_end")
                        nodes.append(dead_node)
                        edge.to_node = dead_node.id

                    current_road_points = [new_pos]
                    last_node_id = None

            elif symbol == "H":
                # Highway segment
                current_road_type = "highway"
                length = self.config.segment_length * 2
                new_pos = turtle.move(length)

                if self._in_bounds(new_pos, dimensions):
                    current_road_points.append(new_pos)

            elif symbol == "+":
                # Turn left
                angle = self.config.angle * (1 + self._rng.uniform(
                    -self.config.variation, self.config.variation
                ))
                turtle.turn(angle)

                # End current road, start new one
                if len(current_road_points) > 1:
                    self._finish_road(
                        current_road_points,
                        current_road_type,
                        nodes,
                        edges,
                        node_positions,
                        last_node_id
                    )
                    last_node_id = nodes[-1].id if nodes else None

                current_road_points = [(turtle.x, turtle.y)]
                current_road_type = "local"

            elif symbol == "-":
                # Turn right
                angle = -self.config.angle * (1 + self._rng.uniform(
                    -self.config.variation, self.config.variation
                ))
                turtle.turn(angle)

                # End current road, start new one
                if len(current_road_points) > 1:
                    self._finish_road(
                        current_road_points,
                        current_road_type,
                        nodes,
                        edges,
                        node_positions,
                        last_node_id
                    )
                    last_node_id = nodes[-1].id if nodes else None

                current_road_points = [(turtle.x, turtle.y)]
                current_road_type = "local"

            elif symbol == "~":
                # Curve - small angle change
                angle = self._rng.uniform(-30, 30)
                turtle.turn(angle)

                length = self.config.segment_length * 0.7
                new_pos = turtle.move(length)

                if self._in_bounds(new_pos, dimensions):
                    current_road_points.append(new_pos)

            elif symbol == "[":
                # Push state (start branch)
                state_stack.append(turtle.copy())

                # End current road at branch point
                if len(current_road_points) > 1:
                    self._finish_road(
                        current_road_points,
                        current_road_type,
                        nodes,
                        edges,
                        node_positions,
                        last_node_id
                    )
                    last_node_id = nodes[-1].id

                current_road_points = [(turtle.x, turtle.y)]

            elif symbol == "]":
                # Pop state (end branch)
                if state_stack:
                    # Finish current road
                    if len(current_road_points) > 1:
                        self._finish_road(
                            current_road_points,
                            current_road_type,
                            nodes,
                            edges,
                            node_positions,
                            last_node_id
                        )

                    # Restore state
                    turtle = state_stack.pop()
                    current_road_points = [(turtle.x, turtle.y)]
                    last_node_id = None

            elif symbol == ".":
                # Dead end
                if len(current_road_points) > 1:
                    self._finish_road(
                        current_road_points,
                        current_road_type,
                        nodes,
                        edges,
                        node_positions,
                        last_node_id,
                        is_dead_end=True
                    )
                    current_road_points = [(turtle.x, turtle.y)]
                    last_node_id = nodes[-1].id if nodes else None

        # Finish final road
        if len(current_road_points) > 1:
            self._finish_road(
                current_road_points,
                current_road_type,
                nodes,
                edges,
                node_positions,
                last_node_id
            )

        # Update node connections
        self._update_node_connections(nodes, edges)

        return RoadNetwork(
            dimensions=dimensions,
            nodes=nodes,
            edges=edges,
            seed=self.seed,
        )

    def _in_bounds(self, pos: Tuple[float, float], dimensions: Tuple[float, float]) -> bool:
        """Check if position is within bounds."""
        margin = 5.0
        return (margin <= pos[0] <= dimensions[0] - margin and
                margin <= pos[1] <= dimensions[1] - margin)

    def _create_node(
        self,
        position: Tuple[float, float],
        node_type: str
    ) -> RoadNode:
        """Create a new node."""
        node = RoadNode(
            id=f"node_{self._node_counter}",
            position=position,
            node_type=node_type,
        )
        self._node_counter += 1
        return node

    def _create_edge(
        self,
        from_node: str,
        to_node: Optional[str],
        curve_points: List[Tuple[float, float]],
        road_type: str
    ) -> RoadEdge:
        """Create a new edge."""
        lane_config = LaneConfig(
            count=4 if road_type == "highway" else 2,
            width=3.5,
        )

        edge = RoadEdge(
            id=f"edge_{self._edge_counter}",
            from_node=from_node or "",
            to_node=to_node or "",
            road_type=road_type,
            curve_points=curve_points,
            lanes=lane_config,
        )
        self._edge_counter += 1
        return edge

    def _finish_road(
        self,
        points: List[Tuple[float, float]],
        road_type: str,
        nodes: List[RoadNode],
        edges: List[RoadEdge],
        node_positions: Dict[str, Tuple[float, float]],
        last_node_id: Optional[str],
        is_dead_end: bool = False
    ) -> None:
        """Finish a road segment and add to network."""
        if len(points) < 2:
            return

        # Create end node
        end_type = "dead_end" if is_dead_end else "intersection_4way"
        end_node = self._create_node(points[-1], end_type)
        nodes.append(end_node)

        # Create edge
        edge = self._create_edge(
            last_node_id or "",
            end_node.id,
            points,
            road_type
        )
        edges.append(edge)

    def _update_node_connections(
        self,
        nodes: List[RoadNode],
        edges: List[RoadEdge]
    ) -> None:
        """Update node connection lists."""
        for node in nodes:
            node.connections = []

        for edge in edges:
            from_node = next((n for n in nodes if n.id == edge.from_node), None)
            to_node = next((n for n in nodes if n.id == edge.to_node), None)

            if from_node and edge.id not in from_node.connections:
                from_node.connections.append(edge.id)
            if to_node and edge.id not in to_node.connections:
                to_node.connections.append(edge.id)

        # Update node types based on connections
        for node in nodes:
            conn_count = len(node.connections)
            if conn_count == 1:
                node.node_type = "dead_end"
            elif conn_count == 2:
                node.node_type = "curve_point"
            elif conn_count == 3:
                node.node_type = "intersection_3way"
            elif conn_count >= 4:
                node.node_type = "intersection_4way"
                node.has_traffic_light = True


def generate_road_network(
    pattern: str = "grid",
    dimensions: Tuple[float, float] = (200.0, 200.0),
    iterations: int = 3,
    seed: Optional[int] = None,
) -> RoadNetwork:
    """
    Convenience function to generate a road network.

    Args:
        pattern: Pattern name (grid, organic, suburban, highway, downtown)
        dimensions: Network dimensions
        iterations: Number of L-system iterations
        seed: Random seed

    Returns:
        Generated RoadNetwork
    """
    # Choose axiom based on pattern
    axioms = {
        "grid": "R+R+R+R",  # Square starting shape
        "organic": "R~R~R~R",  # Curved starting shape
        "suburban": "R[R]R[R]R",  # Branching starting shape
        "highway": "H+H+H+H",  # Highway square
        "downtown": "R+R+R+R",  # Dense grid square
    }

    axiom = axioms.get(pattern, "R+R+R+R")

    generator = LSystemRoads(seed=seed)
    return generator.generate(axiom, iterations, pattern, dimensions)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "LSystemRule",
    "LSystemConfig",
    "LSystemRoads",
    "ROAD_RULE_SETS",
    "SYMBOL_MEANINGS",
    "generate_road_network",
]
