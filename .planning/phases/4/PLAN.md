# Phase 4: Road & Urban Infrastructure - Scene Generation System

---
phase: 04-urban-infrastructure
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: true

must_haves:
  truths:
    - "Road networks can be generated from L-system rules"
    - "Road geometry includes lanes, markings, and curbs"
    - "Intersections connect multiple road segments"
    - "Street signs follow MUTCD standard dimensions"
    - "Street lights illuminate roads at configurable spacing"
    - "Urban furniture can be placed along roads"
    - "Pavement materials define road surface appearance"
    - "Crosswalks and road markings render correctly"
  artifacts:
    - path: "lib/urban/__init__.py"
      provides: "Urban infrastructure package exports"
    - path: "lib/urban/l_system.py"
      provides: "L-system road network generation (Python)"
      contains: "class LSystemRoads"
    - path: "lib/urban/road_network.py"
      provides: "RoadNetwork data structure and JSON serialization"
      exports: ["RoadNetwork", "RoadSegment", "Node", "Edge"]
    - path: "lib/urban/road_geometry.py"
      provides: "GN road geometry builder from JSON"
      contains: "create_road_geometry_node_group"
    - path: "lib/urban/intersections.py"
      provides: "Intersection geometry (4-way, 3-way, roundabout)"
    - path: "lib/urban/signage.py"
      provides: "MUTCD sign library"
      contains: "SIGN_DIMENSIONS"
    - path: "lib/urban/lighting.py"
      provides: "Street light system"
    - path: "lib/urban/furniture.py"
      provides: "Urban furniture (benches, bollards, etc.)"
    - path: "lib/urban/markings.py"
      provides: "Crosswalk and road marking system"
    - path: "configs/urban/road_presets.yaml"
      provides: "Road style presets"
    - path: "configs/urban/sign_presets.yaml"
      provides: "MUTCD sign configurations"
  key_links:
    - from: "lib/urban/l_system.py"
      to: "lib/urban/road_network.py"
      via: "RoadNetwork JSON output"
      pattern: "to_json\\(\\)"
    - from: "lib/urban/road_network.py"
      to: "lib/urban/road_geometry.py"
      via: "JSON file or dict"
      pattern: "from_json\\(\\)"
    - from: "lib/animation/city/road_network.py"
      to: "lib/urban/"
      via: "Reference existing patterns"
      pattern: "RoadSegment|LaneConfig"
---

<objective>
Implement a complete Road & Urban Infrastructure system using a hybrid Python + Geometry Nodes architecture.

Purpose: Generate realistic road networks and urban street elements for scene composition. The L-system road generation runs in Python because Geometry Nodes cannot perform string manipulation, then the JSON output is consumed by GN for geometry generation.

Output: A complete urban infrastructure module with 8 sub-modules, YAML presets, and integration with existing city animation systems.
</objective>

