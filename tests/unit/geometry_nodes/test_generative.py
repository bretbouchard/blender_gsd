"""
Tests for the Generative Modeling Module (Phase 7)

Verifies:
- MultiLayerShell
- FacetedRemesh
- GenerativeShell
- create_generative_shell function
"""

from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import List, Optional, Any

from lib.geometry_nodes.generative import (
    MultiLayerShell,
    ShellLayer,
    FacetedRemesh,
    GenerativeShell,
    create_generative_shell,
)


if TYPE_CHECKING:
    import bpy
else:
    bpy = None  # type: ignore


    Node = Any


@pytest.fixture
def shell_layer():
    """Test ShellLayer dataclass."""
    layer = ShellLayer()
    assert layer.scale == 1.0
    assert layer.offset == 0.0
    assert layer.material is None
    assert layer.solidify == 0.0
    assert layer.rotation == (0.0, 0.0, 0.0)
    assert layer.attribute_transfer == []

    with pytest.raises(ValueError):
        ShellLayer(scale=-1.0)


    with pytest.raises(ValueError):
        ShellLayer(scale=2.0, offset=-5.0)


    # Test defaults
    layer = ShellLayer(scale=0.5, offset=0.02)
    assert layer.scale == 0.5
    assert layer.offset == 0.02


    # Test attribute_transfer default
    assert layer.attribute_transfer == []
    # Test custom attribute_transfer
    layer2 = ShellLayer(attribute_transfer=["uv", "normal"])
    assert layer.attribute_transfer == ["uv", "normal"]


    # Test defaults with custom values
    layer3 = ShellLayer(
        scale=0.95,
        offset=-0.02,
        material="test_material",
        solidify=0.1,
        rotation=(45.0, 0.0, 0.0),
        attribute_transfer=["custom"]
    )
    assert layer3.scale == 0.95
    assert layer3.offset == -0.02
    assert layer3.material == "test_material"
    assert layer3.solidify == 0.1
    assert layer3.rotation == (45.0, 0.0, 0.0)
    assert layer3.attribute_transfer == ["custom"]


@pytest.fixture
def multi_layer_shell():
    """Test MultiLayerShell class."""
    shell = MultiLayerShell(builder=None)  # type: ignore
    assert shell.layers == []
    assert shell._input_mesh is None
    with pytest.raises(ValueError):
        shell.build()
    shell.set_input_mesh("mock_mesh")
    assert shell._input_mesh == "mock_mesh"


@pytest.fixture
def multi_layer_shell_add_layer():
    """Test add_layer method."""
    shell = MultiLayerShell(builder=None)  # type: ignore
    # Test method chaining
    result = shell.add_layer(scale=0.95, offset=-0.02)
    assert result is shell
    assert len(shell.layers) == 1
    assert shell.layers[0].scale == 0.95
    assert shell.layers[0].offset == -0.02
    # Add another layer
    shell.add_layer(scale=1.0, material="outer")
    assert len(shell.layers) == 2
    assert shell.layers[1].scale == 1.0
    assert shell.layers[1].material == "outer"
    # Test scale clamping
    shell.add_layer(scale=-0.5)
    assert shell.layers[2].scale == 0.001
    # Test offset clamping
    shell.add_layer(offset=-1.0)
    assert shell.layers[3].offset == 0.0


@pytest.fixture
def multi_layer_shell_set_input_mesh():
    """Test set_input_mesh method."""
    shell = MultiLayerShell(builder=None)  # type: ignore
    result = shell.set_input_mesh("mock_mesh")
    assert result is shell
    assert shell._input_mesh == "mock_mesh"


@pytest.fixture
def faceted_remesh():
    """Test FacetedRemesh class."""
    remesh = FacetedRemesh(builder=None)  # type: ignore
    assert remesh._voxel_size == 0.05
    assert remesh._preserve_sharp_edges is False
    assert remesh._edge_angle == 30.0
    assert remesh._store_normals is True
    assert remesh._normal_attr_name == "faceted_normal"
    assert remesh._input_mesh is None
    with pytest.raises(ValueError):
        remesh.build()
    remesh.set_input_mesh("mock_mesh")
    assert remesh._input_mesh == "mock_mesh"
@pytest.fixture
def faceted_remesh_set_voxel_size():
    """Test set_voxel_size method."""
    remesh = FacetedRemesh(builder=None)  # type: ignore
    result = remesh.set_voxel_size(0.1)
    assert result is remesh
    assert remesh._voxel_size == 0.1
    # Test clamping
    remesh.set_voxel_size(0.0001)
    assert remesh._voxel_size == 0.001
@pytest.fixture
def faceted_remesh_preserve_edges():
    """Test preserve_edges method."""
    remesh = FacetedRemesh(builder=None)  # type: ignore
    result = remesh.preserve_edges(angle=45.0)
    assert result is remesh
    assert remesh._preserve_sharp_edges is True
    assert remesh._edge_angle == 45.0
    # Test angle clamping
    remesh.preserve_edges(angle=200.0)
    assert remesh._edge_angle == 180.0
    remesh.preserve_edges(angle=-10.0)
    assert remesh._edge_angle == 0.0
@pytest.fixture
def faceted_remesh_store_normals():
    """Test store_normals method."""
    remesh = FacetedRemesh(builder=None)  # type: ignore
    result = remesh.store_normals(False)
    assert result is remesh
    assert remesh._store_normals is False
@pytest.fixture
def faceted_remesh_set_normal_attribute_name():
    """Test set_normal_attribute_name method."""
    remesh = FacetedRemesh(builder=None)  # type: ignore
    result = remesh.set_normal_attribute_name("custom_normal")
    assert result is remesh
    assert remesh._normal_attr_name == "custom_normal"
@pytest.fixture
def generative_shell():
    """Test GenerativeShell class."""
    shell = GenerativeShell(builder=None)  # type: ignore
    assert shell._noise_scale == {}
    assert shell._rotation_variation == {}
    assert shell._scale_variation == {}
@pytest.fixture
def generative_shell_add_noise():
    """Test add_noise method."""
    shell = GenerativeShell(builder=None)  # type: ignore
    result = shell.add_noise(0.05, layer_index=0)
    assert result is shell
    assert shell._noise_scale[0] == 0.05
    # Test default layer index (-1)
    shell.add_noise(0.02)
    assert shell._noise_scale[-1] == 0.02
@pytest.fixture
def generative_shell_add_rotation_variation():
    """Test add_rotation_variation method."""
    shell = GenerativeShell(builder=None)  # type: ignore
    result = shell.add_rotation_variation(15.0, layer_index=0)
    assert result is shell
    assert shell._rotation_variation[0] == 15.0
@pytest.fixture
def generative_shell_add_scale_variation():
    """Test add_scale_variation method."""
    shell = GenerativeShell(builder=None)  # type: ignore
    result = shell.add_scale_variation(0.1, layer_index=0)
    assert result is shell
    assert shell._scale_variation[0] == 0.1
@pytest.fixture
def create_generative_shell_func():
    """Test create_generative_shell convenience function."""
    # This would normally need a NodeTreeBuilder, but we testing without Blender
    # We can test the configuration logic
    shell = GenerativeShell(builder=None)  # type: ignore
    for i in range(3):
        shell.add_layer(scale=1.0 - i * 0.02, offset=-i * 0.01)
    assert len(shell.layers) == 3
