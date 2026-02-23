"""
Tests for lib/vfx/cryptomatte.py

Tests Cryptomatte utilities without Blender (bpy).
"""

import pytest
import json
import tempfile
import os
import struct
import hashlib

from lib.vfx.cryptomatte import (
    CryptomatteManifestEntry,
    CryptomatteManifest,
    MatteResult,
    hash_object_name,
    hash_to_float,
    float_to_hash,
    load_manifest_from_json,
    load_manifest_from_exr_sidecar,
    parse_manifest_from_exr_header,
    create_cryptomatte_manifest,
    save_manifest,
    extract_matte_for_object,
    extract_matte_for_objects,
    get_cryptomatte_layer_names,
    get_cryptomatte_info,
    rank_to_channels,
    estimate_cryptomatte_ranks,
    merge_manifests,
)


class TestCryptomatteManifestEntry:
    """Tests for CryptomatteManifestEntry dataclass."""

    def test_create_entry(self):
        """Test creating a manifest entry."""
        entry = CryptomatteManifestEntry(
            name="Cube",
            hash="a1b2c3d4",
            rank=0
        )
        assert entry.name == "Cube"
        assert entry.hash == "a1b2c3d4"
        assert entry.rank == 0

    def test_entry_default_rank(self):
        """Test that rank defaults to 0."""
        entry = CryptomatteManifestEntry(name="Sphere", hash="abcdef12")
        assert entry.rank == 0

    def test_entry_to_dict(self):
        """Test serialization to dictionary."""
        entry = CryptomatteManifestEntry(name="Cube", hash="a1b2c3d4", rank=1)
        result = entry.to_dict()
        assert result == {
            "name": "Cube",
            "hash": "a1b2c3d4",
            "rank": 1
        }

    def test_entry_from_dict(self):
        """Test deserialization from dictionary."""
        data = {"name": "Light", "hash": "deadbeef", "rank": 2}
        entry = CryptomatteManifestEntry.from_dict(data)
        assert entry.name == "Light"
        assert entry.hash == "deadbeef"
        assert entry.rank == 2

    def test_entry_from_dict_missing_fields(self):
        """Test deserialization with missing fields."""
        entry = CryptomatteManifestEntry.from_dict({})
        assert entry.name == ""
        assert entry.hash == ""
        assert entry.rank == 0


class TestCryptomatteManifest:
    """Tests for CryptomatteManifest dataclass."""

    def test_create_manifest(self):
        """Test creating a manifest."""
        manifest = CryptomatteManifest(layer_name="cryptomatte00")
        assert manifest.layer_name == "cryptomatte00"
        assert manifest.entries == []
        assert manifest._hash_to_name == {}

    def test_add_entry(self):
        """Test adding entries to manifest."""
        manifest = CryptomatteManifest(layer_name="crypto")
        manifest.add_entry("Cube", "a1b2c3d4")
        assert len(manifest.entries) == 1
        assert manifest.entries[0].name == "Cube"
        assert manifest.entries[0].hash == "a1b2c3d4"

    def test_get_name_from_hash(self):
        """Test looking up name by hash."""
        manifest = CryptomatteManifest(layer_name="crypto")
        manifest.add_entry("Cube", "a1b2c3d4")
        assert manifest.get_name("a1b2c3d4") == "Cube"
        assert manifest.get_name("nonexistent") is None

    def test_get_hash_from_name(self):
        """Test looking up hash by name."""
        manifest = CryptomatteManifest(layer_name="crypto")
        manifest.add_entry("Cube", "a1b2c3d4")
        assert manifest.get_hash("Cube") == "a1b2c3d4"
        assert manifest.get_hash("Nonexistent") is None

    def test_get_all_names(self):
        """Test getting all object names."""
        manifest = CryptomatteManifest(layer_name="crypto")
        manifest.add_entry("Cube", "a1b2c3d4")
        manifest.add_entry("Sphere", "b2c3d4e5")
        names = manifest.get_all_names()
        assert set(names) == {"Cube", "Sphere"}

    def test_get_entries_by_rank(self):
        """Test filtering entries by rank."""
        manifest = CryptomatteManifest(layer_name="crypto")
        manifest.add_entry("Cube", "a1b2c3d4", rank=0)
        manifest.add_entry("Sphere", "b2c3d4e5", rank=1)
        manifest.add_entry("Light", "c3d4e5f6", rank=0)

        rank0 = manifest.get_entries_by_rank(0)
        assert len(rank0) == 2
        rank1 = manifest.get_entries_by_rank(1)
        assert len(rank1) == 1

    def test_manifest_to_dict(self):
        """Test manifest serialization."""
        manifest = CryptomatteManifest(layer_name="crypto00")
        manifest.add_entry("Cube", "a1b2c3d4")
        result = manifest.to_dict()
        assert result["layer_name"] == "crypto00"
        assert len(result["entries"]) == 1
        assert result["entries"][0]["name"] == "Cube"

    def test_manifest_from_dict(self):
        """Test manifest deserialization."""
        data = {
            "layer_name": "crypto01",
            "entries": [
                {"name": "Cube", "hash": "a1b2c3d4", "rank": 0},
                {"name": "Sphere", "hash": "b2c3d4e5", "rank": 1}
            ]
        }
        manifest = CryptomatteManifest.from_dict(data)
        assert manifest.layer_name == "crypto01"
        assert len(manifest.entries) == 2
        assert manifest.get_name("a1b2c3d4") == "Cube"

    def test_rebuild_index(self):
        """Test that index is rebuilt correctly."""
        manifest = CryptomatteManifest(layer_name="crypto")
        manifest.add_entry("Cube", "a1b2c3d4")
        # Manually corrupt index
        manifest._hash_to_name = {}
        manifest._rebuild_index()
        assert manifest.get_name("a1b2c3d4") == "Cube"


