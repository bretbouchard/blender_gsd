"""
Unit tests for lib/geometry_nodes/asset_instances.py

Tests the asset instance library system including:
- AssetReference dataclass
- InstanceSpec dataclass
- InstancePool dataclass
- ScaleNormalizer
- AssetInstanceLibrary
- create_asset_id function
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

from lib.geometry_nodes.asset_instances import (
    AssetType,
    AssetFormat,
    AssetReference,
    InstanceSpec,
    InstancePool,
    ScaleNormalizer,
    AssetInstanceLibrary,
    create_asset_id,
)


class TestAssetType:
    """Tests for AssetType enum."""

    def test_asset_type_values(self):
        """Test that AssetType enum has expected values."""
        assert AssetType.PROPS.value == "props"
        assert AssetType.FURNITURE.value == "furniture"
        assert AssetType.VEHICLES.value == "vehicles"
        assert AssetType.CHARACTERS.value == "characters"
        assert AssetType.ARCHITECTURE.value == "architecture"
        assert AssetType.NATURE.value == "nature"
        assert AssetType.EFFECTS.value == "effects"

    def test_asset_type_count(self):
        """Test that all expected asset types exist."""
        assert len(AssetType) == 7


class TestAssetFormat:
    """Tests for AssetFormat enum."""

    def test_asset_format_values(self):
        """Test that AssetFormat enum has expected values."""
        assert AssetFormat.BLEND.value == "blend"
        assert AssetFormat.FBX.value == "fbx"
        assert AssetFormat.OBJ.value == "obj"
        assert AssetFormat.GLB.value == "glb"
        assert AssetFormat.GLTF.value == "gltf"

    def test_asset_format_count(self):
        """Test that all expected formats exist."""
        assert len(AssetFormat) == 5


class TestAssetReference:
    """Tests for AssetReference dataclass."""

    def test_default_values(self):
        """Test AssetReference default values."""
        asset = AssetReference()
        assert asset.asset_id == ""
        assert asset.name == ""
        assert asset.asset_type == "props"
        assert asset.file_path == ""
        assert asset.format == "blend"
        assert asset.collection_name == ""
        assert asset.bbox == (1.0, 1.0, 1.0)
        assert asset.reference_scale == 1.0
        assert asset.tags == []
        assert asset.categories == []

    def test_custom_values(self):
        """Test AssetReference with custom values."""
        asset = AssetReference(
            asset_id="sofa_001",
            name="Modern Sofa",
            asset_type="furniture",
            file_path="/assets/furniture/sofa.blend",
            format="blend",
            collection_name="Sofa_Modern",
            bbox=(2.0, 1.0, 0.8),
            reference_scale=0.75,
            tags=["living_room", "modern"],
            categories=["seating", "indoor"],
        )
        assert asset.asset_id == "sofa_001"
        assert asset.name == "Modern Sofa"
        assert asset.asset_type == "furniture"
        assert asset.bbox == (2.0, 1.0, 0.8)
        assert "living_room" in asset.tags

    def test_to_dict(self):
        """Test AssetReference.to_dict() serialization."""
        asset = AssetReference(
            asset_id="chair_001",
            name="Office Chair",
            tags=["office", "seating"],
        )
        data = asset.to_dict()
        assert data["asset_id"] == "chair_001"
        assert data["name"] == "Office Chair"
        assert data["tags"] == ["office", "seating"]
        assert "bbox" in data
        assert isinstance(data["bbox"], list)

    def test_from_dict(self):
        """Test AssetReference.from_dict() deserialization."""
        data = {
            "asset_id": "table_001",
            "name": "Dining Table",
            "asset_type": "furniture",
            "bbox": [1.8, 1.0, 0.75],
            "tags": ["dining", "wood"],
        }
        asset = AssetReference.from_dict(data)
        assert asset.asset_id == "table_001"
        assert asset.name == "Dining Table"
        assert asset.bbox == (1.8, 1.0, 0.75)
        assert "wood" in asset.tags

    def test_roundtrip_serialization(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = AssetReference(
            asset_id="test_001",
            name="Test Asset",
            bbox=(1.5, 2.0, 3.0),
            reference_scale=0.5,
        )
        data = original.to_dict()
        restored = AssetReference.from_dict(data)
        assert restored.asset_id == original.asset_id
        assert restored.name == original.name
        assert restored.bbox == original.bbox
        assert restored.reference_scale == original.reference_scale


class TestInstanceSpec:
    """Tests for InstanceSpec dataclass."""

    def test_default_values(self):
        """Test InstanceSpec default values."""
        spec = InstanceSpec()
        assert spec.instance_id == ""
        assert spec.asset_id == ""
        assert spec.position == (0.0, 0.0, 0.0)
        assert spec.rotation == (0.0, 0.0, 0.0)
        assert spec.scale == 1.0
        assert spec.variant == 0
        assert spec.lod_level == 0
        assert spec.visibility is True

    def test_custom_values(self):
        """Test InstanceSpec with custom values."""
        spec = InstanceSpec(
            instance_id="inst_001",
            asset_id="sofa_001",
            position=(5.0, 3.0, 0.0),
            rotation=(0.0, 0.0, 90.0),
            scale=1.5,
            variant=2,
            lod_level=1,
            visibility=False,
            custom_properties={"color": "red"},
        )
        assert spec.instance_id == "inst_001"
        assert spec.position == (5.0, 3.0, 0.0)
        assert spec.rotation == (0.0, 0.0, 90.0)
        assert spec.scale == 1.5
        assert spec.visibility is False
        assert spec.custom_properties["color"] == "red"

    def test_to_dict(self):
        """Test InstanceSpec.to_dict() serialization."""
        spec = InstanceSpec(
            instance_id="inst_002",
            asset_id="chair_001",
            position=(1.0, 2.0, 3.0),
        )
        data = spec.to_dict()
        assert data["instance_id"] == "inst_002"
        assert data["position"] == [1.0, 2.0, 3.0]
        assert data["scale"] == 1.0

    def test_from_dict(self):
        """Test InstanceSpec.from_dict() deserialization."""
        data = {
            "instance_id": "inst_003",
            "asset_id": "table_001",
            "position": [10.0, 20.0, 0.0],
            "rotation": [0.0, 0.0, 45.0],
            "scale": 2.0,
        }
        spec = InstanceSpec.from_dict(data)
        assert spec.instance_id == "inst_003"
        assert spec.position == (10.0, 20.0, 0.0)
        assert spec.rotation == (0.0, 0.0, 45.0)
        assert spec.scale == 2.0


class TestInstancePool:
    """Tests for InstancePool dataclass."""

    def test_default_values(self):
        """Test InstancePool default values."""
        pool = InstancePool()
        assert pool.pool_id == ""
        assert pool.instances == []
        assert pool.asset_cache == {}
        assert pool.total_bounds == (0, 0, 0, 1, 1, 1)

    def test_instance_count(self):
        """Test InstancePool.instance_count property."""
        pool = InstancePool()
        assert pool.instance_count == 0

        pool.instances.append(InstanceSpec(instance_id="inst_001"))
        pool.instances.append(InstanceSpec(instance_id="inst_002"))
        assert pool.instance_count == 2

    def test_add_instance(self):
        """Test InstancePool.add_instance() method."""
        pool = InstancePool(pool_id="pool_001")
        instance = InstanceSpec(instance_id="inst_001", asset_id="sofa_001")
        asset = AssetReference(asset_id="sofa_001", name="Sofa")

        pool.add_instance(instance, asset)

        assert len(pool.instances) == 1
        assert pool.instances[0].instance_id == "inst_001"
        assert "sofa_001" in pool.asset_cache

    def test_add_instance_without_asset(self):
        """Test add_instance without providing asset."""
        pool = InstancePool(pool_id="pool_001")
        instance = InstanceSpec(instance_id="inst_001", asset_id="sofa_001")

        pool.add_instance(instance)

        assert len(pool.instances) == 1
        assert len(pool.asset_cache) == 0

    def test_to_dict(self):
        """Test InstancePool.to_dict() serialization."""
        pool = InstancePool(pool_id="pool_001")
        instance = InstanceSpec(instance_id="inst_001", asset_id="sofa_001")
        pool.add_instance(instance)

        data = pool.to_dict()
        assert data["pool_id"] == "pool_001"
        assert len(data["instances"]) == 1


class TestScaleNormalizer:
    """Tests for ScaleNormalizer class."""

    def test_default_reference(self):
        """Test ScaleNormalizer with default reference."""
        normalizer = ScaleNormalizer()
        assert normalizer.default_reference == 1.0

    def test_custom_reference(self):
        """Test ScaleNormalizer with custom reference."""
        normalizer = ScaleNormalizer(default_reference=2.0)
        assert normalizer.default_reference == 2.0

    def test_reference_heights(self):
        """Test that reference heights are defined."""
        normalizer = ScaleNormalizer()
        assert "furniture" in normalizer.REFERENCE_HEIGHTS
        assert "characters" in normalizer.REFERENCE_HEIGHTS
        assert "vehicles" in normalizer.REFERENCE_HEIGHTS

    def test_normalize_furniture(self):
        """Test normalization for furniture asset."""
        normalizer = ScaleNormalizer()
        asset = AssetReference(
            asset_id="chair_001",
            asset_type="furniture",
            reference_scale=0.75,  # Chair seat height
        )
        scale = normalizer.normalize(asset)
        # Target height is 0.75 (furniture reference), so scale should be 1.0
        assert scale == pytest.approx(1.0, rel=0.01)

    def test_normalize_with_custom_target(self):
        """Test normalization with custom target height."""
        normalizer = ScaleNormalizer()
        asset = AssetReference(
            asset_id="chair_001",
            asset_type="furniture",
            reference_scale=0.5,
        )
        scale = normalizer.normalize(asset, target_height=1.0)
        assert scale == pytest.approx(2.0, rel=0.01)

    def test_normalize_zero_reference_scale(self):
        """Test normalization with zero reference scale."""
        normalizer = ScaleNormalizer()
        asset = AssetReference(asset_id="test", reference_scale=0.0)
        scale = normalizer.normalize(asset)
        assert scale == 1.0

    def test_denormalize(self):
        """Test denormalization."""
        normalizer = ScaleNormalizer()
        asset = AssetReference(
            asset_id="chair_001",
            asset_type="furniture",
            reference_scale=0.75,
        )
        normalized = normalizer.normalize(asset)
        denormalized = normalizer.denormalize(asset, normalized)
        assert denormalized == pytest.approx(1.0, rel=0.01)


class TestAssetInstanceLibrary:
    """Tests for AssetInstanceLibrary class."""

    def test_empty_library(self):
        """Test empty library initialization."""
        library = AssetInstanceLibrary()
        assert len(library.assets) == 0
        assert len(library.pools) == 0

    def test_add_asset(self):
        """Test adding an asset to the library."""
        library = AssetInstanceLibrary()
        asset = AssetReference(asset_id="sofa_001", name="Sofa")

        library.add_asset(asset)

        assert "sofa_001" in library.assets
        assert library.assets["sofa_001"].name == "Sofa"

    def test_get_asset(self):
        """Test getting an asset by ID."""
        library = AssetInstanceLibrary()
        asset = AssetReference(asset_id="sofa_001", name="Sofa")
        library.add_asset(asset)

        result = library.get_asset("sofa_001")
        assert result.name == "Sofa"

        result = library.get_asset("nonexistent")
        assert result is None

    def test_create_instance(self):
        """Test creating an instance."""
        library = AssetInstanceLibrary()
        asset = AssetReference(
            asset_id="sofa_001",
            name="Sofa",
            asset_type="furniture",
            reference_scale=0.75,
        )
        library.add_asset(asset)

        instance = library.create_instance(
            "sofa_001",
            position=(5.0, 3.0, 0.0),
            rotation=(0.0, 0.0, 90.0),
        )

        assert instance is not None
        assert instance.asset_id == "sofa_001"
        assert instance.position == (5.0, 3.0, 0.0)
        assert instance.rotation == (0.0, 0.0, 90.0)

    def test_create_instance_nonexistent_asset(self):
        """Test creating instance for nonexistent asset."""
        library = AssetInstanceLibrary()
        instance = library.create_instance("nonexistent")
        assert instance is None

    def test_create_instance_with_pool(self):
        """Test creating instance and adding to pool."""
        library = AssetInstanceLibrary()
        asset = AssetReference(asset_id="sofa_001", name="Sofa")
        library.add_asset(asset)

        instance = library.create_instance("sofa_001", pool_id="room_001")

        assert instance is not None
        assert "room_001" in library.pools
        assert library.pools["room_001"].instance_count == 1

    def test_create_pool(self):
        """Test creating an instance pool."""
        library = AssetInstanceLibrary()
        pool = library.create_pool("pool_001")

        assert pool.pool_id == "pool_001"
        assert "pool_001" in library.pools

    def test_get_pool(self):
        """Test getting a pool by ID."""
        library = AssetInstanceLibrary()
        library.create_pool("pool_001")

        pool = library.get_pool("pool_001")
        assert pool.pool_id == "pool_001"

        pool = library.get_pool("nonexistent")
        assert pool is None

    def test_search_by_name(self):
        """Test searching assets by name."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(asset_id="sofa_001", name="Modern Sofa"))
        library.add_asset(AssetReference(asset_id="chair_001", name="Office Chair"))
        library.add_asset(AssetReference(asset_id="table_001", name="Dining Table"))

        results = library.search(query="sofa")
        assert len(results) == 1
        assert results[0].name == "Modern Sofa"

    def test_search_by_type(self):
        """Test searching assets by type."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(asset_id="sofa_001", name="Sofa", asset_type="furniture"))
        library.add_asset(AssetReference(asset_id="car_001", name="Car", asset_type="vehicles"))

        results = library.search(asset_type="furniture")
        assert len(results) == 1
        assert results[0].asset_type == "furniture"

    def test_search_by_tags(self):
        """Test searching assets by tags."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(
            asset_id="sofa_001",
            name="Sofa",
            tags=["living_room", "modern"],
        ))
        library.add_asset(AssetReference(
            asset_id="chair_001",
            name="Chair",
            tags=["office"],
        ))

        results = library.search(tags=["living_room"])
        assert len(results) == 1
        assert results[0].name == "Sofa"

    def test_search_by_category(self):
        """Test searching assets by category."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(
            asset_id="sofa_001",
            name="Sofa",
            categories=["seating", "indoor"],
        ))
        library.add_asset(AssetReference(
            asset_id="tree_001",
            name="Tree",
            categories=["nature", "outdoor"],
        ))

        results = library.search(category="seating")
        assert len(results) == 1

    def test_search_combined_filters(self):
        """Test searching with combined filters."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(
            asset_id="sofa_001",
            name="Modern Sofa",
            asset_type="furniture",
            tags=["living_room"],
        ))
        library.add_asset(AssetReference(
            asset_id="chair_001",
            name="Modern Chair",
            asset_type="furniture",
            tags=["office"],
        ))
        library.add_asset(AssetReference(
            asset_id="car_001",
            name="Modern Car",
            asset_type="vehicles",
            tags=["living_room"],
        ))

        results = library.search(query="modern", asset_type="furniture")
        assert len(results) == 2

    def test_to_gn_input(self):
        """Test converting library to GN input format."""
        library = AssetInstanceLibrary()
        asset = AssetReference(asset_id="sofa_001", name="Sofa")
        library.add_asset(asset)
        library.create_instance("sofa_001", pool_id="room_001")

        gn_data = library.to_gn_input()
        assert "version" in gn_data
        assert "pools" in gn_data
        assert "assets" in gn_data
        assert len(gn_data["pools"]) == 1

    def test_to_gn_input_specific_pool(self):
        """Test converting specific pool to GN input."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(asset_id="sofa_001", name="Sofa"))
        library.create_instance("sofa_001", pool_id="room_001")
        library.create_instance("sofa_001", pool_id="room_002")

        gn_data = library.to_gn_input(pool_id="room_001")
        assert len(gn_data["pools"]) == 1
        assert gn_data["pools"][0]["pool_id"] == "room_001"

    def test_generate_instance_points(self):
        """Test generating instances at multiple points."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(
            asset_id="tree_001",
            name="Tree",
            asset_type="nature",
            reference_scale=2.0,
        ))

        points = [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (10.0, 0.0, 0.0)]
        instances = library.generate_instance_points("tree_001", points)

        assert len(instances) == 3
        assert instances[0].position == (0.0, 0.0, 0.0)
        assert instances[1].position == (5.0, 0.0, 0.0)
        assert instances[2].position == (10.0, 0.0, 0.0)

    def test_generate_instance_points_with_rotations(self):
        """Test generating instances with custom rotations."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(asset_id="tree_001", name="Tree"))

        points = [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0)]
        rotations = [(0.0, 0.0, 0.0), (0.0, 0.0, 90.0)]

        instances = library.generate_instance_points(
            "tree_001", points, rotations=rotations
        )

        assert instances[0].rotation == (0.0, 0.0, 0.0)
        assert instances[1].rotation == (0.0, 0.0, 90.0)

    def test_generate_instance_points_with_scales(self):
        """Test generating instances with custom scales."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(asset_id="tree_001", name="Tree"))

        points = [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0)]
        scales = [1.0, 2.0]

        instances = library.generate_instance_points(
            "tree_001", points, scales=scales
        )

        assert instances[0].scale == 1.0
        assert instances[1].scale == 2.0

    def test_load_catalog(self):
        """Test loading assets from catalog JSON."""
        library = AssetInstanceLibrary()

        catalog_data = {
            "version": "1.0",
            "assets": [
                {"asset_id": "sofa_001", "name": "Sofa"},
                {"asset_id": "chair_001", "name": "Chair"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(catalog_data, f)
            temp_path = f.name

        try:
            count = library.load_catalog(temp_path)
            assert count == 2
            assert "sofa_001" in library.assets
            assert "chair_001" in library.assets
        finally:
            os.unlink(temp_path)

    def test_save_catalog(self):
        """Test saving assets to catalog JSON."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(asset_id="sofa_001", name="Sofa"))
        library.add_asset(AssetReference(asset_id="chair_001", name="Chair"))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            library.save_catalog(temp_path)

            with open(temp_path, 'r') as f:
                data = json.load(f)

            assert data["version"] == "1.0"
            assert len(data["assets"]) == 2
        finally:
            os.unlink(temp_path)

    def test_instance_counter_increments(self):
        """Test that instance counter increments properly."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(asset_id="sofa_001", name="Sofa"))

        inst1 = library.create_instance("sofa_001")
        inst2 = library.create_instance("sofa_001")
        inst3 = library.create_instance("sofa_001")

        assert inst1.instance_id != inst2.instance_id
        assert inst2.instance_id != inst3.instance_id


class TestCreateAssetId:
    """Tests for create_asset_id function."""

    def test_create_asset_id_deterministic(self):
        """Test that create_asset_id is deterministic."""
        id1 = create_asset_id("/assets/sofa.blend", "Sofa_Collection")
        id2 = create_asset_id("/assets/sofa.blend", "Sofa_Collection")
        assert id1 == id2

    def test_create_asset_id_unique(self):
        """Test that different inputs produce different IDs."""
        id1 = create_asset_id("/assets/sofa.blend", "Sofa_Collection")
        id2 = create_asset_id("/assets/chair.blend", "Chair_Collection")
        assert id1 != id2

    def test_create_asset_id_format(self):
        """Test that asset ID has expected format."""
        asset_id = create_asset_id("/path/to/asset.blend", "Collection")
        assert asset_id.startswith("asset_")
        assert len(asset_id) == len("asset_") + 8  # 8 hex characters

    def test_create_asset_id_same_file_different_collection(self):
        """Test that same file with different collection produces different IDs."""
        id1 = create_asset_id("/assets.blend", "Sofa")
        id2 = create_asset_id("/assets.blend", "Chair")
        assert id1 != id2


class TestAssetInstanceLibraryEdgeCases:
    """Edge case tests for AssetInstanceLibrary."""

    def test_search_empty_library(self):
        """Test searching an empty library."""
        library = AssetInstanceLibrary()
        results = library.search(query="sofa")
        assert results == []

    def test_search_no_matches(self):
        """Test searching with no matches."""
        library = AssetInstanceLibrary()
        library.add_asset(AssetReference(asset_id="sofa_001", name="Sofa"))

        results = library.search(query="helicopter")
        assert results == []

    def test_create_instance_with_custom_scale(self):
        """Test creating instance with custom scale (no normalization)."""
        library = AssetInstanceLibrary()
        asset = AssetReference(
            asset_id="sofa_001",
            name="Sofa",
            reference_scale=0.5,
        )
        library.add_asset(asset)

        instance = library.create_instance("sofa_001", scale=2.0, normalize=False)
        assert instance.scale == 2.0

    def test_generate_instance_points_nonexistent_asset(self):
        """Test generating instances for nonexistent asset."""
        library = AssetInstanceLibrary()
        instances = library.generate_instance_points("nonexistent", [(0, 0, 0)])
        assert instances == []

    def test_to_gn_input_empty_library(self):
        """Test converting empty library to GN input."""
        library = AssetInstanceLibrary()
        gn_data = library.to_gn_input()
        assert gn_data["pools"] == []
        assert gn_data["assets"] == {}

    def test_to_gn_input_nonexistent_pool(self):
        """Test converting nonexistent pool to GN input."""
        library = AssetInstanceLibrary()
        gn_data = library.to_gn_input(pool_id="nonexistent")
        assert gn_data["pools"] == []

    def test_load_catalog_empty_assets(self):
        """Test loading catalog with no assets."""
        library = AssetInstanceLibrary()

        catalog_data = {"version": "1.0", "assets": []}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(catalog_data, f)
            temp_path = f.name

        try:
            count = library.load_catalog(temp_path)
            assert count == 0
        finally:
            os.unlink(temp_path)
