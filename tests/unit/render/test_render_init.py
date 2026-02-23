"""
Tests for render/__init__.py module.

Tests the main exports and module structure.
"""

import pytest


class TestRenderModuleInit:
    """Tests for render module __init__.py."""

    def test_module_imports(self):
        """Test that the render module can be imported."""
        from lib.render import __version__, __all__
        assert __version__ == "0.1.0"
        assert isinstance(__all__, list)

    def test_exports_list(self):
        """Test that __all__ contains expected exports."""
        from lib.render import __all__

        expected = [
            # Profiles
            "RenderProfile",
            "get_profile",
            "get_all_profiles",
            "apply_profile",
            "create_profile_from_scene",
            "PROFILES",
            # Cycles
            "CyclesConfig",
            "get_cycles_preset",
            "apply_cycles_config",
            "configure_optix",
            "configure_hip",
            "configure_metal",
            "configure_cpu",
            "CYCLES_PRESETS",
            # EEVEE Next
            "EEVEENextConfig",
            "get_eevee_preset",
            "apply_eevee_config",
            "configure_raytracing",
            "configure_taa",
            "EEVEE_PRESETS",
        ]

        for item in expected:
            assert item in __all__, f"{item} not in __all__"


class TestRenderModuleImports:
    """Test importing specific items from the render module."""

    def test_import_profile_components(self):
        """Test importing profile components."""
        from lib.render import (
            RenderProfile,
            get_profile,
            get_all_profiles,
            apply_profile,
            create_profile_from_scene,
            PROFILES,
        )
        from lib.render.profiles import RenderEngine, QualityTier

        assert RenderProfile is not None
        assert RenderEngine is not None
        assert QualityTier is not None
        assert callable(get_profile)
        assert callable(get_all_profiles)
        assert callable(apply_profile)
        assert callable(create_profile_from_scene)
        assert isinstance(PROFILES, dict)

    def test_import_cycles_components(self):
        """Test importing Cycles components."""
        from lib.render import (
            CyclesConfig,
            get_cycles_preset,
            apply_cycles_config,
            configure_optix,
            configure_hip,
            configure_metal,
            configure_cpu,
            CYCLES_PRESETS,
        )
        from lib.render.cycles_config import DeviceType, DenoiserType

        assert CyclesConfig is not None
        assert DeviceType is not None
        assert DenoiserType is not None
        assert callable(get_cycles_preset)
        assert callable(apply_cycles_config)
        assert callable(configure_optix)
        assert callable(configure_hip)
        assert callable(configure_metal)
        assert callable(configure_cpu)
        assert isinstance(CYCLES_PRESETS, dict)

    def test_import_eevee_components(self):
        """Test importing EEVEE components."""
        from lib.render import (
            EEVEENextConfig,
            get_eevee_preset,
            apply_eevee_config,
            configure_raytracing,
            configure_taa,
            EEVEE_PRESETS,
        )
        from lib.render.eevee_config import RaytracingMethod, ShadowMethod

        assert EEVEENextConfig is not None
        assert RaytracingMethod is not None
        assert ShadowMethod is not None
        assert callable(get_eevee_preset)
        assert callable(apply_eevee_config)
        assert callable(configure_raytracing)
        assert callable(configure_taa)
        assert isinstance(EEVEE_PRESETS, dict)


class TestRenderModuleSubmodules:
    """Test importing submodules directly."""

    def test_import_profiles_module(self):
        """Test importing profiles module directly."""
        from lib.render.profiles import RenderProfile, get_profile
        assert RenderProfile is not None
        assert callable(get_profile)

    def test_import_cycles_config_module(self):
        """Test importing cycles_config module directly."""
        from lib.render.cycles_config import CyclesConfig, get_cycles_preset
        assert CyclesConfig is not None
        assert callable(get_cycles_preset)

    def test_import_eevee_config_module(self):
        """Test importing eevee_config module directly."""
        from lib.render.eevee_config import EEVEENextConfig, get_eevee_preset
        assert EEVEENextConfig is not None
        assert callable(get_eevee_preset)


class TestRenderModuleStructure:
    """Tests for render module directory structure."""

    def test_profiles_file_exists(self):
        """Test that profiles.py exists."""
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        profiles_path = os.path.join(base_path, 'lib', 'render', 'profiles.py')
        assert os.path.isfile(profiles_path), f"profiles.py not found at {profiles_path}"

    def test_cycles_config_file_exists(self):
        """Test that cycles_config.py exists."""
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        cycles_path = os.path.join(base_path, 'lib', 'render', 'cycles_config.py')
        assert os.path.isfile(cycles_path), f"cycles_config.py not found at {cycles_path}"

    def test_eevee_config_file_exists(self):
        """Test that eevee_config.py exists."""
        import os
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        eevee_path = os.path.join(base_path, 'lib', 'render', 'eevee_config.py')
        assert os.path.isfile(eevee_path), f"eevee_config.py not found at {eevee_path}"


class TestRenderIntegration:
    """Integration tests for render module components."""

    def test_profile_to_cycles_workflow(self):
        """Test workflow from profile to Cycles configuration."""
        from lib.render import (
            get_profile,
            get_cycles_preset,
            RenderProfile,
            CyclesConfig,
        )

        # Get a production profile
        profile = get_profile("cycles_production")
        assert profile.engine == "CYCLES"

        # Get matching Cycles preset
        cycles_config = get_cycles_preset("production")
        assert cycles_config.name == "production"

        # Verify they have compatible settings
        assert profile.denoise == cycles_config.use_denoising

    def test_profile_to_eevee_workflow(self):
        """Test workflow from profile to EEVEE configuration."""
        from lib.render import (
            get_profile,
            get_eevee_preset,
            RenderProfile,
            EEVEENextConfig,
        )

        # Get an EEVEE production profile
        profile = get_profile("eevee_production")
        assert profile.engine == "BLENDER_EEVEE_NEXT"

        # Get matching EEVEE preset
        eevee_config = get_eevee_preset("production")
        assert eevee_config.name == "production"

        # Verify they have compatible settings
        assert profile.metadata.get("taa_samples") == eevee_config.taa_samples

    def test_custom_profile_creation(self):
        """Test creating custom profiles."""
        from lib.render import RenderProfile

        custom = RenderProfile(
            name="custom_test",
            engine="CYCLES",
            resolution=(2560, 1440),
            samples=256,
            denoise=True,
            motion_blur=True,
            metadata={"custom_setting": "value"},
        )

        assert custom.name == "custom_test"
        assert custom.resolution == (2560, 1440)
        assert custom.metadata["custom_setting"] == "value"

    def test_custom_cycles_config_creation(self):
        """Test creating custom Cycles configuration."""
        from lib.render import CyclesConfig

        custom = CyclesConfig(
            name="custom_cycles",
            samples=512,
            adaptive_sampling=True,
            adaptive_threshold=0.005,
            use_denoising=True,
            denoiser="OPTIX",
            max_bounces=16,
        )

        assert custom.name == "custom_cycles"
        assert custom.samples == 512
        assert custom.adaptive_threshold == 0.005

    def test_custom_eevee_config_creation(self):
        """Test creating custom EEVEE configuration."""
        from lib.render import EEVEENextConfig

        custom = EEVEENextConfig(
            name="custom_eevee",
            taa_samples=96,
            use_raytracing=True,
            raytracing_method="RAYTRACED",
            raytracing_samples=6,
            gtao_quality=0.9,
        )

        assert custom.name == "custom_eevee"
        assert custom.taa_samples == 96
        assert custom.raytracing_method == "RAYTRACED"
