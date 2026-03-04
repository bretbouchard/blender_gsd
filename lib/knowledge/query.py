"""
Knowledge Base Query System - Search and retrieve patterns from accumulated knowledge.

This module provides fast access to the Blender knowledge base without needing
to read entire documentation files.

Usage:
    from lib.knowledge.query import KnowledgeQuery

    # Search for relevant patterns
    kb = KnowledgeQuery()
    results = kb.search("curl noise particles")

    # Get a specific pattern
    pattern = kb.get_pattern("sdf_workflow")

    # List all available patterns
    patterns = kb.list_patterns()
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

# Optional YAML support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class KnowledgeResult:
    """A single search result from the knowledge base."""
    file: str
    section: str
    title: str
    content: str
    relevance: float
    keywords: List[str] = field(default_factory=list)
    code_example: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "section": self.section,
            "title": self.title,
            "content": self.content,
            "relevance": self.relevance,
            "keywords": self.keywords,
            "code_example": self.code_example
        }


@dataclass
class Pattern:
    """A reusable pattern from the knowledge base."""
    name: str
    description: str
    category: str
    nodes: List[str]
    workflow: str
    code_example: Optional[str] = None
    source_file: str = ""
    source_section: str = ""
    blender_version: str = "5.0"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "nodes": self.nodes,
            "workflow": self.workflow,
            "code_example": self.code_example,
            "source_file": self.source_file,
            "source_section": self.source_section,
            "blender_version": self.blender_version,
            "tags": self.tags
        }


class KnowledgeQuery:
    """
    Query the Blender knowledge base for relevant patterns and information.

    The knowledge base includes:
    - GEOMETRY_NODES_KNOWLEDGE.md (13 CGMatter tutorials)
    - BLENDER_51_TUTORIAL_KNOWLEDGE.md (38 advanced tutorials)
    - BLENDER_50_ARRAY_MODIFIER_KNOWLEDGE.md
    - BLENDER_50_KNOWLEDGE_SYNTHESIS.md (compiled 5.0 features)
    """

    # Knowledge base files relative to docs/
    KNOWLEDGE_FILES = [
        "GEOMETRY_NODES_KNOWLEDGE.md",
        "BLENDER_51_TUTORIAL_KNOWLEDGE.md",
        "BLENDER_50_ARRAY_MODIFIER_KNOWLEDGE.md",
        "BLENDER_50_KNOWLEDGE_SYNTHESIS.md",
    ]

    # Pre-indexed patterns for fast lookup
    PATTERNS: Dict[str, Pattern] = {}

    def __init__(self, docs_path: Optional[str] = None):
        """
        Initialize the knowledge query system.

        Args:
            docs_path: Path to docs directory. Auto-detected if not provided.
        """
        if docs_path:
            self.docs_path = Path(docs_path)
        else:
            # Auto-detect docs path
            self.docs_path = self._find_docs_path()

        self._cache: Dict[str, List[KnowledgeResult]] = {}
        self._loaded_files: Dict[str, str] = {}
        self._initialize_patterns()

    def _find_docs_path(self) -> Path:
        """Find the docs directory."""
        # Try common locations
        candidates = [
            Path(__file__).parent.parent.parent / "docs",
            Path.cwd() / "docs",
            Path(__file__).parent / "docs",
        ]

        for path in candidates:
            if path.exists():
                return path

        # Fallback to relative path
        return Path(__file__).parent.parent.parent / "docs"

    def _initialize_patterns(self) -> None:
        """Initialize pre-defined patterns from knowledge synthesis and YAML index."""
        # Start with hardcoded patterns
        self.PATTERNS = {
            # === VOLUME GRIDS ===
            "sdf_workflow": Pattern(
                name="sdf_workflow",
                description="Signed Distance Field workflow for procedural volume work",
                category="volume",
                nodes=["Mesh to SDF", "Points to SDF Grid", "Grid Dilate", "Grid Erode", "Grid Blur", "Grid to Mesh"],
                workflow="Mesh/Points → Points to SDF Grid / Mesh to SDF → Process (Dilate/Erode/Blur) → Grid to Mesh",
                code_example="""
