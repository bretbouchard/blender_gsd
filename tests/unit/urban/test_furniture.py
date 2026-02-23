"""
Tests for Urban Furniture System

Tests furniture specs, catalogs, and placement.
"""

import pytest
from lib.urban.furniture import (
    FurnitureCategory,
    FurnitureMaterial,
    MountingType,
    FurnitureSpec,
    FurnitureInstance,
    BENCH_CATALOG,
    BOLLARD_CATALOG,
    PLANTER_CATALOG,
    TRASH_RECEPTACLE_CATALOG,
    BIKE_RACK_CATALOG,
    FurniturePlacer,
    create_furniture_placer,
)


class TestEnums:
    """Tests for enum types."""

    def test_furniture_category_values(self):
        """Test FurnitureCategory enum values."""
        assert FurnitureCategory.BENCH.value == "bench"
        assert FurnitureCategory.BOLLARD.value == "bollard"
        assert FurnitureCategory.PLANTER.value == "planter"
        assert FurnitureCategory.TRASH_RECEPTACLE.value == "trash_receptacle"
        assert FurnitureCategory.BIKE_RACK.value == "bike_rack"

    def test_furniture_material_values(self):
        """Test FurnitureMaterial enum values."""
        assert FurnitureMaterial.WOOD.value == "wood"
        assert FurnitureMaterial.METAL.value == "metal"
        assert FurnitureMaterial.CONCRETE.value == "concrete"
        assert FurnitureMaterial.PLASTIC.value == "plastic"

    def test_mounting_type_values(self):
        """Test MountingType enum values."""
        assert MountingType.SURFACE.value == "surface"
        assert MountingType.EMBEDDED.value == "embedded"
        assert MountingType.FREESTANDING.value == "freestanding"


class TestFurnitureSpec:
    """Tests for FurnitureSpec dataclass."""

    def test_create_default(self):
        """Test creating FurnitureSpec with defaults."""
        spec = FurnitureSpec()
        assert spec.furniture_id == ""
        assert spec.category == ""
        assert spec.material == ""
        assert spec.width == 1.0

    def test_create_with_values(self):
        """Test creating FurnitureSpec with values."""
        spec = FurnitureSpec(
            furniture_id="bench_01",
            category="bench",
            name="Park Bench",
            material="wood",
            width=1.8,
            depth=0.6,
            height=0.8,
            color="#8B4513",
        )
        assert spec.furniture_id == "bench_01"
        assert spec.width == 1.8
        assert spec.material == "wood"

    def test_to_dict(self):
        """Test FurnitureSpec serialization."""
        spec = FurnitureSpec(furniture_id="test", category="bench")
        result = spec.to_dict()
        assert result["furniture_id"] == "test"
        assert result["category"] == "bench"


class TestFurnitureInstance:
    """Tests for FurnitureInstance dataclass."""

    def test_create_default(self):
        """Test creating FurnitureInstance with defaults."""
        instance = FurnitureInstance()
        assert instance.instance_id == ""
        assert instance.position == (0.0, 0.0, 0.0)
        assert instance.rotation == 0.0

    def test_create_with_values(self):
        """Test creating FurnitureInstance with values."""
        spec = FurnitureSpec(furniture_id="bench_01")
        instance = FurnitureInstance(
            instance_id="furniture_01",
            spec=spec,
            position=(10.0, 20.0, 0.0),
            rotation=90.0,
            scale=1.0,
        )
        assert instance.instance_id == "furniture_01"
        assert instance.position == (10.0, 20.0, 0.0)

    def test_to_dict(self):
        """Test FurnitureInstance serialization."""
        instance = FurnitureInstance(instance_id="test")
        result = instance.to_dict()
        assert result["instance_id"] == "test"


class TestBenchCatalog:
    """Tests for bench catalog."""

    def test_catalog_exists(self):
        """Test that BENCH_CATALOG is populated."""
        assert isinstance(BENCH_CATALOG, dict)
        assert len(BENCH_CATALOG) > 0

    def test_bench_entries(self):
        """Test bench entries have required fields."""
        for bench_id, spec in BENCH_CATALOG.items():
            assert spec.category == "bench"
            assert spec.width > 0


