"""
GeoJSON to Blender Building Generator

Imports Charlotte building footprints from GeoJSON and generates 3D buildings
with accurate heights, materials, and LED facade integration.

Usage in Blender:
    import sys
    sys.path.append('/path/to/blender_gsd')

    from lib.charlotte_digital_twin.buildings.geojson_importer import (
        CharlotteBuildingGenerator,
        generate_uptown_charlotte,
    )

    # Generate all Uptown buildings
    generate_uptown_charlotte()

    # Or generate specific buildings
    generator = CharlotteBuildingGenerator()
    generator.load_geojson("charlotte_uptown_buildings.geojson")
    generator.generate_all_buildings()
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import json
import math
import os

try:
    import bpy
    import bmesh
    from bpy.types import Object, Mesh, Collection
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = Any
    Mesh = Any
    Collection = Any
    Vector = Any
    Matrix = Any


# Charlotte coordinate reference point (origin for local coordinates)
# Center of Uptown Charlotte
CHARLOTTE_ORIGIN = {
    "latitude": 35.227,
    "longitude": -80.843,
}

# Scale factor: 1 degree lat ≈ 111km, 1 degree lon at 35°N ≈ 91km
DEGREE_TO_METERS_LAT = 111000.0
DEGREE_TO_METERS_LON = 91000.0  # At Charlotte's latitude


class BuildingMaterialType(Enum):
    """Building material types for shading."""
    GLASS = "glass"
    GRANITE = "granite"
    CONCRETE = "concrete"
    STEEL = "steel"
    BRICK = "brick"
    MIXED = "mixed"


@dataclass
class BuildingFootprint:
    """Represents a single building footprint from GeoJSON."""
    osm_id: int
    name: str
    polygon: List[Tuple[float, float]]  # List of (lon, lat) pairs
    height_m: float
    floors: int
    building_type: str
    material: BuildingMaterialType = BuildingMaterialType.GLASS
    has_led: bool = False
    led_type: str = ""

    # Computed local coordinates
    local_polygon: List[Tuple[float, float]] = field(default_factory=list)
    centroid: Tuple[float, float] = (0.0, 0.0)


class GeoJSONLoader:
    """Loads and parses GeoJSON building data."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            # Default to data directory relative to this file
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        self.data_dir = data_dir

    def load_geojson(self, filename: str) -> Dict[str, Any]:
        """Load GeoJSON file."""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'r') as f:
            return json.load(f)

    def parse_features(self, geojson: Dict) -> List[BuildingFootprint]:
        """Parse GeoJSON features into BuildingFootprint objects."""
        buildings = []

        for feature in geojson.get("features", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})

            if geom.get("type") != "Polygon":
                continue

            # Get polygon coordinates
            coords = geom.get("coordinates", [[]])[0]

            # Parse height
            height = self._parse_height(props.get("height", "0"))

            # Parse floors
            floors = 0
            if props.get("levels"):
                try:
                    floors = int(props["levels"])
                except ValueError:
                    pass

            # Estimate height from floors if not provided
            if height == 0 and floors > 0:
                height = floors * 4.0  # ~4m per floor average

            # Default height for buildings without data
            if height == 0:
                height = 15.0  # Default 3-4 story building

            # Determine material from building type
            material = self._determine_material(props.get("building", "yes"))

            building = BuildingFootprint(
                osm_id=props.get("osm_id", 0),
                name=props.get("name", ""),
                polygon=[(c[0], c[1]) for c in coords],
                height_m=height,
                floors=floors,
                building_type=props.get("building", "yes"),
                material=material,
            )

            buildings.append(building)

        return buildings

    def _parse_height(self, height_str: str) -> float:
        """Parse height string to meters."""
        if not height_str:
            return 0.0

        try:
            height_str = str(height_str).lower().strip()
            if height_str.endswith("m"):
                return float(height_str[:-1])
            elif height_str.endswith("ft"):
                return float(height_str[:-2]) * 0.3048
            else:
                return float(height_str)
        except ValueError:
            return 0.0

    def _determine_material(self, building_type: str) -> BuildingMaterialType:
        """Determine building material from type."""
        material_map = {
            "office": BuildingMaterialType.GLASS,
            "commercial": BuildingMaterialType.GLASS,
            "apartments": BuildingMaterialType.CONCRETE,
            "residential": BuildingMaterialType.BRICK,
            "hotel": BuildingMaterialType.GLASS,
            "retail": BuildingMaterialType.GLASS,
            "warehouse": BuildingMaterialType.CONCRETE,
            "industrial": BuildingMaterialType.STEEL,
        }
        return material_map.get(building_type, BuildingMaterialType.MIXED)