# SDF Workflow Pattern
mesh = bpy.data.objects["Cube"]
# Create SDF from mesh
sdf_node = nodes.new("GeometryNodeMeshToSDF")
# Process with dilate
dilate = nodes.new("GeometryNodeGridDilate")
# Convert back to mesh
grid_to_mesh = nodes.new("GeometryNodeGridToMesh")
""",
                source_file="BLENDER_50_KNOWLEDGE_SYNTHESIS.md",
                source_section="Volume Grid System",
                blender_version="5.0",
                tags=["volume", "sdf", "grid", "mesh", "procedural"]
            ),

            # === CURL NOISE ===
            "curl_noise": Pattern(
                name="curl_noise",
                description="Divergence-free particle motion using curl of vector field",
                category="particles",
                nodes=["Noise Texture", "Math (Derivative)", "Set Position", "Simulation Zone", "Repeat Zone"],
                workflow="Grid of Points → Simulation Zone → Repeat Zone (substeps) → Curl Field × Delta Time → Set Position",
                code_example="""
# Curl Noise Calculation
epsilon = 0.001
dVz_dX = (Vz(position + epsilon_x) - Vz(position)) / epsilon
dVz_dY = (Vz(position + epsilon_y) - Vz(position)) / epsilon
curl_x = dVz_dY
curl_y = -dVz_dX
""",
                source_file="GEOMETRY_NODES_KNOWLEDGE.md",
                source_section="7. Curl Noise Particles",
                blender_version="4.0+",
                tags=["particles", "noise", "simulation", "divergence-free", "curl"]
            ),

            # === BUNDLES ===
            "material_bundle": Pattern(
                name="material_bundle",
                description="Package material settings into a reusable bundle",
                category="bundles",
                nodes=["Store Bundle Item", "Get Bundle Item", "Bundle Info"],
                workflow="Create Bundle → Store Base Color, Roughness, Metallic → Pass through nodes → Unpack where needed",
                code_example="""
# Material Bundle Pattern
bundle = {}
bundle["base_color"] = (0.8, 0.2, 0.1, 1.0)
bundle["roughness"] = 0.4
bundle["metallic"] = 0.8
# Pass bundle through processing nodes
# Unpack at final geometry
""",
                source_file="BLENDER_50_KNOWLEDGE_SYNTHESIS.md",
                source_section="Closures & Bundles Deep Dive",
                blender_version="5.0",
                tags=["bundle", "material", "data", "pass-through"]
            ),

            "physics_bundle": Pattern(
                name="physics_bundle",
                description="Declarative physics configuration using bundles",
                category="physics",
                nodes=["Store Bundle Item", "Get Bundle Item", "Simulation Zone"],
                workflow="Physics Bundle (gravity, damping, collisions) → Simulation Zone → Solver → Updated Geometry",
                code_example="""
# Physics Bundle
physics = {
    "gravity": (0, 0, -9.8),
    "damping": 0.98,
    "wind": (0.5, 0, 0),
    "collisions": ["GroundPlane"]
}
# Pass to simulation zone
""",
                source_file="BLENDER_50_KNOWLEDGE_SYNTHESIS.md",
                source_section="Physics Bundles & XPBD Solver",
                blender_version="5.0",
                tags=["physics", "bundle", "simulation", "particles"]
            ),

            # === CLOSURES ===
            "randomize_transform_closure": Pattern(
                name="randomize_transform_closure",
                description="Reusable closure for random instance transforms",
                category="closures",
                nodes=["Closure", "Invoke Closure", "Random Value", "Rotate Instances", "Scale Instances"],
                workflow="Define Closure (Random Rotation, Random Scale) → Invoke on instances with different seeds",
                code_example="""
# Closure: RandomizeInstance
def randomize_transform(rotation_range=(-360, 360), scale_range=(0.8, 1.2)):
    rotation = random_value(rotation_range[0], rotation_range[1])
    scale = random_value(scale_range[0], scale_range[1])
    return rotation, scale