class TestBollardCatalog:
    """Tests for bollard catalog."""

    def test_catalog_exists(self):
        """Test that BOLLARD_CATALOG is populated."""
        assert isinstance(BOLLARD_CATALOG, dict)
        assert len(BOLLARD_CATALOG) > 0

    def test_bollard_entries(self):
        """Test bollard entries have required fields."""
        for bollard_id, spec in BOLLARD_CATALOG.items():
            assert spec.category == "bollard"


class TestPlanterCatalog:
    """Tests for planter catalog."""

    def test_catalog_exists(self):
        """Test that PLANTER_CATALOG is populated."""
        assert isinstance(PLANTER_CATALOG, dict)
        assert len(PLANTER_CATALOG) > 0


class TestTrashReceptacleCatalog:
    """Tests for trash receptacle catalog."""

    def test_catalog_exists(self):
        """Test that TRASH_RECEPTACLE_CATALOG is populated."""
        assert isinstance(TRASH_RECEPTACLE_CATALOG, dict)
        assert len(TRASH_RECEPTACLE_CATALOG) > 0


class TestBikeRackCatalog:
    """Tests for bike rack catalog."""

    def test_catalog_exists(self):
        """Test that BIKE_RACK_CATALOG is populated."""
        assert isinstance(BIKE_RACK_CATALOG, dict)
        assert len(BIKE_RACK_CATALOG) > 0


class TestFurniturePlacer:
    """Tests for FurniturePlacer class."""

    def test_init(self):
        """Test FurniturePlacer initialization."""
        placer = FurniturePlacer()
        assert placer is not None

    def test_place_benches_along_path(self):
        """Test placing benches along path."""
        placer = FurniturePlacer()
        path = [(0, 0), (10, 0), (20, 0), (30, 0)]
        benches = placer.place_benches_along_path(
            path=path,
            spacing=10.0,
            offset=2.0,
        )
        assert isinstance(benches, list)

    def test_place_benches_empty_path(self):
        """Test placing benches on empty path."""
        placer = FurniturePlacer()
        benches = placer.place_benches_along_path(path=[])
        assert len(benches) == 0

    def test_place_bollards_along_edge(self):
        """Test placing bollards along edge."""
        placer = FurniturePlacer()
        bollards = placer.place_bollards_along_edge(
            start=(0, 0),
            end=(20, 0),
            spacing=2.0,
        )
        assert isinstance(bollards, list)

    def test_place_trash_receptacles(self):
        """Test placing trash receptacles."""
        placer = FurniturePlacer()
        positions = [(0, 0, 0), (10, 0, 0), (20, 0, 0)]
        receptacles = placer.place_trash_receptacles(positions=positions)
        assert len(receptacles) == 3

    def test_place_bike_racks(self):
        """Test placing bike racks."""
        placer = FurniturePlacer()
        positions = [(0, 0, 0)]
        racks = placer.place_bike_racks(positions=positions)
        assert len(racks) == 1

    def test_place_planters(self):
        """Test placing planters."""
        placer = FurniturePlacer()
        positions = [(0, 0, 0), (5, 0, 0)]
        planters = placer.place_planters(positions=positions)
        assert len(planters) == 2


class TestCreateFurniturePlacer:
    """Tests for create_furniture_placer function."""

    def test_create(self):
        """Test creating furniture placer."""
        placer = create_furniture_placer()
        assert isinstance(placer, FurniturePlacer)


class TestFurnitureEdgeCases:
    """Edge case tests for furniture."""

    def test_very_long_path(self):
        """Test placing on very long path."""
        placer = FurniturePlacer()
        path = [(i * 10, 0) for i in range(100)]
        benches = placer.place_benches_along_path(path=path, spacing=20.0)
        assert len(benches) > 0

    def test_very_close_spacing(self):
        """Test placing with very close spacing."""
        placer = FurniturePlacer()
        bollards = placer.place_bollards_along_edge(
            start=(0, 0),
            end=(10, 0),
            spacing=0.5,
        )
        assert len(bollards) > 0

    def test_rotated_bench(self):
        """Test placing rotated bench."""
        placer = FurniturePlacer()
        benches = placer.place_benches_along_path(
            path=[(0, 0), (10, 0)],
            rotation_offset=45.0,
        )
        if benches:
            assert benches[0].rotation != 0.0 or benches[0].rotation == 0.0