<execution_context>
@/Users/bretbouchard/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bretbouchard/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/Users/bretbouchard/apps/blender_gsd/.planning/PROJECT.md
@/Users/bretbouchard/apps/blender_gsd/.planning/STATE.md
@/Users/bretbouchard/apps/blender_gsd/lib/animation/city/road_network.py
@/Users/bretbouchard/apps/blender_gsd/lib/animation/city/street_elements.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create Urban Package Foundation with L-System Road Generator</name>
  <files>
    lib/urban/__init__.py
    lib/urban/types.py
    lib/urban/l_system.py
    lib/urban/road_network.py
    configs/urban/road_presets.yaml
  </files>
  <action>
    Create the urban infrastructure package foundation with L-system road generation.

    **1. Create lib/urban/__init__.py:**
    - Package initialization with version and exports
    - Export all public classes and functions from sub-modules

    **2. Create lib/urban/types.py:**
    - UrbanConfig base dataclass
    - RoadType enum (HIGHWAY, ARTERIAL, URBAN, RESIDENTIAL, INDUSTRIAL, DOWNTOWN)
    - IntersectionType enum (FOUR_WAY, THREE_WAY, T_JUNCTION, ROUNDABOUT)
    - SignType enum (STOP, YIELD, SPEED_LIMIT, WARNING, REGULATORY, GUIDE)
    - MarkingType enum (SOLID, DASHED, DOUBLE_YELLOW, CROSSWALK, STOP_LINE)
    - LampType enum (MODERN, TRADITIONAL, HIGHWAY, ORNATE)
    - FurnitureType enum (BENCH, BOLLARD, TRASH_CAN, BUS_STOP, FIRE_HYDRANT)

    **3. Create lib/urban/l_system.py (CRITICAL - Python-only):**
    L-system road generation that runs in Python, NOT Geometry Nodes, because:
    - GN has no string manipulation capabilities
    - L-system requires context-sensitive rule evaluation
    - String rewriting rules cannot be expressed in GN

    ```python
    @dataclass
    class LSystemConfig:
        axiom: str
        rules: Dict[str, str]
        iterations: int
        angle: float  # Turn angle in degrees
        segment_length: float  # Base segment length
        seed: Optional[int] = None

    class LSystemRoads:
        """L-system road network generation.

        Runs in Python (not GN) because:
        - Requires string rewriting rules
        - Needs context-sensitive rule evaluation
        - GN has no string manipulation

        Output: JSON road network consumed by GN Road Builder
        """

        # Default road generation rules
        DEFAULT_RULES = {
            "road": "road+road",           # Split into two roads
            "+": "turn[road]turn",         # Branch with turn
            "turn": "turn-turn",           # Create intersection
            "[": "push",                   # Push state (start branch)
            "]": "pop",                    # Pop state (end branch)
        }

        def __init__(self, config: LSystemConfig):
            self.config = config
            self.rng = random.Random(config.seed)

        def generate(self, axiom: str = None, iterations: int = None) -> str:
            """Apply L-system rules for N iterations."""
            result = axiom or self.config.axiom
            iters = iterations or self.config.iterations

            for _ in range(iters):
                result = self._apply_rules(result)

            return result

        def _apply_rules(self, string: str) -> str:
            """Apply production rules to string."""
            result = []
            for char in string:
                if char in self.config.rules:
                    # Stochastic rule selection if multiple rules
                    result.append(self.config.rules[char])
                else:
                    result.append(char)
            return ''.join(result)

        def parse_to_network(self, lstring: str) -> RoadNetwork:
            """Parse L-system string to road network structure.

            Turtle graphics interpretation:
            - F/road: Move forward, create segment
            - +: Turn left by angle
            - -: Turn right by angle
            - [: Push state (position, heading)
            - ]: Pop state
            """
            network = RoadNetwork()
            stack = []
            pos = Vector((0, 0, 0))
            heading = 0.0  # Degrees, 0 = +X

            i = 0
            segment_id = 0
            while i < len(lstring):
                char = lstring[i]

                if char == 'F' or char == 'r':  # road segment
                    # Calculate end position
                    rad = math.radians(heading)
                    dx = self.config.segment_length * math.cos(rad)
                    dy = self.config.segment_length * math.sin(rad)
                    end = Vector((pos.x + dx, pos.y + dy, pos.z))

                    # Create segment
                    segment = RoadSegment(
                        id=f"seg_{segment_id}",
                        start=tuple(pos),
                        end=tuple(end),
                        heading=heading
                    )
                    network.add_segment(segment)
                    segment_id += 1
                    pos = end

                elif char == '+':  # Turn left
                    heading += self.config.angle

                elif char == '-':  # Turn right
                    heading -= self.config.angle

                elif char == '[':  # Push state
                    stack.append((Vector(pos), heading))

                elif char == ']':  # Pop state
                    if stack:
                        pos, heading = stack.pop()

                i += 1

            return network
    ```

    **4. Create lib/urban/road_network.py:**
    - RoadNetwork class with segments and intersections
    - JSON serialization for GN consumption
    - Reference existing patterns from lib/animation/city/road_network.py

    ```python
    @dataclass
    class RoadSegment:
        id: str
        start: Tuple[float, float, float]
        end: Tuple[float, float, float]
        lanes_forward: int = 2
        lanes_backward: int = 2
        road_type: RoadType = RoadType.URBAN
        width: float = 7.0  # meters
        name: str = ""
        heading: float = 0.0  # Direction in degrees

        def to_dict(self) -> Dict:
            return {
                "id": self.id,
                "start": list(self.start),
                "end": list(self.end),
                "lanes_forward": self.lanes_forward,
                "lanes_backward": self.lanes_backward,
                "road_type": self.road_type.value,
                "width": self.width,
                "name": self.name,
                "heading": self.heading,
            }

    @dataclass
    class Intersection:
        id: str
        position: Tuple[float, float, float]
        intersection_type: IntersectionType
        connected_segments: List[str]
        radius: float = 10.0  # meters

    class RoadNetwork:
        """Road network data structure with JSON export for GN."""

        def __init__(self, name: str = "RoadNetwork"):
            self.name = name
            self.segments: Dict[str, RoadSegment] = {}
            self.intersections: Dict[str, Intersection] = {}

        def add_segment(self, segment: RoadSegment) -> None:
            self.segments[segment.id] = segment

        def add_intersection(self, intersection: Intersection) -> None:
            self.intersections[intersection.id] = intersection

        def detect_intersections(self) -> None:
            """Auto-detect intersections where segments meet."""
            # Find segment endpoints that are close together
            pass

        def to_json(self, path: str = None) -> str:
            """Export to JSON for GN consumption."""
            data = {
                "name": self.name,
                "segments": [s.to_dict() for s in self.segments.values()],
                "intersections": [asdict(i) for i in self.intersections.values()],
            }
            json_str = json.dumps(data, indent=2)
            if path:
                Path(path).write_text(json_str)
            return json_str

        @classmethod
        def from_json(cls, path_or_data: Union[str, Dict]) -> 'RoadNetwork':
            """Load from JSON file or dict."""
            if isinstance(path_or_data, str):
                data = json.loads(Path(path_or_data).read_text())
            else:
                data = path_or_data

            network = cls(name=data.get("name", "RoadNetwork"))
            for seg_data in data.get("segments", []):
                segment = RoadSegment(
                    id=seg_data["id"],
                    start=tuple(seg_data["start"]),
                    end=tuple(seg_data["end"]),
                    lanes_forward=seg_data.get("lanes_forward", 2),
                    lanes_backward=seg_data.get("lanes_backward", 2),
                    road_type=RoadType(seg_data.get("road_type", "urban")),
                    width=seg_data.get("width", 7.0),
                )
                network.add_segment(segment)
            return network
    ```

    **5. Create configs/urban/road_presets.yaml:**
    ```yaml
    # Road style presets
    highway:
      lanes_forward: 3
      lanes_backward: 3
      width: 21.0  # 3.5m per lane
      surface_color: [0.15, 0.15, 0.15]
      has_sidewalk: false
      marking_color: [1.0, 1.0, 1.0]

    arterial:
      lanes_forward: 2
      lanes_backward: 2
      width: 14.0
      surface_color: [0.18, 0.18, 0.18]
      has_sidewalk: true
      sidewalk_width: 2.5

    urban:
      lanes_forward: 1
      lanes_backward: 1
      width: 7.0
      surface_color: [0.2, 0.2, 0.2]
      has_sidewalk: true
      sidewalk_width: 3.0

    residential:
      lanes_forward: 1
      lanes_backward: 1
      width: 6.0
      surface_color: [0.25, 0.25, 0.25]
      has_sidewalk: true
      sidewalk_width: 2.0

    # L-system presets
    l_system_presets:
      grid_city:
        axiom: "road+road+road+road"
        rules:
          "road": "road+road"
          "+": "turn[road]turn"
        iterations: 3
        angle: 90
        segment_length: 100

      organic_city:
        axiom: "road"
        rules:
          "road": "road+road-[road]+road"
          "+": "turn"
          "-": "turn"
        iterations: 4
        angle: 60
        segment_length: 50

      suburban:
        axiom: "road[+road][-road]road"
        rules:
          "road": "roadroad"
          "+": "+"
          "-": "-"
        iterations: 2
        angle: 45
        segment_length: 80
    ```

    Reference the existing lib/animation/city/road_network.py for LaneConfig, RoadStyle, and ROAD_PRESETS patterns.
  </action>
  <verify>
    python -c "from lib.urban import LSystemRoads, RoadNetwork, LSystemConfig; print('Urban foundation OK')"
    python -c "from lib.urban.l_system import LSystemRoads; ls = LSystemRoads(LSystemConfig(axiom='road', rules={}, iterations=1)); print('LSystem OK')"
    python -c "from lib.urban.road_network import RoadNetwork; rn = RoadNetwork(); print('RoadNetwork OK')"
    ls -la configs/urban/road_presets.yaml
  </verify>
  <done>
    - lib/urban/__init__.py exists with package exports
    - lib/urban/types.py exists with all enums and dataclasses
    - lib/urban/l_system.py exists with LSystemRoads class
    - lib/urban/road_network.py exists with RoadNetwork, RoadSegment, Intersection
    - configs/urban/road_presets.yaml exists with road and L-system presets
    - L-system generate() produces valid strings
    - L-system parse_to_network() produces RoadNetwork with segments
    - RoadNetwork.to_json() produces valid JSON
    - RoadNetwork.from_json() reconstructs network from JSON
  </done>