""",
                source_file="BLENDER_50_KNOWLEDGE_SYNTHESIS.md",
                source_section="Closures & Bundles Deep Dive",
                blender_version="5.0",
                tags=["closure", "randomize", "transform", "instances"]
            ),

            # === INSTANCE PATTERNS ===
            "height_based_scale": Pattern(
                name="height_based_scale",
                description="Scale instances based on Z position (smaller at top)",
                category="instances",
                nodes=["Position", "Separate XYZ", "Math (Multiply Add)", "Scale Instances"],
                workflow="Position → Separate XYZ → Z → Math (Multiply, -value) → Math (Add, offset) → Scale Instances",
                code_example="""
# Height-based scaling (for plants)
# As Z increases, scale decreases
position = node_input_position()
z = separate_xyz(position).z
scale_factor = multiply_add(z, -2.0, 1.0)  # -2 inverts, +1 base
scale_instances(scale_factor)
""",
                source_file="BLENDER_50_ARRAY_MODIFIER_KNOWLEDGE.md",
                source_section="Key Techniques",
                blender_version="5.0",
                tags=["instances", "scale", "position", "height", "plants"]
            ),

            "curve_aligned_distribution": Pattern(
                name="curve_aligned_distribution",
                description="Distribute instances along a curve with alignment",
                category="instances",
                nodes=["Curve (Path)", "Resample Curve", "Instance on Points", "Align Euler to Vector"],
                workflow="Curve → Resample (count) → Instance on Points (rotation: Align Euler to Vector from Normal)",
                code_example="""
# Curve-aligned distribution
curve = get_curve("Path")
points = resample_curve(curve, count=25)
instances = instance_on_points(
    points=points,
    instance=leaf_mesh,
    rotation=align_euler_to_vector(normal, axis='Y')
)
""",
                source_file="BLENDER_50_ARRAY_MODIFIER_KNOWLEDGE.md",
                source_section="Node Patterns",
                blender_version="5.0",
                tags=["curve", "instances", "alignment", "distribution"]
            ),

            # === SIMULATION ===
            "simulation_zone_pattern": Pattern(
                name="simulation_zone_pattern",
                description="Basic simulation zone structure for state-based updates",
                category="simulation",
                nodes=["Simulation Zone", "Repeat Zone"],
                workflow="Input → Simulation Zone (State Update: position, velocity, etc.) → Output",
                code_example="""
# Simulation Zone Pattern
# Inside simulation zone:
# 1. Read previous state (position, velocity)
# 2. Apply forces (gravity, wind)
# 3. Update velocity
# 4. Update position
# 5. Output new state
""",
                source_file="GEOMETRY_NODES_KNOWLEDGE.md",
                source_section="Quick Reference: Common Patterns",
                blender_version="4.0+",
                tags=["simulation", "state", "physics", "animation"]
            ),

            # === EROSION ===
            "edge_erosion": Pattern(
                name="edge_erosion",
                description="Procedural edge erosion using angle detection",
                category="modeling",
                nodes=["Edge Angle", "Separate Geometry", "Delete Geometry", "Mesh to Curve", "Resample Curve", "Tube Node", "SDF Remesh", "Mesh Boolean"],
                workflow="Mesh → Edge Angle (threshold) → Separate Geometry → Delete faces → Mesh to Curve → Resample → Tube → SDF Remesh → Boolean (difference)",
                code_example="""
# Edge Erosion
threshold = 6  # radians
edges = edge_angle(mesh, threshold)
separated = separate_geometry(edges)
curves = mesh_to_curve(separated)
resampled = resample_curve(curves, 100)
tubes = tube(resampled, radius=noise_control)
eroded = mesh_boolean(mesh, tubes, operation='DIFFERENCE')
""",
                source_file="GEOMETRY_NODES_KNOWLEDGE.md",
                source_section="4. Erosion Systems",
                blender_version="4.0+",
                tags=["erosion", "procedural", "modeling", "edge", "boolean"]
            ),

            "face_erosion": Pattern(
                name="face_erosion",
                description="Procedural face erosion using point distribution",
                category="modeling",
                nodes=["Distribute Points on Faces", "Noise Texture", "Delete Geometry", "Points to SDF", "Grid to Mesh", "Mesh Boolean"],
                workflow="Mesh → Distribute Points → Noise → Delete by threshold → Points to SDF → Grid to Mesh → Boolean (difference) → Delete Floaters",
                code_example="""