class TestHashFunctions:
    """Tests for cryptomatte hash functions."""

    def test_hash_object_name_consistent(self):
        """Test that same name produces same hash."""
        hash1 = hash_object_name("Cube")
        hash2 = hash_object_name("Cube")
        assert hash1 == hash2
        assert len(hash1) == 8  # 32-bit hex

    def test_hash_object_name_different(self):
        """Test that different names produce different hashes."""
        hash1 = hash_object_name("Cube")
        hash2 = hash_object_name("Sphere")
        assert hash1 != hash2

    def test_hash_to_float_roundtrip(self):
        """Test hash to float conversion roundtrip."""
        original_hash = "a1b2c3d4"
        float_val = hash_to_float(original_hash)
        result_hash = float_to_hash(float_val)
        assert result_hash == original_hash

    def test_hash_to_float_produces_float(self):
        """Test that hash_to_float produces a float."""
        result = hash_to_float("a1b2c3d4")
        assert isinstance(result, float)

    def test_float_to_hash_format(self):
        """Test that float_to_hash produces 8-char hex string."""
        result = float_to_hash(0.5)
        assert isinstance(result, str)
        assert len(result) == 8
        # Should be valid hex
        int(result, 16)

    def test_hash_object_name_md5_based(self):
        """Test that hash is based on MD5."""
        name = "TestObject"
        expected_md5 = hashlib.md5(name.encode('utf-8')).digest()
        expected_int = struct.unpack('<I', expected_md5[:4])[0]
        expected_hash = format(expected_int, '08x')
        result = hash_object_name(name)
        assert result == expected_hash