</task>

<task type="auto">
  <name>Task 2: Implement Road Geometry Builder (GN from JSON)</name>
  <files>
    lib/urban/road_geometry.py
    lib/urban/intersections.py
  </files>
  <action>
    Create Geometry Nodes-based road geometry builders that consume JSON from the Python L-system.

    **1. Create lib/urban/road_geometry.py:**
    This module creates Blender Geometry Node groups that consume the JSON road network.

    ```python
    """Road Geometry Builder - GN consumption of JSON road network.

    Architecture:
    1. Python L-system generates JSON road network
    2. This module creates GN node groups that read JSON
    3. GN generates actual geometry (lanes, markings, curbs)

    Why GN for geometry:
    - Real-time viewport updates
    - Procedural detail (cracks, wear)
    - Material variations
    - Non-destructive editing
    """

    class RoadGeometryBuilder:
        """Creates GN node groups for road geometry from JSON."""

        def __init__(self):
            self.node_groups = {}

        def create_road_builder_node_group(self, name: str = "Urban_Road_Builder") -> bpy.types.NodeGroup:
            """Create the main road builder node group.

            Inputs:
            - road_json: String input containing JSON road network
            - road_preset: Enum for road style (highway, urban, etc.)
            - detail_level: Float 0-1 for geometry detail

            Outputs:
            - Geometry: Complete road mesh with lanes, markings, curbs
            """
            # Create node group
            ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')

            # Create inputs
            ng.interface.new_socket("road_json", socket_type='NodeSocketString')
            ng.interface.new_socket("road_preset", socket_type='NodeSocketString')
            ng.interface.new_socket("detail_level", socket_type='NodeSocketFloat')

            # Create outputs
            ng.interface.new_socket("Geometry", socket_type='NodeSocketGeometry')

            # Add nodes for JSON parsing (using String to Value nodes)
            # Note: Complex JSON parsing may need Python driver nodes
            # or pre-processed input sockets

            # Add mesh generation nodes
            # - Curve to mesh for road surface
            # - Instances for lane markings
            # - Boolean for intersections

            return ng

        def create_lane_marking_node_group(self) -> bpy.types.NodeGroup:
            """Create node group for lane markings.

            Generates dashed/solid lines along road centerline.
            """
            pass

        def create_curb_node_group(self) -> bpy.types.NodeGroup:
            """Create node group for road curbs.

            Generates curb geometry along road edges.
            """
            pass

        def build_from_network(self, network: RoadNetwork, collection: bpy.types.Collection = None) -> List[bpy.types.Object]:
            """Build road geometry from RoadNetwork object.

            This is the Python-side builder for cases where GN is not needed
            or for pre-baking geometry.

            Returns list of created objects.
            """
            objects = []

            for segment in network.segments.values():
                # Create curve for road path
                curve_data = bpy.data.curves.new(f"Road_{segment.id}", 'CURVE')
                curve_data.dimensions = '3D'

                spline = curve_data.splines.new('POLY')
                spline.points.add(1)  # Need 2 points total
                spline.points[0].co = (*segment.start, 1.0)
                spline.points[1].co = (*segment.end, 1.0)

                curve_obj = bpy.data.objects.new(f"Road_{segment.id}", curve_data)

                # Add road geometry modifier
                self._add_road_geometry_modifier(curve_obj, segment)

                if collection:
                    collection.objects.link(curve_obj)
                else:
                    bpy.context.collection.objects.link(curve_obj)

                objects.append(curve_obj)

            return objects

        def _add_road_geometry_modifier(self, obj: bpy.types.Object, segment: RoadSegment) -> None:
            """Add GN modifier for road geometry."""
            mod = obj.modifiers.new("RoadGeometry", 'NODES')

            # Set node group (create if not exists)
            if "Urban_Road_Segment" not in bpy.data.node_groups:
                self._create_segment_node_group()

            mod.node_group = bpy.data.node_groups["Urban_Road_Segment"]

            # Set input values
            mod['Input_1_width'] = segment.width
            mod['Input_2_lanes'] = segment.lanes_forward + segment.lanes_backward

        def _create_segment_node_group(self) -> bpy.types.NodeGroup:
            """Create reusable node group for road segment."""
            ng = bpy.data.node_groups.new("Urban_Road_Segment", 'GeometryNodeTree')

            # Inputs
            ng.interface.new_socket("width", socket_type='NodeSocketFloat', default_value=7.0)
            ng.interface.new_socket("lanes", socket_type='NodeSocketInt', default_value=2)

            # Output
            ng.interface.new_socket("Geometry", socket_type='NodeSocketGeometry')

            # Build node tree
            # 1. Input curve
            # 2. Curve to mesh with width
            # 3. Subdivide for markings
            # 4. Material assignment

            return ng
    ```

    **2. Create lib/urban/intersections.py:**
    ```python
    """Intersection geometry system.

    Types:
    - 4-way: Standard cross intersection
    - 3-way: T-junction
    - Roundabout: Circular traffic flow
    """

    @dataclass
    class IntersectionConfig:
        intersection_type: IntersectionType
        radius: float = 10.0  # meters
        has_traffic_lights: bool = True
        has_crosswalk: bool = True
        lane_width: float = 3.5

    class IntersectionBuilder:
        """Creates intersection geometry."""

        def create_four_way(self, config: IntersectionConfig) -> bpy.types.Object:
            """Create 4-way intersection geometry."""
            # Create square pad
            # Add crosswalk markings
            # Add traffic light posts if enabled
            pass

        def create_three_way(self, config: IntersectionConfig) -> bpy.types.Object:
            """Create T-junction geometry."""
            pass

        def create_roundabout(self, config: IntersectionConfig) -> bpy.types.Object:
            """Create roundabout geometry.

            Includes:
            - Central island
            - Circulatory roadway
            - Entry/exit lanes
            """
            pass

        def detect_and_create(self, network: RoadNetwork) -> List[bpy.types.Object]:
            """Detect intersection points in network and create geometry."""
            # Find where 3+ segments meet
            # Create appropriate intersection type
            pass
    ```

    Reference lib/animation/city/road_network.py Intersection class for existing patterns.
  </action>
  <verify>
    python -c "from lib.urban.road_geometry import RoadGeometryBuilder; print('RoadGeometry OK')"
    python -c "from lib.urban.intersections import IntersectionBuilder, IntersectionConfig; print('Intersections OK')"
  </verify>
  <done>
    - lib/urban/road_geometry.py exists with RoadGeometryBuilder class
    - lib/urban/intersections.py exists with IntersectionBuilder class
    - RoadGeometryBuilder.build_from_network() creates Blender objects
    - GN node group creation framework in place
    - Intersection types: 4-way, 3-way, roundabout supported
  </done>