# Face Erosion
points = distribute_points_on_faces(mesh, 1500)
noise = noise_texture(points, normalized=False)
filtered = delete_geometry(points, threshold_based)
sdf = points_to_sdf(filtered)
eroded_mesh = grid_to_mesh(sdf)
result = mesh_boolean(mesh, eroded_mesh, operation='DIFFERENCE')
# Remove floaters with island + face area check
""",
                source_file="GEOMETRY_NODES_KNOWLEDGE.md",
                source_section="4. Erosion Systems",
                blender_version="4.0+",
                tags=["erosion", "procedural", "modeling", "face", "points"]
            ),

            # === GEOMETRIC MINIMALISM ===
            "radial_cube_rotation": Pattern(
                name="radial_cube_rotation",
                description="Index-driven rotation for radial cube patterns",
                category="generative",
                nodes=["Curve Circle", "Instance on Points", "Align Rotation to Vector", "Math (Multiply)", "Rotate Instances"],
                workflow="Curve Circle → Instance Cubes → Align Rotation → Index × factor → Rotate Instances",
                code_example="""
# Radial Cube Rotation
circle = curve_circle(radius=7, resolution=80)
instances = instance_on_points(circle, cube)
aligned = align_rotation_to_vector(instances, axis='Y', vector=normal)
# Use Index for rotation pattern
# Index 3 = perfect spiral
# Index 5 = more rotations
rotation = index * factor  # factor determines pattern
rotate_instances(instances, rotation)
""",
                source_file="BLENDER_51_TUTORIAL_KNOWLEDGE.md",
                source_section="2. Geometric Minimalism",
                blender_version="4.0+",
                tags=["generative", "radial", "rotation", "index", "pattern"]
            ),

            # === ANIMATION ===
            "perfect_loop_animation": Pattern(
                name="perfect_loop_animation",
                description="Math for creating perfectly looping animations",
                category="animation",
                nodes=["Scene Time", "Math"],
                workflow="Frame 0: Start value → Frame N: End value (use multiples of 2π for rotation)",
                code_example="""
# Perfect Loop Math
# Method 1: Position
# Frame 0: Z = -5, Frame N: Z = 5

# Method 2: Rotation (use pi)
# Frame 0: 0, Frame N: 2 * pi

# Method 3: Phase offset
# Frame 0: 0, Frame N: N * pi

# Set interpolation to LINEAR for perfect loops
bpy.preferences.edit.keyframe_interpolation = 'LINEAR'
""",
                source_file="BLENDER_51_TUTORIAL_KNOWLEDGE.md",
                source_section="2. Geometric Minimalism",
                blender_version="4.0+",
                tags=["animation", "loop", "seamless", "math"]
            ),

            # === LIGHTING ===
            "studio_lighting_isometric": Pattern(
                name="studio_lighting_isometric",
                description="3-point lighting adapted for isometric views",
                category="lighting",
                nodes=["Light", "World Background"],
                workflow="Key Light (45° from camera, warm) + Fill Light (opposite, cool, 50%) + Rim Light (behind, edge definition)",
                code_example="""
# Isometric 3-Point Lighting
key = create_light(type='SUN', power=3000)
key.location = (5, 5, 10)  # 45° from camera
key.data.color = (1.0, 0.95, 0.9)  # Warm

fill = create_light(type='SUN', power=1500)
fill.location = (-5, -5, 8)
fill.data.color = (0.9, 0.95, 1.0)  # Cool

