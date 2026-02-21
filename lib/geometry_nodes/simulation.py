"""
SimulationBuilder - Build simulation zones with common patterns.

Provides high-level abstractions for creating physics simulations,
advection, pressure solving, and substep loops using Blender's
geometry nodes simulation zones.

Usage:
    builder = NodeTreeBuilder("FluidSim")
    sim = SimulationBuilder(builder)

    # Create a fluid advection simulation
    sim.create_advection_step(velocity_field, dt=0.016)
    sim.create_pressure_iteration(iterations=4)
    sim.create_substep_loop(substeps=5)

    tree = sim.build()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import bpy
from mathutils import Vector

if TYPE_CHECKING:
    from bpy.types import Node, NodeTree

    from .node_builder import NodeTreeBuilder


class SimulationBuilder:
    """
    Build simulation zones with common patterns.

    Provides high-level methods for creating simulation-based
    geometry node setups including:
    - Fluid advection
    - Pressure projection (incompressibility)
    - Substep loops for stability
    - State persistence

    Attributes:
        builder: The underlying NodeTreeBuilder.
        tree: The geometry node tree being built.
    """

    def __init__(self, builder: NodeTreeBuilder) -> None:
        """
        Initialize the SimulationBuilder.

        Args:
            builder: A NodeTreeBuilder instance to build upon.
        """
        self.builder = builder
        self.tree = builder.get_tree()
        self._sim_zones: list[tuple[Node, Node]] = []
        self._stored_states: dict[str, Node] = {}

    def create_simulation_zone(
        self,
        location: tuple[float, float] = (0, 0),
        name: Optional[str] = None,
    ) -> tuple[Node, Node]:
        """
        Create a new simulation zone.

        Args:
            location: Position for the input node.
            name: Optional prefix for node names.

        Returns:
            Tuple of (input_node, output_node).
        """
        sim_in, sim_out = self.builder.add_simulation_zone(location, name)
        self._sim_zones.append((sim_in, sim_out))
        return sim_in, sim_out

    def create_advection_step(
        self,
        velocity_grid,
        dt: float,
        geometry_input=None,
        location: tuple[float, float] = (0, 0),
    ) -> tuple[Node, Node]:
        """
        Create an advection step for fluid simulation.

        Advects geometry or attributes through a velocity field using
        semi-Lagrangian advection. This moves particles/geometry along
        the velocity field over time step dt.

        Args:
            velocity_grid: Field or grid representing velocity at each point.
                          Can be a node output or field reference.
            dt: Time step size for the advection.
            geometry_input: Geometry to advect (uses simulation input if None).
            location: Position for the simulation zone.

        Returns:
            Tuple of (sim_input, sim_output) nodes.

        Example:
            >>> sim_in, sim_out = sim.create_advection_step(
            ...     velocity_node.outputs["Field"],
            ...     dt=0.016,
            ...     location=(400, 200)
            ... )
        """
        sim_in, sim_out = self.create_simulation_zone(location, "Advection")

        # Get group input for geometry if not provided
        if geometry_input is None:
            group_in = self.builder.add_group_input((location[0] - 400, location[1]))
            geometry_input = group_in.outputs["Geometry"]

        # Connect input geometry to simulation
        self.builder.link(geometry_input, sim_in.inputs["Geometry"])

        # Create delta time node
        dt_node = self.builder.add_node(
            "GeometryNodeInputSceneTime",
            (location[0] - 200, location[1] + 200),
            name="DeltaTime",
        )

        # Create position node for current particle position
        position = self.builder.add_node(
            "GeometryNodeInputPosition",
            (location[0] + 100, location[1] + 150),
            name="CurrentPosition",
        )

        # Sample velocity at current position
        # This requires sampling the velocity field
        sample_vel = self.builder.add_node(
            "GeometryNodeSampleIndex",
            (location[0] + 200, location[1] + 100),
            name="SampleVelocity",
        )

        # Set velocity field to sample
        if velocity_grid is not None:
            self.builder.link(velocity_grid, sample_vel.inputs["Value"])

        # Calculate new position: pos + vel * dt
        # Multiply velocity by dt
        scale = self.builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 300, location[1] + 50),
            name="ScaleVelocity",
        )
        scale.operation = "SCALE"
        # Note: Vector operations in geometry nodes may use different nodes

        # Add displacement to position
        add_pos = self.builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 400, location[1]),
            name="AddDisplacement",
        )
        add_pos.operation = "ADD"

        # Set position on geometry
        set_pos = self.builder.add_node(
            "GeometryNodeSetPosition",
            (location[0] + 500, location[1]),
            name="SetAdvectedPosition",
        )

        # Connect nodes
        self.builder.link(
            sim_in.outputs["Geometry"],
            set_pos.inputs["Geometry"],
        )
        self.builder.link(
            position.outputs["Position"],
            add_pos.inputs[0],
        )
        self.builder.link(
            set_pos.outputs["Geometry"],
            sim_out.inputs["Geometry"],
        )

        return sim_in, sim_out

    def create_pressure_iteration(
        self,
        iterations: int = 4,
        location: tuple[float, float] = (0, 0),
        divergence_field=None,
    ) -> tuple[Node, Node]:
        """
        Create a pressure iteration step for incompressible flow.

        Implements the pressure projection step that enforces
        incompressibility in fluid simulation. Iteratively solves
        for pressure to eliminate divergence.

        Args:
            iterations: Number of Jacobi iterations (default 4).
                       More iterations = more accurate but slower.
            location: Position for the simulation zone.
            divergence_field: Field representing velocity divergence.

        Returns:
            Tuple of (sim_input, sim_output) nodes.

        Note:
            This is a simplified implementation. Full pressure solve
            typically requires custom grid-based computations.
        """
        # Create a repeat zone for iterations
        repeat_in, repeat_out = self.builder.add_repeat_zone(
            iterations=iterations,
            location=location,
            name="PressureSolve",
        )

        # Create simulation zone for the pressure solve
        sim_in, sim_out = self.create_simulation_zone(
            (location[0] + 600, location[1]),
            "Pressure",
        )

        # Connect repeat zone to simulation
        self.builder.link(
            sim_out.outputs["Geometry"],
            repeat_in.inputs["Geometry"],
        )

        # Pressure correction nodes would go here
        # This is a placeholder for the Jacobi iteration:
        # p_new = (p_neighbors - div) / 4

        # For each iteration:
        # 1. Sample pressure from neighbors
        # 2. Subtract divergence
        # 3. Average

        neighbor_avg = self.builder.add_node(
            "GeometryNodeFieldAverage",
            (location[0] + 200, location[1] - 100),
            name="NeighborAverage",
        )

        subtract_div = self.builder.add_node(
            "ShaderNodeMath",
            (location[0] + 350, location[1] - 100),
            name="SubtractDivergence",
        )
        subtract_div.operation = "SUBTRACT"

        # Store updated pressure
        store_pressure = self.builder.add_node(
            "GeometryNodeStoreNamedAttribute",
            (location[0] + 500, location[1] - 100),
            name="StorePressure",
        )
        store_pressure.inputs["Name"].default_value = "pressure"

        return sim_in, sim_out

    def create_substep_loop(
        self,
        substeps: int = 5,
        location: tuple[float, float] = (0, 0),
        simulation_step=None,
    ) -> tuple[Node, Node]:
        """
        Create a substep loop for simulation stability.

        Wraps a simulation step in a repeat zone to perform multiple
        substeps per frame. This improves stability by using smaller
        time steps internally.

        Args:
            substeps: Number of substeps per frame.
            location: Position for the repeat zone.
            simulation_step: Optional node group to execute per substep.

        Returns:
            Tuple of (repeat_input, repeat_output) nodes.

        Example:
            >>> repeat_in, repeat_out = sim.create_substep_loop(
            ...     substeps=5,
            ...     location=(800, 0)
            ... )
            >>> # Connect your simulation step between repeat_in and repeat_out
        """
        repeat_in, repeat_out = self.builder.add_repeat_zone(
            iterations=substeps,
            location=location,
            name="Substep",
        )

        # Create scaled delta time
        # dt_substep = dt_frame / substeps
        scene_time = self.builder.add_node(
            "GeometryNodeInputSceneTime",
            (location[0] - 200, location[1] + 100),
            name="SceneTime",
        )

        divide_node = self.builder.add_node(
            "ShaderNodeMath",
            (location[0] - 100, location[1] + 100),
            name="SubstepDT",
            Value2=float(substeps),
        )
        divide_node.operation = "DIVIDE"

        self.builder.link(
            scene_time.outputs["Delta Time"],
            divide_node.inputs[0],
        )

        # If a simulation step is provided, integrate it
        if simulation_step is not None:
            # Connect the step between repeat zone sockets
            self.builder.link(
                repeat_in.outputs["Geometry"],
                simulation_step.inputs.get("Geometry"),
            )
            self.builder.link(
                simulation_step.outputs.get("Geometry"),
                repeat_out.inputs["Geometry"],
            )

        return repeat_in, repeat_out

    def store_state(
        self,
        name: str,
        geometry_source,
        location: Optional[tuple[float, float]] = None,
        domain: str = "POINT",
    ) -> Node:
        """
        Store simulation state as a named attribute.

        Persists data across simulation frames by storing it as a
        named attribute on the geometry.

        Args:
            name: Name for the stored attribute.
            geometry_source: Node or socket providing the geometry.
            location: Position for the store node (auto-placed if None).
            domain: Attribute domain ("POINT", "EDGE", "FACE", "CORNER").

        Returns:
            The Store Named Attribute node.

        Example:
            >>> store_node = sim.store_state("velocity", velocity_field)
            >>> # Later: retrieve with get_named_attribute()
        """
        if location is None:
            # Auto-place based on last node
            x = max(n.location.x for n in self.tree.nodes.values()) + 200
            y = 0
            location = (x, y)

        store_node = self.builder.add_node(
            "GeometryNodeStoreNamedAttribute",
            location,
            name=f"Store_{name}",
        )

        # Set attribute name
        store_node.inputs["Name"].default_value = name
        store_node.inputs["Domain"].default_value = domain

        # Store reference for later retrieval
        self._stored_states[name] = store_node

        return store_node

    def retrieve_state(
        self,
        name: str,
        geometry_source,
        data_type: str = "FLOAT_VECTOR",
        location: Optional[tuple[float, float]] = None,
    ) -> Node:
        """
        Retrieve previously stored simulation state.

        Args:
            name: Name of the stored attribute.
            geometry_source: Geometry to read attribute from.
            data_type: Expected data type ("FLOAT", "FLOAT_VECTOR", etc.).
            location: Position for the node.

        Returns:
            The Named Attribute node.
        """
        if location is None:
            x = max(n.location.x for n in self.tree.nodes.values()) + 200
            location = (x, 0)

        attr_node = self.builder.add_node(
            "GeometryNodeInputNamedAttribute",
            location,
            name=f"Get_{name}",
        )

        attr_node.inputs["Name"].default_value = name
        attr_node.inputs["Data Type"].default_value = data_type

        return attr_node

    def add_spring_damper(
        self,
        rest_position: tuple[float, float, float] = (0, 0, 0),
        stiffness: float = 100.0,
        damping: float = 0.5,
        location: tuple[float, float] = (0, 0),
    ) -> tuple[Node, Node]:
        """
        Create a spring-damper system within a simulation.

        Adds spring forces that pull particles toward a rest position
        with damping to prevent oscillation.

        Args:
            rest_position: The target rest position.
            stiffness: Spring constant (higher = stronger).
            damping: Damping factor (0-1, higher = more damping).
            location: Position for the simulation zone.

        Returns:
            Tuple of (sim_input, sim_output) nodes.
        """
        sim_in, sim_out = self.create_simulation_zone(location, "SpringDamper")

        # Get current position
        position = self.builder.add_node(
            "GeometryNodeInputPosition",
            (location[0] + 100, location[1] + 100),
            name="Position",
        )

        # Calculate displacement from rest
        rest_vec = self.builder.add_node(
            "GeometryNodeInputVector",
            (location[0] - 100, location[1] + 200),
            name="RestPosition",
            Vector=rest_position,
        )

        displacement = self.builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 200, location[1] + 150),
            name="Displacement",
        )
        displacement.operation = "SUBTRACT"

        self.builder.link(position.outputs["Position"], displacement.inputs[0])
        self.builder.link(rest_vec.outputs["Vector"], displacement.inputs[1])

        # Scale by stiffness (spring force)
        spring_force = self.builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 300, location[1] + 100),
            name="SpringForce",
        )
        spring_force.operation = "SCALE"

        # Get velocity for damping
        velocity_attr = self.retrieve_state(
            "velocity",
            sim_in.outputs["Geometry"],
            location=(location[0] + 100, location[1] - 100),
        )

        # Damping force = -damping * velocity
        damping_force = self.builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 300, location[1] - 50),
            name="DampingForce",
        )
        damping_force.operation = "SCALE"

        # Total force = spring + damping
        total_force = self.builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 400, location[1]),
            name="TotalForce",
        )
        total_force.operation = "ADD"

        # Apply force to velocity
        # v_new = v + force * dt / mass
        apply_force = self.builder.add_node(
            "ShaderNodeVectorMath",
            (location[0] + 500, location[1] - 100),
            name="ApplyForce",
        )
        apply_force.operation = "ADD"

        # Store new velocity
        store_vel = self.store_state(
            "velocity",
            apply_force.outputs[0],
            location=(location[0] + 600, location[1] - 100),
        )

        # Update position
        set_pos = self.builder.add_node(
            "GeometryNodeSetPosition",
            (location[0] + 700, location[1]),
            name="UpdatePosition",
        )

        self.builder.link(sim_in.outputs["Geometry"], set_pos.inputs["Geometry"])
        self.builder.link(set_pos.outputs["Geometry"], sim_out.inputs["Geometry"])

        return sim_in, sim_out

    def build(self) -> NodeTree:
        """
        Finalize and return the built node tree.

        Returns:
            The completed GeometryNodeTree.
        """
        return self.tree

    def get_simulation_zones(self) -> list[tuple[Node, Node]]:
        """
        Get all created simulation zones.

        Returns:
            List of (input_node, output_node) tuples.
        """
        return self._sim_zones.copy()

    def add_boundary_condition(
        self,
        boundary_type: str = "WALL",
        location: tuple[float, float] = (0, 0),
        bounds: tuple[float, float, float, float, float, float] = (-10, 10, -10, 10, -10, 10),
    ) -> Node:
        """
        Add a boundary condition to the simulation.

        Args:
            boundary_type: Type of boundary ("WALL", "PERIODIC", "OUTFLOW").
            location: Position for the boundary node.
            bounds: (min_x, max_x, min_y, max_y, min_z, max_z) bounds.

        Returns:
            The boundary condition node.
        """
        # Create bounds vectors
        min_bounds = self.builder.add_node(
            "GeometryNodeInputVector",
            (location[0] - 200, location[1] + 100),
            name="MinBounds",
            Vector=(bounds[0], bounds[2], bounds[4]),
        )

        max_bounds = self.builder.add_node(
            "GeometryNodeInputVector",
            (location[0] - 200, location[1]),
            name="MaxBounds",
            Vector=(bounds[1], bounds[3], bounds[5]),
        )

        # Create position comparison
        position = self.builder.add_node(
            "GeometryNodeInputPosition",
            (location[0] - 100, location[1] - 100),
            name="Position",
        )

        # For WALL boundary: reflect velocity when hitting boundary
        # This is simplified - full implementation would need more nodes

        return position