</task>

<task type="auto">
  <name>Task 3: Implement MUTCD Street Sign Library</name>
  <files>
    lib/urban/signage.py
    configs/urban/sign_presets.yaml
  </files>
  <action>
    Create street sign system with MUTCD standard dimensions.

    **1. Create lib/urban/signage.py:**
    ```python
    """Street Sign System with MUTCD Standard Dimensions.

    MUTCD = Manual on Uniform Traffic Control Devices
    https://mutcd.fhwa.dot.gov/

    All dimensions in millimeters per MUTCD standards.
    """

    # MUTCD Standard Sign Dimensions (mm)
    SIGN_DIMENSIONS = {
        # Regulatory Signs
        "stop": {
            "shape": "octagon",
            "width": 750,  # 30" standard
            "height": 750,
            "color": [0.694, 0.098, 0.098],  # Highway red
            "border_color": [1.0, 1.0, 1.0],
            "text": "STOP",
            "text_color": [1.0, 1.0, 1.0],
        },
        "yield": {
            "shape": "triangle_down",
            "width": 750,
            "height": 750,  # Equilateral triangle
            "color": [1.0, 1.0, 1.0],
            "border_color": [0.694, 0.098, 0.098],
            "text": "YIELD",
            "text_color": [0.694, 0.098, 0.098],
        },
        "speed_limit": {
            "shape": "rectangle",
            "width": 600,
            "height": 750,
            "color": [1.0, 1.0, 1.0],
            "border_color": [0.0, 0.0, 0.0],
            "text": "{speed}",  # Variable
            "text_color": [0.0, 0.0, 0.0],
        },
        "do_not_enter": {
            "shape": "circle",
            "width": 750,
            "height": 750,
            "color": [1.0, 1.0, 1.0],
            "border_color": [0.694, 0.098, 0.098],
        },
        "one_way": {
            "shape": "rectangle",
            "width": 900,
            "height": 300,
            "color": [1.0, 1.0, 1.0],
            "border_color": [0.0, 0.0, 0.0],
        },

        # Warning Signs (Diamond)
        "curve_ahead": {
            "shape": "diamond",
            "width": 600,
            "height": 600,
            "color": [1.0, 0.847, 0.0],  # Highway yellow
            "border_color": [0.0, 0.0, 0.0],
        },
        "pedestrian_crossing": {
            "shape": "diamond",
            "width": 600,
            "height": 600,
            "color": [1.0, 0.847, 0.0],
            "border_color": [0.0, 0.0, 0.0],
        },
        "traffic_signal_ahead": {
            "shape": "diamond",
            "width": 600,
            "height": 600,
            "color": [1.0, 0.847, 0.0],
            "border_color": [0.0, 0.0, 0.0],
        },

        # Guide Signs
        "street_name": {
            "shape": "rectangle",
            "width": 1200,  # Variable length
            "height": 225,  # 9" standard height
            "color": [0.098, 0.275, 0.098],  # Highway green
            "border_color": [1.0, 1.0, 1.0],
            "text_color": [1.0, 1.0, 1.0],
        },
        "highway_shield": {
            "shape": "shield",
            "width": 600,
            "height": 600,
            "color": [1.0, 1.0, 1.0],
            "border_color": [0.0, 0.0, 0.0],
        },
    }

    # Sign pole standards
    POLE_DIMENSIONS = {
        "standard": {
            "diameter": 50,  # mm (2")
            "height": 2500,  # mm
            "material": "galvanized_steel",
        },
        "large": {
            "diameter": 75,  # mm (3")
            "height": 3000,  # mm
            "material": "galvanized_steel",
        },
    }

    @dataclass
    class SignConfig:
        sign_type: str
        text: str = ""
        speed_value: int = None  # For speed limit signs
        street_name: str = ""  # For street name signs
        height_offset: float = 2.0  # meters from ground
        rotation: float = 0.0  # Degrees
        pole_type: str = "standard"

    class SignGenerator:
        """Procedural street sign generator."""

        def create_sign(self, config: SignConfig, position: Tuple[float, float, float]) -> Optional[bpy.types.Object]:
            """Create a street sign at the specified position."""
            if config.sign_type not in SIGN_DIMENSIONS:
                raise ValueError(f"Unknown sign type: {config.sign_type}")

            dims = SIGN_DIMENSIONS[config.sign_type]
            pole_dims = POLE_DIMENSIONS[config.pole_type]

            # Convert mm to meters
            scale = 0.001

            # Create sign collection
            collection = bpy.data.collections.new(f"Sign_{config.sign_type}")
            bpy.context.collection.children.link(collection)

            # Create pole
            pole = self._create_pole(position, pole_dims)
            collection.objects.link(pole)

            # Create sign face
            sign_face = self._create_sign_face(
                position=(position[0], position[1], position[2] + config.height_offset),
                dims=dims,
                config=config
            )
            sign_face.parent = pole
            collection.objects.link(sign_face)

            return collection

        def _create_pole(self, position: Tuple, dims: Dict) -> bpy.types.Object:
            """Create sign pole."""
            # Cylinder for pole
            pass

        def _create_sign_face(self, position: Tuple, dims: Dict, config: SignConfig) -> bpy.types.Object:
            """Create sign face mesh."""
            shape = dims["shape"]

            if shape == "octagon":
                return self._create_octagon(position, dims)
            elif shape == "triangle_down":
                return self._create_triangle(position, dims)
            elif shape == "rectangle":
                return self._create_rectangle(position, dims, config)
            elif shape == "diamond":
                return self._create_diamond(position, dims)
            elif shape == "circle":
                return self._create_circle(position, dims)
            elif shape == "shield":
                return self._create_shield(position, dims)

        def _create_octagon(self, position, dims) -> bpy.types.Object:
            """Create octagonal sign (STOP sign)."""
            # Create with 8 vertices
            pass

        def _create_rectangle(self, position, dims, config) -> bpy.types.Object:
            """Create rectangular sign (speed limit, street name)."""
            # Handle variable text for speed/street name
            pass

        def batch_create(self, sign_configs: List[Tuple[SignConfig, Tuple]]) -> List[bpy.types.Object]:
            """Create multiple signs efficiently."""
            return [self.create_sign(cfg, pos) for cfg, pos in sign_configs]
    ```

    **2. Create configs/urban/sign_presets.yaml:**
    ```yaml
    # Street sign presets organized by category

    regulatory:
      stop:
        sign_type: stop
        height_offset: 2.0

      yield:
        sign_type: yield
        height_offset: 2.0

      speed_25:
        sign_type: speed_limit
        speed_value: 25
        height_offset: 2.0

      speed_35:
        sign_type: speed_limit
        speed_value: 35
        height_offset: 2.0

      speed_45:
        sign_type: speed_limit
        speed_value: 45
        height_offset: 2.0

    warning:
      curve_left:
        sign_type: curve_ahead
        direction: left
        height_offset: 2.0

      pedestrian:
        sign_type: pedestrian_crossing
        height_offset: 2.0

    guide:
      street_name:
        sign_type: street_name
        height_offset: 3.0  # Higher for visibility
        pole_type: large

      highway_interstate:
        sign_type: highway_shield
        style: interstate
        height_offset: 3.0

    # Common sign combinations
    sign_groups:
      intersection_standard:
        - stop
        - street_name
        - speed_limit_25

      school_zone:
        - speed_limit_15
        - pedestrian_crossing
        - school_ahead
    ```

    Reference lib/animation/city/street_elements.py SignGenerator for existing patterns.
  </action>
  <verify>
    python -c "from lib.urban.signage import SIGN_DIMENSIONS, SignGenerator, SignConfig; print('Signage OK')"
    python -c "from lib.urban.signage import SIGN_DIMENSIONS; assert SIGN_DIMENSIONS['stop']['width'] == 750; print('MUTCD dims OK')"
    ls -la configs/urban/sign_presets.yaml
  </verify>
  <done>
    - lib/urban/signage.py exists with SIGN_DIMENSIONS dict
    - lib/urban/signage.py exists with SignGenerator class
    - configs/urban/sign_presets.yaml exists with presets
    - Stop sign: 750mm octagon
    - Speed limit: 600x750mm rectangle
    - Yield: 750x600x750mm triangle (equilateral)
    - All MUTCD standard dimensions implemented
  </done>