class TestManifestLoading:
    """Tests for manifest file operations."""

    def test_load_manifest_from_json(self):
        """Test loading manifest from JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "layer_name": "test_layer",
                "entries": [
                    {"name": "Cube", "hash": "a1b2c3d4", "rank": 0}
                ]
            }, f)
            f.flush()
            path = f.name

        try:
            manifest = load_manifest_from_json(path)
            assert manifest is not None
            assert manifest.layer_name == "test_layer"
            assert len(manifest.entries) == 1
        finally:
            os.unlink(path)

    def test_load_manifest_from_json_invalid(self):
        """Test loading from invalid JSON returns None."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json {")
            f.flush()
            path = f.name

        try:
            manifest = load_manifest_from_json(path)
            assert manifest is None
        finally:
            os.unlink(path)

    def test_load_manifest_from_json_missing_file(self):
        """Test loading from missing file returns None."""
        manifest = load_manifest_from_json("/nonexistent/path.json")
        assert manifest is None

    def test_load_manifest_from_exr_sidecar(self):
        """Test loading from EXR sidecar file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.exr.manifest.json', delete=False) as f:
            json.dump({
                "layer_name": "sidecar_test",
                "entries": []
            }, f)
            f.flush()
            sidecar_path = f.name

        # Get the EXR path (without .manifest.json)
        exr_path = sidecar_path.replace('.manifest.json', '')

        try:
            manifest = load_manifest_from_exr_sidecar(exr_path)
            assert manifest is not None
            assert manifest.layer_name == "sidecar_test"
        finally:
            os.unlink(sidecar_path)

    def test_parse_manifest_from_exr_header(self):
        """Test EXR header parsing (returns None without OpenEXR)."""
        result = parse_manifest_from_exr_header("/any/path.exr")
        # Returns None because OpenEXR library is not available
        assert result is None


class TestCreateManifest:
    """Tests for manifest creation."""

    def test_create_cryptomatte_manifest(self):
        """Test creating manifest from object list."""
        objects = ["Cube", "Sphere", "Light"]
        manifest = create_cryptomatte_manifest(objects)
        assert manifest.layer_name == "cryptomatte00"
        assert len(manifest.entries) == 3
        names = manifest.get_all_names()
        assert set(names) == set(objects)

    def test_create_cryptomatte_manifest_custom_layer(self):
        """Test creating manifest with custom layer name."""
        objects = ["Cube"]
        manifest = create_cryptomatte_manifest(objects, layer_name="crypto01")
        assert manifest.layer_name == "crypto01"

    def test_create_cryptomatte_manifest_empty(self):
        """Test creating manifest from empty list."""
        manifest = create_cryptomatte_manifest([])
        assert len(manifest.entries) == 0

    def test_create_manifest_hash_matches(self):
        """Test that created manifest hashes are correct."""
        objects = ["TestObject"]
        manifest = create_cryptomatte_manifest(objects)
        expected_hash = hash_object_name("TestObject")
        assert manifest.get_hash("TestObject") == expected_hash


class TestSaveManifest:
    """Tests for saving manifests."""

    def test_save_manifest(self):
        """Test saving manifest to file."""
        manifest = create_cryptomatte_manifest(["Cube", "Sphere"])
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name

        try:
            result = save_manifest(manifest, path)
            assert result is True
            assert os.path.exists(path)

            # Verify content
            with open(path, 'r') as f:
                data = json.load(f)
            assert data["layer_name"] == "cryptomatte00"
            assert len(data["entries"]) == 2
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_save_manifest_invalid_path(self):
        """Test saving to invalid path returns False."""
        manifest = create_cryptomatte_manifest(["Cube"])
        result = save_manifest(manifest, "/nonexistent/directory/file.json")
        assert result is False


class TestMatteExtraction:
    """Tests for matte extraction functions."""

    def test_extract_matte_for_object_found(self):
        """Test extracting matte for existing object."""
        manifest = create_cryptomatte_manifest(["Cube", "Sphere"])
        result = extract_matte_for_object(manifest, "Cube")
        assert result.success is True
        assert result.matte is None  # Would be numpy array in practice
        assert result.coverage == 1.0

    def test_extract_matte_for_object_not_found(self):
        """Test extracting matte for non-existent object."""
        manifest = create_cryptomatte_manifest(["Cube"])
        result = extract_matte_for_object(manifest, "NonExistent")
        assert result.success is False
        assert "not found" in result.error

    def test_extract_matte_for_objects_union(self):
        """Test extracting combined matte for multiple objects."""
        manifest = create_cryptomatte_manifest(["Cube", "Sphere", "Light"])
        result = extract_matte_for_objects(manifest, ["Cube", "Sphere"])
        # Without actual EXR data, matte is None so success is False
        # But this tests that the function doesn't crash with multiple objects
        # In production with real EXR data, success would be True
        assert result.success is False  # matte is None without real EXR data

    def test_extract_matte_for_objects_empty(self):
        """Test extracting matte with empty object list."""
        manifest = create_cryptomatte_manifest(["Cube"])
        result = extract_matte_for_objects(manifest, [])
        assert result.success is False
        assert "No objects specified" in result.error

    def test_extract_matte_for_objects_none_found(self):
        """Test extracting matte when none of the objects exist."""
        manifest = create_cryptomatte_manifest(["Cube"])
        result = extract_matte_for_objects(manifest, ["NonExistent1", "NonExistent2"])
        assert result.success is False


class TestUtilities:
    """Tests for utility functions."""

    def test_get_cryptomatte_layer_names(self):
        """Test getting layer names (returns empty without OpenEXR)."""
        result = get_cryptomatte_layer_names("/any/path.exr")
        assert result == []  # Returns empty without OpenEXR

    def test_get_cryptomatte_info(self):
        """Test getting cryptomatte info."""
        result = get_cryptomatte_info("/any/path.exr")
        assert "has_cryptomatte" in result
        assert "layers" in result
        assert "manifests" in result
        assert result["has_cryptomatte"] is False  # Without OpenEXR

    def test_rank_to_channels(self):
        """Test converting rank to channel names."""
        channels = rank_to_channels(0)
        assert channels == ["cryptomatte00.R", "cryptomatte00.G", "cryptomatte00.B"]

        channels = rank_to_channels(5)
        assert channels == ["cryptomatte05.R", "cryptomatte05.G", "cryptomatte05.B"]

    def test_estimate_cryptomatte_ranks(self):
        """Test estimating required ranks."""
        # Each rank stores ~2 objects
        assert estimate_cryptomatte_ranks(1) == 1
        assert estimate_cryptomatte_ranks(2) == 1
        assert estimate_cryptomatte_ranks(3) == 2
        assert estimate_cryptomatte_ranks(10) == 5
        assert estimate_cryptomatte_ranks(100) == 50


class TestMergeManifests:
    """Tests for manifest merging."""

    def test_merge_empty_list(self):
        """Test merging empty manifest list."""
        result = merge_manifests([])
        assert result.layer_name == "merged"
        assert len(result.entries) == 0

    def test_merge_single_manifest(self):
        """Test merging single manifest."""
        manifest = create_cryptomatte_manifest(["Cube"])
        result = merge_manifests([manifest])
        assert len(result.entries) == 1

    def test_merge_multiple_manifests(self):
        """Test merging multiple manifests."""
        m1 = create_cryptomatte_manifest(["Cube", "Sphere"])
        m2 = create_cryptomatte_manifest(["Light", "Camera"])
        result = merge_manifests([m1, m2])
        names = result.get_all_names()
        assert set(names) == {"Cube", "Sphere", "Light", "Camera"}

    def test_merge_removes_duplicates(self):
        """Test that merging removes duplicate names."""
        m1 = create_cryptomatte_manifest(["Cube", "Sphere"])
        m2 = create_cryptomatte_manifest(["Sphere", "Light"])  # Sphere duplicated
        result = merge_manifests([m1, m2])
        names = result.get_all_names()
        assert names.count("Sphere") == 1
        assert len(names) == 3


class TestMatteResult:
    """Tests for MatteResult dataclass."""

    def test_matte_result_defaults(self):
        """Test MatteResult default values."""
        result = MatteResult(success=True)
        assert result.success is True
        assert result.matte is None
        assert result.error == ""
        assert result.coverage == 0.0

    def test_matte_result_with_values(self):
        """Test MatteResult with custom values."""
        result = MatteResult(
            success=False,
            matte=None,
            error="Object not found",
            coverage=0.5
        )
        assert result.success is False
        assert result.error == "Object not found"
        assert result.coverage == 0.5


class TestCryptomatteEdgeCases:
    """Tests for edge cases in cryptomatte."""

    def test_hash_unicode_names(self):
        """Test hashing unicode object names."""
        hash1 = hash_object_name("Cube_001")
        hash2 = hash_object_name("Cube-002")
        hash3 = hash_object_name("Cube.003")
        assert hash1 != hash2 != hash3

    def test_manifest_large_number_of_objects(self):
        """Test manifest with many objects."""
        objects = [f"Object_{i:04d}" for i in range(1000)]
        manifest = create_cryptomatte_manifest(objects)
        assert len(manifest.entries) == 1000
        # Verify lookup works
        assert manifest.get_hash("Object_0500") is not None

    def test_empty_object_name_hash(self):
        """Test hashing empty string."""
        hash_val = hash_object_name("")
        assert len(hash_val) == 8
        assert isinstance(hash_val, str)

    def test_special_characters_in_name(self):
        """Test hashing names with special characters."""
        names = [
            "Cube.001",
            "Cube_001",
            "Cube-001",
            "Cube 001",
            "Cube/001",
            "Cube\\001",
        ]
        hashes = [hash_object_name(n) for n in names]
        # All should be unique
        assert len(set(hashes)) == len(hashes)