class CoordinateConverter:
    """Converts GPS coordinates to local Blender coordinates."""

    def __init__(self, origin_lat: float = None, origin_lon: float = None):
        self.origin_lat = origin_lat or CHARLOTTE_ORIGIN["latitude"]
        self.origin_lon = origin_lon or CHARLOTTE_ORIGIN["longitude"]

    def to_local(self, lon: float, lat: float) -> Tuple[float, float]:
        """Convert GPS coordinates to local meters from origin."""
        x = (lon - self.origin_lon) * DEGREE_TO_METERS_LON
        y = (lat - self.origin_lat) * DEGREE_TO_METERS_LAT
        return (x, y)

    def polygon_to_local(self, polygon: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Convert entire polygon to local coordinates."""
        return [self.to_local(lon, lat) for lon, lat in polygon]


class CharlotteBuildingGenerator:
    """
    Generates 3D buildings in Blender from Charlotte GeoJSON data.

    Features:
    - Accurate building footprints from OSM
    - Height extrusion from GeoJSON or floor estimation
    - Material assignment based on building type
    - LED building detection and tagging
    - Level of Detail (LOD) support
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.loader = GeoJSONLoader(data_dir)
        self.converter = CoordinateConverter()
        self.buildings: List[BuildingFootprint] = []
        self.collection: Optional[Collection] = None

        # Known LED buildings for special handling
        self.led_buildings = {
            "duke_energy_center",
            "bank_of_america_corporate_center",
            "bank of america corporate center",
            "duke energy center",
            "550 south tryon",
            "truist center",
            "one wells fargo center",
            "fnb tower",
            "honeywell tower",
            "ally charlotte center",
            "carillon tower",
            "nascar hall of fame",
            "200 south tryon",
        }

    def load_geojson(self, filename: str = "charlotte_uptown_buildings.geojson") -> int:
        """
        Load buildings from GeoJSON file.

        Returns:
            Number of buildings loaded
        """
        geojson = self.loader.load_geojson(filename)
        self.buildings = self.loader.parse_features(geojson)

        # Convert coordinates and detect LED buildings
        for building in self.buildings:
            building.local_polygon = self.converter.polygon_to_local(building.polygon)
            building.centroid = self._compute_centroid(building.local_polygon)
            building.has_led = self._is_led_building(building.name)

        return len(self.buildings)

    def _compute_centroid(self, polygon: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Compute centroid of polygon."""
        if not polygon:
            return (0.0, 0.0)
        x_sum = sum(p[0] for p in polygon)
        y_sum = sum(p[1] for p in polygon)
        n = len(polygon)
        return (x_sum / n, y_sum / n)

    def _is_led_building(self, name: str) -> bool:
        """Check if building is a known LED building."""
        name_lower = name.lower().replace("-", " ").replace("_", " ")
        for led_name in self.led_buildings:
            if led_name.replace("_", " ") in name_lower:
                return True
        return False

    def create_collection(self, name: str = "Charlotte Buildings") -> Collection:
        """Create or get collection for buildings."""
        if not BLENDER_AVAILABLE:
            return None

        if name in bpy.data.collections:
            return bpy.data.collections[name]

        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        return collection

    def generate_building_mesh(
        self,
        building: BuildingFootprint,
        name: Optional[str] = None,
    ) -> Optional[Object]:
        """
        Generate a 3D building mesh from footprint.

        Args:
            building: Building footprint data
            name: Optional mesh name

        Returns:
            Created Blender object or None
        """
        if not BLENDER_AVAILABLE:
            return None

        name = name or building.name or f"Building_{building.osm_id}"

        # Create mesh
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        # Link to collection
        if self.collection:
            self.collection.objects.link(obj)
        else:
            bpy.context.collection.objects.link(obj)

        # Create bmesh for geometry
        bm = bmesh.new()

        # Create base face from polygon
        verts = []
        for x, y in building.local_polygon:
            vert = bm.verts.new((x, y, 0.0))
            verts.append(vert)

        # Create face
        if len(verts) >= 3:
            try:
                face = bm.faces.new(verts)
            except ValueError:
                # Face already exists or invalid
                pass

        # Extrude to height
        if building.height_m > 0:
            # Select all faces
            for f in bm.faces:
                f.select = True

            # Extrude
            geom = bmesh.ops.extrude_discrete_faces(bm, faces=bm.faces)

            # Move extruded faces up
            extruded_verts = [v for v in geom['geom'] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(
                bm,
                vec=(0, 0, building.height_m),
                verts=extruded_verts
            )

        # Update mesh
        bm.to_mesh(mesh)
        bm.free()

        # Store building metadata
        obj["osm_id"] = building.osm_id
        obj["building_name"] = building.name
        obj["height_m"] = building.height_m
        obj["floors"] = building.floors
        obj["building_type"] = building.building_type
        obj["has_led"] = building.has_led
        obj["material_type"] = building.material.value

        return obj

    def generate_all_buildings(
        self,
        min_height: float = 0.0,
        min_floors: int = 0,
        named_only: bool = False,
    ) -> List[Object]:
        """
        Generate all loaded buildings.

        Args:
            min_height: Minimum height filter
            min_floors: Minimum floors filter
            named_only: Only generate named buildings

        Returns:
            List of created objects
        """
        if not BLENDER_AVAILABLE:
            return []

        self.collection = self.create_collection()

        objects = []
        for building in self.buildings:
            # Apply filters
            if min_height > 0 and building.height_m < min_height:
                continue
            if min_floors > 0 and building.floors < min_floors:
                continue
            if named_only and not building.name:
                continue

            obj = self.generate_building_mesh(building)
            if obj:
                objects.append(obj)

        return objects

    def generate_led_buildings(self) -> List[Object]:
        """Generate only buildings with LED facades."""
        if not BLENDER_AVAILABLE:
            return []

        self.collection = self.create_collection("Charlotte LED Buildings")

        objects = []
        for building in self.buildings:
            if building.has_led:
                obj = self.generate_building_mesh(building)
                if obj:
                    objects.append(obj)

        return objects

    def get_building_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded buildings."""
        if not self.buildings:
            return {}

        heights = [b.height_m for b in self.buildings]
        floors = [b.floors for b in self.buildings if b.floors > 0]
        led_count = sum(1 for b in self.buildings if b.has_led)
        named_count = sum(1 for b in self.buildings if b.name)

        return {
            "total_buildings": len(self.buildings),
            "named_buildings": named_count,
            "led_buildings": led_count,
            "height": {
                "min": min(heights),
                "max": max(heights),
                "avg": sum(heights) / len(heights),
            },
            "floors": {
                "min": min(floors) if floors else 0,
                "max": max(floors) if floors else 0,
                "avg": sum(floors) / len(floors) if floors else 0,
            },
        }


# Convenience functions for easy use in Blender

def generate_uptown_charlotte(
    min_height: float = 0.0,
    named_only: bool = False,
) -> List[Object]:
    """
    Generate Uptown Charlotte buildings in Blender.

    Args:
        min_height: Minimum building height filter
        named_only: Only generate named buildings

    Returns:
        List of created building objects
    """
    generator = CharlotteBuildingGenerator()
    generator.load_geojson("charlotte_uptown_buildings.geojson")

    print(f"Loaded {len(generator.buildings)} buildings")
    print(f"Stats: {generator.get_building_stats()}")

    objects = generator.generate_all_buildings(
        min_height=min_height,
        named_only=named_only,
    )

    print(f"Generated {len(objects)} building meshes")
    return objects


def generate_charlotte_led_buildings() -> List[Object]:
    """
    Generate only Charlotte buildings with LED facades.

    Returns:
        List of created LED building objects
    """
    generator = CharlotteBuildingGenerator()
    generator.load_geojson("charlotte_uptown_buildings.geojson")

    objects = generator.generate_led_buildings()
    print(f"Generated {len(objects)} LED building meshes")
    return objects


def generate_charlotte_tall_buildings(min_floors: int = 20) -> List[Object]:
    """
    Generate Charlotte buildings with minimum floor count.

    Args:
        min_floors: Minimum number of floors

    Returns:
        List of created building objects
    """
    generator = CharlotteBuildingGenerator()
    generator.load_geojson("charlotte_uptown_buildings.geojson")

    objects = generator.generate_all_buildings(min_floors=min_floors)
    print(f"Generated {len(objects)} tall building meshes ({min_floors}+ floors)")
    return objects


class BuildingMaterialGenerator:
    """Generates Blender materials for building types."""

    # Material presets
    MATERIAL_PRESETS = {
        BuildingMaterialType.GLASS: {
            "base_color": (0.15, 0.18, 0.22),
            "roughness": 0.1,
            "metallic": 0.0,
            "ior": 1.45,
        },
        BuildingMaterialType.GRANITE: {
            "base_color": (0.35, 0.33, 0.30),
            "roughness": 0.7,
            "metallic": 0.0,
        },
        BuildingMaterialType.CONCRETE: {
            "base_color": (0.4, 0.4, 0.38),
            "roughness": 0.8,
            "metallic": 0.0,
        },
        BuildingMaterialType.STEEL: {
            "base_color": (0.5, 0.52, 0.55),
            "roughness": 0.3,
            "metallic": 0.8,
        },
        BuildingMaterialType.BRICK: {
            "base_color": (0.6, 0.35, 0.25),
            "roughness": 0.9,
            "metallic": 0.0,
        },
        BuildingMaterialType.MIXED: {
            "base_color": (0.3, 0.3, 0.32),
            "roughness": 0.5,
            "metallic": 0.1,
        },
    }

    def __init__(self):
        self.materials: Dict[str, Any] = {}

    def get_or_create_material(
        self,
        material_type: BuildingMaterialType,
        has_led: bool = False,
        led_color: Tuple[float, float, float] = (1.0, 1.0, 0.95),
    ) -> Any:
        """
        Get or create a material for a building.

        Args:
            material_type: Type of building material
            has_led: Whether building has LED facade
            led_color: LED emission color

        Returns:
            Blender material
        """
        if not BLENDER_AVAILABLE:
            return None

        # Create unique material name
        mat_name = f"building_{material_type.value}"
        if has_led:
            mat_name += "_led"

        # Check cache
        if mat_name in self.materials:
            return self.materials[mat_name]

        # Check if material already exists
        mat = bpy.data.materials.get(mat_name)
        if mat:
            self.materials[mat_name] = mat
            return mat

        # Create new material
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        nodes.clear()

        # Get preset
        preset = self.MATERIAL_PRESETS.get(material_type, self.MATERIAL_PRESETS[BuildingMaterialType.MIXED])

        if has_led:
            # Create LED-enabled material
            self._create_led_material(nodes, links, preset, led_color)
        else:
            # Create standard material
            self._create_standard_material(nodes, links, preset)

        self.materials[mat_name] = mat
        return mat

    def _create_standard_material(self, nodes, links, preset: Dict):
        """Create a standard PBR material."""
        output = nodes.new('ShaderNodeOutputMaterial')
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')

        # Apply preset
        bsdf.inputs['Base Color'].default_value = (*preset['base_color'], 1.0)
        bsdf.inputs['Roughness'].default_value = preset['roughness']
        bsdf.inputs['Metallic'].default_value = preset.get('metallic', 0.0)

        if 'ior' in preset:
            bsdf.inputs['IOR'].default_value = preset['ior']

        # Link
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        # Position
        output.location = (300, 0)
        bsdf.location = (0, 0)

    def _create_led_material(self, nodes, links, preset: Dict, led_color: Tuple[float, float, float]):
        """Create a material with LED emission."""
        output = nodes.new('ShaderNodeOutputMaterial')
        mix = nodes.new('ShaderNodeMixShader')
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        emission = nodes.new('ShaderNodeEmission')
        fresnel = nodes.new('ShaderNodeFresnel')

        # Apply base material preset
        bsdf.inputs['Base Color'].default_value = (*preset['base_color'], 1.0)
        bsdf.inputs['Roughness'].default_value = preset['roughness']
        bsdf.inputs['Metallic'].default_value = preset.get('metallic', 0.0)

        # LED emission
        emission.inputs['Color'].default_value = (*led_color, 1.0)
        emission.inputs['Strength'].default_value = 3.0

        # Link nodes
        links.new(fresnel.outputs['Fac'], mix.inputs['Fac'])
        links.new(bsdf.outputs['BSDF'], mix.inputs[1])
        links.new(emission.outputs['Emission'], mix.inputs[2])
        links.new(mix.outputs['Shader'], output.inputs['Surface'])

        # Position
        output.location = (600, 0)
        mix.location = (300, 0)
        bsdf.location = (0, 100)
        emission.location = (0, -100)
        fresnel.location = (-200, 0)


class IntegratedCharlotteGenerator:
    """
    Integrated generator that combines GeoJSON footprints with LED facades.

    This is the main entry point for generating a complete Charlotte skyline:
    - Loads building footprints from GeoJSON
    - Generates 3D meshes with accurate heights
    - Applies appropriate materials (glass, granite, concrete)
    - Integrates LED facade system for illuminated buildings
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.building_gen = CharlotteBuildingGenerator(data_dir)
        self.material_gen = BuildingMaterialGenerator()
        self.led_configs: Dict[str, Any] = {}  # LEDBuildingConfig by building name

    def load_geojson(self, filename: str = "charlotte_uptown_buildings.geojson") -> int:
        """Load GeoJSON building data."""
        return self.building_gen.load_geojson(filename)

    def load_led_configs(self):
        """Load LED facade configurations."""
        # Import LED facade builder
        try:
            from .led_facade import LEDFacadeBuilder
            builder = LEDFacadeBuilder()
            self.led_configs = builder.create_all_charlotte_led_facades()
        except ImportError:
            pass

    def _match_led_config(self, building_name: str) -> Optional[Any]:
        """Find matching LED config for a building."""
        if not building_name or not self.led_configs:
            return None

        name_lower = building_name.lower().replace("-", " ").replace("_", " ")

        for key, config in self.led_configs.items():
            config_name = config.building_name.lower().replace("-", " ")
            if config_name in name_lower or name_lower in config_name:
                return config

        return None

    def generate_scene(
        self,
        min_height: float = 0.0,
        min_floors: int = 0,
        include_led: bool = True,
        apply_materials: bool = True,
    ) -> List[Object]:
        """
        Generate complete Charlotte scene.

        Args:
            min_height: Minimum building height filter
            min_floors: Minimum floors filter
            include_led: Include LED facade system
            apply_materials: Apply building materials

        Returns:
            List of generated building objects
        """
        if not BLENDER_AVAILABLE:
            return []

        # Load LED configs if requested
        if include_led:
            self.load_led_configs()

        # Create collection
        self.building_gen.collection = self.building_gen.create_collection()

        objects = []
        for building in self.building_gen.buildings:
            # Apply filters
            if min_height > 0 and building.height_m < min_height:
                continue
            if min_floors > 0 and building.floors < min_floors:
                continue

            # Generate mesh
            obj = self.building_gen.generate_building_mesh(building)
            if not obj:
                continue

            # Find LED config
            led_config = self._match_led_config(building.name) if include_led else None
            has_led = led_config is not None or building.has_led

            # Apply material
            if apply_materials:
                led_color = (1.0, 1.0, 0.95)  # Default warm white
                if led_config:
                    led_color = led_config.default_color

                mat = self.material_gen.get_or_create_material(
                    building.material,
                    has_led=has_led,
                    led_color=led_color,
                )
                if mat:
                    obj.data.materials.append(mat)

            objects.append(obj)

        return objects

    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics."""
        stats = self.building_gen.get_building_stats()
        stats["led_configs_loaded"] = len(self.led_configs)
        return stats


def generate_charlotte_scene(
    min_height: float = 0.0,
    min_floors: int = 0,
    with_leds: bool = True,
    with_materials: bool = True,
) -> List[Object]:
    """
    Generate a complete Charlotte skyline scene.

    This is the main convenience function for generating Charlotte buildings.

    Args:
        min_height: Minimum building height (meters)
        min_floors: Minimum number of floors
        with_leds: Include LED facade system for illuminated buildings
        with_materials: Apply PBR materials to buildings

    Returns:
        List of generated building objects

    Example:
        import bpy
        import sys
        sys.path.append('/path/to/blender_gsd')

        from lib.charlotte_digital_twin.buildings.geojson_importer import generate_charlotte_scene

        # Generate all Uptown buildings with LED facades
        buildings = generate_charlotte_scene(with_leds=True)

        # Generate only tall buildings (20+ floors)
        tall_buildings = generate_charlotte_scene(min_floors=20)
    """
    generator = IntegratedCharlotteGenerator()
    generator.load_geojson("charlotte_uptown_buildings.geojson")

    print(f"Loaded {len(generator.building_gen.buildings)} buildings")
    print(f"Stats: {generator.get_stats()}")

    objects = generator.generate_scene(
        min_height=min_height,
        min_floors=min_floors,
        include_led=with_leds,
        apply_materials=with_materials,
    )

    print(f"Generated {len(objects)} building meshes")
    return objects


# Command-line testing (without Blender)
if __name__ == "__main__":
    print("Testing GeoJSON importer (without Blender)...")

    generator = CharlotteBuildingGenerator()

    # Load and analyze
    count = generator.load_geojson("charlotte_uptown_buildings.geojson")
    print(f"Loaded {count} buildings")

    stats = generator.get_building_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")

    # Show LED buildings
    led_buildings = [b for b in generator.buildings if b.has_led]
    print(f"\nLED Buildings found: {len(led_buildings)}")
    for b in led_buildings:
        print(f"  - {b.name or 'Unnamed'}: {b.height_m}m, {b.floors} floors")