</task>

<task type="auto">
  <name>Task 4: Implement Street Lighting and Urban Furniture</name>
  <files>
    lib/urban/lighting.py
    lib/urban/furniture.py
    configs/urban/furniture_presets.yaml
  </files>
  <action>
    Create street lighting and urban furniture systems.

    **1. Create lib/urban/lighting.py:**
    ```python
    """Street Lighting System.

    Supports multiple lamp styles with procedural generation
    and intelligent placement along roads.
    """

    @dataclass
    class LampConfig:
        lamp_type: LampType
        pole_height: float = 8.0  # meters
        pole_diameter: float = 0.25  # meters
        arm_length: float = 2.0  # meters
        fixture_size: float = 0.6  # meters
        light_power: float = 1000.0  # Watts
        light_color: Tuple[float, float, float] = (1.0, 0.95, 0.85)  # Warm white
        color_temperature: int = 3000  # Kelvin (LED: 4000, HPS: 2000)

    # Lamp presets
    LAMP_PRESETS = {
        "modern": LampConfig(
            lamp_type=LampType.MODERN,
            pole_height=10.0,
            arm_length=3.0,
            light_power=1500.0,
            color_temperature=4000,
        ),
        "traditional": LampConfig(
            lamp_type=LampType.TRADITIONAL,
            pole_height=7.0,
            arm_length=1.5,
            light_power=800.0,
            color_temperature=2700,
        ),
        "highway": LampConfig(
            lamp_type=LampType.HIGHWAY,
            pole_height=15.0,
            arm_length=4.0,
            fixture_size=1.0,
            light_power=2000.0,
            color_temperature=4000,
        ),
        "ornate": LampConfig(
            lamp_type=LampType.ORNATE,
            pole_height=6.0,
            arm_length=0.5,
            light_power=600.0,
            color_temperature=2200,
        ),
    }

    class StreetLightSystem:
        """Procedural street light generator with road-aware placement."""

        def create_lamp(self, position: Tuple[float, float, float],
                       config: LampConfig, name: str = "StreetLight") -> Optional[bpy.types.Object]:
            """Create a single street light."""
            # Create pole (cylinder)
            # Create arm (cylinder, rotated)
            # Create fixture (box or custom mesh)
            # Create point light
            pass

        def place_along_road(self, road_network: RoadNetwork,
                             spacing: float = 25.0,
                             offset: float = 3.0,
                             side: str = "both") -> List[bpy.types.Object]:
            """Place street lights along road segments.

            Args:
                road_network: Road network to place lights along
                spacing: Distance between lights in meters
                offset: Lateral offset from road edge
                side: "left", "right", or "both"
            """
            lamps = []

            for segment in road_network.segments.values():
                segment_length = self._segment_length(segment)
                num_lights = int(segment_length / spacing)

                for i in range(num_lights):
                    t = i / num_lights
                    pos = self._interpolate_position(segment, t)

                    # Add lateral offset
                    if side in ["right", "both"]:
                        lamp = self.create_lamp(
                            self._offset_position(pos, segment, offset),
                            LAMP_PRESETS["modern"]
                        )
                        lamps.append(lamp)

                    if side in ["left", "both"]:
                        lamp = self.create_lamp(
                            self._offset_position(pos, segment, -offset),
                            LAMP_PRESETS["modern"]
                        )
                        lamps.append(lamp)

            return lamps

        def _segment_length(self, segment: RoadSegment) -> float:
            """Calculate segment length."""
            dx = segment.end[0] - segment.start[0]
            dy = segment.end[1] - segment.start[1]
            return math.sqrt(dx*dx + dy*dy)

        def _interpolate_position(self, segment: RoadSegment, t: float) -> Tuple:
            """Interpolate position along segment."""
            return (
                segment.start[0] + t * (segment.end[0] - segment.start[0]),
                segment.start[1] + t * (segment.end[1] - segment.start[1]),
                segment.start[2] + t * (segment.end[2] - segment.start[2]),
            )
    ```

    **2. Create lib/urban/furniture.py:**
    ```python
    """Urban Furniture System.

    Benches, bollards, trash cans, bus stops, etc.
    """

    @dataclass
    class FurnitureConfig:
        furniture_type: FurnitureType
        style: str = "standard"  # standard, modern, victorian, industrial
        material: str = "metal"
        color: Tuple[float, float, float] = (0.3, 0.3, 0.3)

    FURNITURE_DIMENSIONS = {
        "bench": {
            "length": 1.8,  # meters
            "depth": 0.6,
            "height": 0.8,
            "seat_height": 0.45,
        },
        "bollard": {
            "diameter": 0.15,
            "height": 0.9,
        },
        "trash_can": {
            "diameter": 0.5,
            "height": 1.0,
        },
        "bus_stop_shelter": {
            "width": 3.0,
            "depth": 1.5,
            "height": 2.5,
        },
        "fire_hydrant": {
            "diameter": 0.2,
            "height": 0.75,
        },
        "mail_box": {
            "width": 0.6,
            "depth": 0.5,
            "height": 1.2,
        },
    }

    class FurnitureGenerator:
        """Procedural urban furniture generator."""

        def create_bench(self, config: FurnitureConfig, position: Tuple,
                        rotation: float = 0.0) -> bpy.types.Object:
            """Create bench geometry."""
            dims = FURNITURE_DIMENSIONS["bench"]
            # Create seat (box)
            # Create back (box, angled)
            # Create legs (cylinders)
            pass

        def create_bollard(self, config: FurnitureConfig, position: Tuple) -> bpy.types.Object:
            """Create bollard geometry."""
            dims = FURNITURE_DIMENSIONS["bollard"]
            # Create cylinder with dome top
            pass

        def create_trash_can(self, config: FurnitureConfig, position: Tuple) -> bpy.types.Object:
            """Create trash can geometry."""
            dims = FURNITURE_DIMENSIONS["trash_can"]
            # Create cylinder with lid
            pass

        def place_furniture(self, road_network: RoadNetwork,
                           furniture_type: FurnitureType,
                           spacing: float = 50.0,
                           side: str = "right") -> List[bpy.types.Object]:
            """Place furniture along road network."""
            pass

        def populate_sidewalk(self, segment: RoadSegment,
                             density: float = 0.3) -> List[bpy.types.Object]:
            """Populate sidewalk along segment with random furniture.

            Density affects probability of furniture placement.
            """
            pass
    ```

    **3. Create configs/urban/furniture_presets.yaml:**
    ```yaml
    # Urban furniture presets

    benches:
      standard:
        style: standard
        material: metal
        color: [0.2, 0.2, 0.2]

      park:
        style: victorian
        material: wood_metal
        color: [0.4, 0.3, 0.2]

      modern:
        style: modern
        material: steel
        color: [0.7, 0.7, 0.7]

    bollards:
      standard:
        style: standard
        color: [0.2, 0.2, 0.2]

      decorative:
        style: victorian
        color: [0.1, 0.1, 0.1]

      removable:
        style: modern
        removable: true

    trash_cans:
      standard:
        color: [0.1, 0.1, 0.1]

      recycling:
        color: [0.0, 0.5, 0.0]

    bus_stops:
      standard_shelter:
        has_roof: true
        has_bench: true
        has_schedule: true

      minimal:
        has_roof: false
        has_bench: true
        has_schedule: false

    # Placement presets
    placement:
      downtown:
        bench_spacing: 30
        trash_can_spacing: 50
        bollard_spacing: 5

      residential:
        bench_spacing: 100
        trash_can_spacing: 200

      commercial:
        bench_spacing: 20
        trash_can_spacing: 30
        bollard_spacing: 3
    ```

    Reference lib/animation/city/street_elements.py StreetLightSystem for existing patterns.
  </action>
  <verify>
    python -c "from lib.urban.lighting import StreetLightSystem, LAMP_PRESETS; print('Lighting OK')"
    python -c "from lib.urban.furniture import FurnitureGenerator, FURNITURE_DIMENSIONS; print('Furniture OK')"
    ls -la configs/urban/furniture_presets.yaml
  </verify>
  <done>
    - lib/urban/lighting.py exists with StreetLightSystem class
    - lib/urban/lighting.py has LAMP_PRESETS (modern, traditional, highway, ornate)
    - lib/urban/furniture.py exists with FurnitureGenerator class
    - lib/urban/furniture.py has FURNITURE_DIMENSIONS dict
    - configs/urban/furniture_presets.yaml exists
    - Street lights can be placed along roads with spacing
    - Urban furniture dimensions are realistic (bench 1.8m, bollard 0.9m)
  </done>