rim = create_light(type='SUN', power=2000)
rim.location = (0, -8, 5)
rim.data.color = (1.0, 1.0, 1.0)
""",
                source_file="BLENDER_51_TUTORIAL_KNOWLEDGE.md",
                source_section="3.5 Rick and Morty Garage",
                blender_version="4.0+",
                tags=["lighting", "isometric", "studio", "3-point"]
            ),
        }

        # Load additional patterns from YAML index if available
        self._load_yaml_index()

    def _load_yaml_index(self) -> None:
        """Load patterns from YAML index file if available."""
        import logging
        logger = logging.getLogger(__name__)

        if not YAML_AVAILABLE:
            logger.debug("PyYAML not available, skipping YAML index loading")
            return

        yaml_path = self.docs_path / "KNOWLEDGE_INDEX.yaml"
        if not yaml_path.exists():
            logger.debug(f"YAML index not found at {yaml_path}")
            return

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                index = yaml.safe_load(f)

            if not index or 'patterns' not in index:
                logger.warning(f"YAML index at {yaml_path} has no 'patterns' section")
                return

            loaded_count = 0
            for pattern_name, pattern_data in index['patterns'].items():
                # Skip if already defined
                if pattern_name in self.PATTERNS:
                    logger.debug(f"Pattern '{pattern_name}' already defined, skipping YAML version")
                    continue

                # Create Pattern from YAML data
                self.PATTERNS[pattern_name] = Pattern(
                    name=pattern_name,
                    description=pattern_data.get('description', ''),
                    category=pattern_data.get('category', 'general'),
                    nodes=pattern_data.get('nodes', []),
                    workflow=pattern_data.get('workflow', ''),
                    code_example=pattern_data.get('code_example'),
                    source_file=pattern_data.get('file', pattern_data.get('source_file', 'KNOWLEDGE_INDEX.yaml')),
                    source_section=pattern_data.get('section', pattern_data.get('source_section', '')),
                    blender_version=pattern_data.get('blender_version', '5.0'),
                    tags=pattern_data.get('keywords', pattern_data.get('tags', []))
                )
                loaded_count += 1

            logger.info(f"Loaded {loaded_count} patterns from YAML index")

        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse KNOWLEDGE_INDEX.yaml: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading YAML index: {e}")

    def search(
        self,
        query: str,
        max_results: int = 5,
        min_relevance: float = 0.1
    ) -> List[KnowledgeResult]:
        """
        Search the knowledge base for relevant content.

        Args:
            query: Search query (keywords, pattern name, or natural language)
            max_results: Maximum number of results to return
            min_relevance: Minimum relevance score (0-1)

        Returns:
            List of KnowledgeResult sorted by relevance
        """
        query_lower = query.lower()
        query_terms = set(re.findall(r'\w+', query_lower))

        results = []

        # 1. Check patterns first (fastest)
        for name, pattern in self.PATTERNS.items():
            relevance = self._calculate_pattern_relevance(query_terms, pattern)
            if relevance >= min_relevance:
                results.append(KnowledgeResult(
                    file=pattern.source_file,
                    section=pattern.source_section,
                    title=f"Pattern: {pattern.name}",
                    content=self._pattern_to_content(pattern),
                    relevance=relevance,
                    keywords=pattern.tags,
                    code_example=pattern.code_example is not None
                ))

        # 2. Search in knowledge files
        for filename in self.KNOWLEDGE_FILES:
            file_results = self._search_file(filename, query_terms, query_lower)
            results.extend(file_results)

        # Sort by relevance and limit
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:max_results]

    def _calculate_pattern_relevance(self, query_terms: set, pattern: Pattern) -> float:
        """Calculate relevance score for a pattern."""
        # Check name match (highest priority)
        if query_terms.issubset(set(pattern.name.lower().split('_'))):
            return 1.0

        # Check tags
        tag_matches = len(query_terms & set(pattern.tags))
        tag_score = tag_matches / max(len(query_terms), 1)

        # Check description
        desc_terms = set(re.findall(r'\w+', pattern.description.lower()))
        desc_matches = len(query_terms & desc_terms)
        desc_score = desc_matches / max(len(query_terms), 1)

        # Check nodes
        node_matches = sum(1 for term in query_terms
                         if any(term in node.lower() for node in pattern.nodes))
        node_score = node_matches / max(len(query_terms), 1)

        # Weighted combination
        return max(tag_score * 0.5, desc_score * 0.3, node_score * 0.2)

    def _pattern_to_content(self, pattern: Pattern) -> str:
        """Convert pattern to readable content string."""
        lines = [
            f"**{pattern.name}** ({pattern.category})",
            f"{pattern.description}",
            "",
            f"**Nodes:** {', '.join(pattern.nodes)}",
            "",
            f"**Workflow:** {pattern.workflow}",
        ]
        # code_example can be a string, a boolean (from YAML), or None
        if pattern.code_example and isinstance(pattern.code_example, str):
            lines.extend(["", "**Code:**", pattern.code_example])
        return "\n".join(lines)

    def _search_file(
        self,
        filename: str,
        query_terms: set,
        query_lower: str
    ) -> List[KnowledgeResult]:
        """Search within a knowledge file."""
        results = []
        filepath = self.docs_path / filename

        if not filepath.exists():
            return results

        # Load file content
        if filename not in self._loaded_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._loaded_files[filename] = f.read()
            except Exception:
                return results

        content = self._loaded_files[filename]

        # Find sections
        sections = self._extract_sections(content)

        for section_title, section_content in sections:
            section_lower = section_content.lower()
            section_terms = set(re.findall(r'\w+', section_lower))

            # Calculate relevance
            term_matches = len(query_terms & section_terms)
            relevance = term_matches / max(len(query_terms), 1)

            # Boost for exact phrase match
            if query_lower in section_lower:
                relevance = min(1.0, relevance + 0.3)

            # Boost for title match
            if any(term in section_title.lower() for term in query_terms):
                relevance = min(1.0, relevance + 0.2)

            if relevance >= 0.1:
                # Check for code examples
                code_example = '```' in section_content or '    def ' in section_content

                results.append(KnowledgeResult(
                    file=filename,
                    section=section_title,
                    title=section_title,
                    content=self._truncate_content(section_content, 500),
                    relevance=relevance,
                    keywords=list(query_terms & section_terms)[:10],
                    code_example=code_example
                ))

        return results

    def _extract_sections(self, content: str) -> List[Tuple[str, str]]:
        """Extract sections from markdown content."""
        sections = []
        current_title = "Introduction"
        current_content = []

        for line in content.split('\n'):
            if line.startswith('## '):
                if current_content:
                    sections.append((current_title, '\n'.join(current_content)))
                current_title = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        # Add final section
        if current_content:
            sections.append((current_title, '\n'.join(current_content)))

        return sections

    def _truncate_content(self, content: str, max_length: int) -> str:
        """Truncate content to max_length while preserving readability."""
        if len(content) <= max_length:
            return content

        # Find a good break point
        truncated = content[:max_length]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')

        break_point = max(last_period, last_newline)
        if break_point > max_length * 0.7:
            truncated = truncated[:break_point + 1]

        return truncated + "\n... (truncated)"

    def get_pattern(self, name: str) -> Optional[Pattern]:
        """
        Get a specific pattern by name.

        Args:
            name: Pattern name (e.g., "sdf_workflow", "curl_noise")

        Returns:
            Pattern if found, None otherwise
        """
        # Normalize name
        name_normalized = name.lower().replace(' ', '_').replace('-', '_')

        # Direct lookup
        if name_normalized in self.PATTERNS:
            return self.PATTERNS[name_normalized]

        # Fuzzy search
        for pattern_name, pattern in self.PATTERNS.items():
            if name_normalized in pattern_name or pattern_name in name_normalized:
                return pattern

        return None

    def list_patterns(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        """
        List all available patterns.

        Args:
            category: Filter by category (volume, particles, bundles, etc.)

        Returns:
            List of pattern summaries
        """
        patterns = []

        for name, pattern in self.PATTERNS.items():
            if category and pattern.category != category:
                continue

            patterns.append({
                "name": pattern.name,
                "description": pattern.description,
                "category": pattern.category,
                "tags": pattern.tags,
                "blender_version": pattern.blender_version
            })

        return patterns

    def list_categories(self) -> List[str]:
        """List all pattern categories."""
        categories = set()
        for pattern in self.PATTERNS.values():
            categories.add(pattern.category)
        return sorted(list(categories))

    def get_quick_reference(self, topic: str) -> str:
        """
        Get a quick reference card for a topic.

        Args:
            topic: Topic name (sdf, curl, bundle, closure, etc.)

        Returns:
            Formatted quick reference string
        """
        references = {
            "closures": """