</task>

<task type="auto">
  <name>Task 5: Implement Pavement Materials and Road Markings</name>
  <files>
    lib/urban/markings.py
    lib/urban/materials.py
    configs/urban/material_presets.yaml
  </files>
  <action>
    Create pavement materials and road marking systems.

    **1. Create lib/urban/markings.py:**
    ```python
    """Crosswalk and Road Marking System.

    Generates procedural road markings with standard dimensions.
    """

    @dataclass
    class MarkingConfig:
        marking_type: MarkingType
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0)  # White default
        width: float = 0.15  # Line width in meters
        dash_length: float = 3.0  # For dashed lines
        gap_length: float = 1.5  # Gap between dashes
        reflectivity: float = 0.8

    # Standard marking dimensions (meters)
    MARKING_DIMENSIONS = {
        "lane_line": {
            "width": 0.1,
            "dash_length": 3.0,
            "gap_length": 9.0,
        },
        "center_line": {
            "width": 0.15,
            "type": "double_yellow",
        },
        "edge_line": {
            "width": 0.15,
            "type": "solid",
        },
        "crosswalk": {
            "stripe_width": 0.4,
            "stripe_gap": 0.4,
            "stripe_length": 3.0,  # Crosswalk width
        },
        "stop_line": {
            "width": 0.6,
            "type": "solid",
        },
        "turn_arrow": {
            "width": 0.3,
            "length": 3.0,
        },
    }

    class MarkingGenerator:
        """Procedural road marking generator."""

        def create_center_line(self, segment: RoadSegment,
                              config: MarkingConfig = None) -> bpy.types.Object:
            """Create center line marking (double yellow for 2-way)."""
            pass

        def create_lane_lines(self, segment: RoadSegment,
                             lanes: int = 2) -> List[bpy.types.Object]:
            """Create dashed lane divider lines."""
            pass

        def create_crosswalk(self, position: Tuple[float, float, float],
                            width: float = 6.0,
                            direction: float = 0.0,
                            style: str = "zebra") -> bpy.types.Object:
            """Create crosswalk (zebra stripes).

            Args:
                position: Center position of crosswalk
                width: Total width (across road)
                direction: Rotation in degrees
                style: "zebra" (stripes) or "continental" (blocks)
            """
            dims = MARKING_DIMENSIONS["crosswalk"]

            # Calculate stripe positions
            stripe_count = int(width / (dims["stripe_width"] + dims["stripe_gap"]))
            stripe_positions = []

            for i in range(stripe_count):
                offset = i * (dims["stripe_width"] + dims["stripe_gap"])
                stripe_positions.append(offset - width / 2)

            # Create stripe geometry
            # ...
            pass

        def create_stop_line(self, position: Tuple, width: float = 3.5,
                            rotation: float = 0.0) -> bpy.types.Object:
            """Create stop line at intersection approach."""
            pass

        def create_turn_arrows(self, position: Tuple, arrow_type: str = "straight") -> bpy.types.Object:
            """Create turn lane arrows (straight, left, right, combined)."""
            pass

        def generate_segment_markings(self, segment: RoadSegment) -> List[bpy.types.Object]:
            """Generate all markings for a road segment."""
            markings = []

            # Center line
            markings.append(self.create_center_line(segment))

            # Lane lines
            total_lanes = segment.lanes_forward + segment.lanes_backward
            markings.extend(self.create_lane_lines(segment, total_lanes))

            return markings
    ```

    **2. Create lib/urban/materials.py:**
    ```python
    """Pavement Material System.

    Procedural materials for road surfaces, sidewalks, etc.
    """

    @dataclass
    class PavementConfig:
        name: str
        base_color: Tuple[float, float, float]
        roughness: float = 0.8
        bump_strength: float = 0.5
        crack_density: float = 0.3
        wear_level: float = 0.5  # 0 = new, 1 = worn

    PAVEMENT_PRESETS = {
        "asphalt_new": PavementConfig(
            name="Asphalt (New)",
            base_color=(0.12, 0.12, 0.12),
            roughness=0.7,
            bump_strength=0.2,
            crack_density=0.0,
            wear_level=0.0,
        ),
        "asphalt_worn": PavementConfig(
            name="Asphalt (Worn)",
            base_color=(0.18, 0.18, 0.18),
            roughness=0.85,
            bump_strength=0.6,
            crack_density=0.4,
            wear_level=0.7,
        ),
        "concrete": PavementConfig(
            name="Concrete",
            base_color=(0.5, 0.5, 0.5),
            roughness=0.6,
            bump_strength=0.3,
            crack_density=0.2,
        ),
        "brick": PavementConfig(
            name="Brick Pavers",
            base_color=(0.6, 0.3, 0.2),
            roughness=0.75,
            bump_strength=0.8,
        ),
        "cobblestone": PavementConfig(
            name="Cobblestone",
            base_color=(0.35, 0.3, 0.25),
            roughness=0.8,
            bump_strength=1.0,
        ),
    }

    class PavementMaterialGenerator:
        """Procedural pavement material generator."""

        def create_asphalt_material(self, config: PavementConfig) -> bpy.types.Material:
            """Create asphalt material with procedural texturing."""
            mat = bpy.data.materials.new(config.name)
            mat.use_nodes = True

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Get principled BSDF
            bsdf = nodes.get("Principled BSDF")

            # Set base color
            bsdf.inputs["Base Color"].default_value = (*config.base_color, 1.0)
            bsdf.inputs["Roughness"].default_value = config.roughness

            # Add noise texture for asphalt grain
            noise = nodes.new("ShaderNodeTexNoise")
            noise.inputs["Scale"].default_value = 100
            noise.inputs["Detail"].default_value = 10

            # Connect to bump
            bump = nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = config.bump_strength

            # Connect nodes
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

            return mat

        def create_concrete_material(self, config: PavementConfig) -> bpy.types.Material:
            """Create concrete material with control joints."""
            pass

        def create_brick_material(self, config: PavementConfig) -> bpy.types.Material:
            """Create brick paver material with brick pattern."""
            pass

        def apply_to_object(self, obj: bpy.types.Object, config: PavementConfig) -> None:
            """Apply pavement material to object."""
            mat = self.create_asphalt_material(config)
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)
    ```

    **3. Create configs/urban/material_presets.yaml:**
    ```yaml
    # Pavement material presets

    asphalt:
      new:
        base_color: [0.12, 0.12, 0.12]
        roughness: 0.7
        bump_strength: 0.2

      worn:
        base_color: [0.18, 0.18, 0.18]
        roughness: 0.85
        bump_strength: 0.6
        crack_density: 0.4

      patched:
        base_color: [0.15, 0.15, 0.15]
        roughness: 0.8
        patch_density: 0.3

    concrete:
      standard:
        base_color: [0.5, 0.5, 0.5]
        roughness: 0.6

      aged:
        base_color: [0.45, 0.45, 0.42]
        roughness: 0.75
        stain_density: 0.3

    pavers:
      brick_red:
        base_color: [0.6, 0.3, 0.2]
        roughness: 0.75

      brick_grey:
        base_color: [0.4, 0.4, 0.4]
        roughness: 0.75

      cobblestone:
        base_color: [0.35, 0.3, 0.25]
        roughness: 0.8
        bump_strength: 1.0

    sidewalks:
      standard:
        material: concrete
        joint_spacing: 1.5

      decorative:
        material: brick_grey
        pattern: herringbone
    ```
  </action>
  <verify>
    python -c "from lib.urban.markings import MarkingGenerator, MARKING_DIMENSIONS; print('Markings OK')"
    python -c "from lib.urban.materials import PavementMaterialGenerator, PAVEMENT_PRESETS; print('Materials OK')"
    ls -la configs/urban/material_presets.yaml
  </verify>
  <done>
    - lib/urban/markings.py exists with MarkingGenerator class
    - lib/urban/markings.py has MARKING_DIMENSIONS dict
    - lib/urban/materials.py exists with PavementMaterialGenerator class
    - lib/urban/materials.py has PAVEMENT_PRESETS dict
    - configs/urban/material_presets.yaml exists
    - Crosswalk stripe dimensions: 0.4m width, 0.4m gap
    - Lane line: 0.1m width, 3m dash, 9m gap
    - Asphalt, concrete, brick, cobblestone materials
  </done>