╔══════════════════════════════════════╗
║       CLOSURES QUICK REFERENCE       ║
╠══════════════════════════════════════╣
║                                      ║
║  Create Closure:                     ║
║    ├── Define inputs/outputs         ║
║    ├── Build internal logic          ║
║    └── Mark as reusable              ║
║                                      ║
║  Invoke Closure:                     ║
║    ├── Pass inputs                   ║
║    ├── Execute logic                 ║
║    └── Receive outputs               ║
║                                      ║
║  Status: STABLE (Blender 5.0)        ║
╚══════════════════════════════════════╝
""",
            "bundles": """
╔══════════════════════════════════════╗
║       BUNDLES QUICK REFERENCE        ║
╠══════════════════════════════════════╣
║                                      ║
║  Create Bundle:                      ║
║    Store Bundle Item (key, value)    ║
║                                      ║
║  Read Bundle:                        ║
║    Get Bundle Item (bundle, key)     ║
║                                      ║
║  Bundle Contents:                    ║
║    Bundle Info (bundle) → keys       ║
║                                      ║
║  Status: STABLE (Blender 5.0)        ║
╚══════════════════════════════════════╝
""",
            "volume": """
╔══════════════════════════════════════╗
║     VOLUME GRIDS QUICK REFERENCE     ║
╠══════════════════════════════════════╣
║                                      ║
║  Create Grid:                        ║
║    Volume Cube / Points to SDF /     ║
║    Mesh to SDF                       ║
║                                      ║
║  Process Grid:                       ║
║    Grid Dilate / Grid Erode /        ║
║    Grid Blur                         ║
║                                      ║
║  Extract Grid:                       ║
║    Grid to Mesh / Sample Grid /      ║
║    Store Named Grid                  ║
║                                      ║
║  Grid Types:                         ║
║    Density (0 bg) / SDF (-/+) /      ║
║    Velocity / Temperature            ║
╚══════════════════════════════════════╝
""",
            "physics": """
╔══════════════════════════════════════╗
║    PHYSICS BUNDLES QUICK REFERENCE   ║
╠══════════════════════════════════════╣
║                                      ║
║  Define Physics:                     ║
║    Gravity + Damping + Collisions    ║
║                                      ║
║  Apply to Simulation:                ║
║    Physics Bundle → Sim Zone → Solv  ║
║                                      ║
║  XPBD Solver (Hair):                 ║
║    Status: IN DEVELOPMENT            ║
║    Expected: Blender 5.2-5.3         ║
║                                      ║
║  Current Physics:                    ║
║    Particles ✓  Cloth ✓  Soft ✓     ║
║    Rigid Body (traditional)          ║
╚══════════════════════════════════════╝
""",
            "curl": """
╔══════════════════════════════════════╗
║      CURL NOISE QUICK REFERENCE      ║
╠══════════════════════════════════════╣
║                                      ║
║  Why Curl?                           ║
║    Curl of any vector field has      ║
║    ZERO DIVERGENCE                   ║
║    = No sinks, no sources            ║
║                                      ║
║  2D Simplification:                  ║
║    Curl X = dVz/dY                   ║
║    Curl Y = -dVz/dX                  ║
║    Curl Z = 0                        ║
║                                      ║
║  Derivative (finite diff):           ║
║    ε = 0.001                         ║
║    dF/dX = (F(x+ε) - F(x)) / ε       ║
║                                      ║
║  Sources: Noise, Wave, Voronoi, etc. ║
╚══════════════════════════════════════╝
""",
        }

        return references.get(topic.lower(), f"No quick reference for '{topic}'. Available: {list(references.keys())}")


# Convenience functions
def search_knowledge(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Quick search of the knowledge base."""
    kb = KnowledgeQuery()
    results = kb.search(query, max_results)
    return [r.to_dict() for r in results]


def get_pattern(name: str) -> Optional[Dict[str, Any]]:
    """Get a specific pattern by name."""
    kb = KnowledgeQuery()
    pattern = kb.get_pattern(name)
    return pattern.to_dict() if pattern else None


def list_all_patterns(category: Optional[str] = None) -> List[Dict[str, str]]:
    """List all available patterns."""
    kb = KnowledgeQuery()
    return kb.list_patterns(category)


def print_quick_reference(topic: str) -> None:
    """Print a quick reference card."""
    kb = KnowledgeQuery()
    print(kb.get_quick_reference(topic))