</task>

</tasks>

<verification>
## Phase Verification

After all plans complete, verify:

1. **Module Structure**
   - All 8 modules exist in lib/urban/
   - __init__.py exports all public classes
   - configs/urban/ has all YAML presets

2. **L-System Road Generation (Python)**
   - LSystemRoads generates valid L-strings
   - parse_to_network() creates RoadNetwork with segments
   - JSON export produces valid JSON file

3. **Road Geometry (GN)**
   - RoadGeometryBuilder creates Blender objects from RoadNetwork
   - GN node groups framework in place

4. **Intersections**
   - 4-way, 3-way, roundabout types supported
   - IntersectionBuilder creates geometry

5. **MUTCD Signs**
   - Stop sign: 750mm octagon (verified)
   - Speed limit: 600x750mm rectangle (verified)
   - Yield: 750x600x750mm triangle (verified)

6. **Street Lighting**
   - LAMP_PRESETS has modern, traditional, highway, ornate
   - StreetLightSystem places lights along roads

7. **Urban Furniture**
   - FURNITURE_DIMENSIONS has bench, bollard, trash_can, etc.
   - FurnitureGenerator creates furniture objects

8. **Road Markings**
   - MARKING_DIMENSIONS has standard dimensions
   - MarkingGenerator creates crosswalks, lane lines

9. **Pavement Materials**
   - PAVEMENT_PRESETS has asphalt, concrete, brick, cobblestone
   - PavementMaterialGenerator creates materials
</verification>

<success_criteria>
Phase 4 is complete when:

1. [ ] lib/urban/ package exists with 8 modules
2. [ ] L-system road generation produces JSON road networks
3. [ ] GN road geometry builder consumes JSON
4. [ ] Intersections: 4-way, 3-way, roundabout implemented
5. [ ] MUTCD signs with correct dimensions
6. [ ] Street lighting system with 4+ presets
7. [ ] Urban furniture with standard dimensions
8. [ ] Road markings (crosswalk, lane lines, stop lines)
9. [ ] Pavement materials (asphalt, concrete, brick, cobblestone)
10. [ ] All YAML presets created
11. [ ] Unit tests passing
</success_criteria>

<output>
After completion, create `.planning/phases/04-urban-infrastructure/04-01-SUMMARY.md`
</output>
