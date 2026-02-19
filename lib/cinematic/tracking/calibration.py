"""
Camera Calibration Module - Camera Profiles and Lens Distortion Models

Provides device-specific camera profiles with lens distortion models
for accurate camera tracking and matching.

Supports iPhone, cinema cameras (RED, ARRI, Blackmagic), and custom profiles.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import math

from .types import CameraProfile


@dataclass
class DistortionCoefficients:
    """
    Lens distortion coefficients.

    Supports Brown-Conrady and simple radial distortion models.

    Attributes:
        k1, k2, k3: Radial distortion coefficients
        p1, p2: Tangential distortion coefficients
        cx, cy: Principal point offset (normalized)
    """
    k1: float = 0.0
    k2: float = 0.0
    k3: float = 0.0
    p1: float = 0.0
    p2: float = 0.0
    cx: float = 0.0
    cy: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "k1": self.k1,
            "k2": self.k2,
            "k3": self.k3,
            "p1": self.p1,
            "p2": self.p2,
            "cx": self.cx,
            "cy": self.cy,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DistortionCoefficients:
        return cls(
            k1=data.get("k1", 0.0),
            k2=data.get("k2", 0.0),
            k3=data.get("k3", 0.0),
            p1=data.get("p1", 0.0),
            p2=data.get("p2", 0.0),
            cx=data.get("cx", 0.0),
            cy=data.get("cy", 0.0),
        )

    @classmethod
    def from_profile(cls, profile: CameraProfile) -> DistortionCoefficients:
        """Create from CameraProfile."""
        return cls(
            k1=profile.k1,
            k2=profile.k2,
            k3=profile.k3,
            p1=profile.p1,
            p2=profile.p2,
            cx=profile.cx,
            cy=profile.cy,
        )


class LensDistortion:
    """
    Lens distortion utility class.

    Provides methods for applying and removing lens distortion
    using various models.
    """

    @staticmethod
    def apply_brown_conrady(
        x: float,
        y: float,
        coeffs: DistortionCoefficients,
    ) -> Tuple[float, float]:
        """
        Apply Brown-Conrady distortion to normalized coordinates.

        Args:
            x, y: Normalized coordinates (centered at 0, 0)
            coeffs: Distortion coefficients

        Returns:
            Distorted (x, y) coordinates
        """
        r2 = x * x + y * y
        r4 = r2 * r2
        r6 = r4 * r2

        # Radial distortion
        radial = 1 + coeffs.k1 * r2 + coeffs.k2 * r4 + coeffs.k3 * r6

        # Tangential distortion
        xy = x * y
        tx = 2 * coeffs.p1 * xy + coeffs.p2 * (r2 + 2 * x * x)
        ty = coeffs.p1 * (r2 + 2 * y * y) + 2 * coeffs.p2 * xy

        # Apply distortion
        x_dist = x * radial + tx
        y_dist = y * radial + ty

        return x_dist, y_dist

    @staticmethod
    def remove_brown_conrady(
        x_dist: float,
        y_dist: float,
        coeffs: DistortionCoefficients,
        iterations: int = 10,
    ) -> Tuple[float, float]:
        """
        Remove Brown-Conrady distortion (undistort).

        Uses iterative method to invert the distortion.

        Args:
            x_dist, y_dist: Distorted normalized coordinates
            coeffs: Distortion coefficients
            iterations: Number of iterations for convergence

        Returns:
            Undistorted (x, y) coordinates
        """
        # Start with distorted coordinates as initial guess
        x = x_dist
        y = y_dist

        for _ in range(iterations):
            # Calculate what the distorted coords would be
            x_calc, y_calc = LensDistortion.apply_brown_conrady(x, y, coeffs)

            # Adjust guess
            x = x + (x_dist - x_calc)
            y = y + (y_dist - y_calc)

        return x, y

    @staticmethod
    def apply_simple_radial(
        x: float,
        y: float,
        k1: float,
        k2: float = 0.0,
    ) -> Tuple[float, float]:
        """
        Apply simple radial distortion.

        Args:
            x, y: Normalized coordinates
            k1, k2: Radial distortion coefficients

        Returns:
            Distorted (x, y) coordinates
        """
        r2 = x * x + y * y
        distortion = 1 + k1 * r2 + k2 * r2 * r2
        return x * distortion, y * distortion


class CameraProfileManager:
    """
    Manager for camera device profiles.

    Provides profile loading, lookup, and calibration utilities.
    """

    # Built-in profiles for common cameras
    BUILTIN_PROFILES: Dict[str, CameraProfile] = {
        # iPhone Profiles
        "iphone_14_pro_main": CameraProfile(
            name="iPhone 14 Pro Main",
            manufacturer="Apple",
            model="iPhone 14 Pro",
            sensor_width=7.57,
            sensor_height=5.68,
            focal_length=6.86,
            crop_factor=4.76,
            distortion_model="brown_conrady",
            k1=-0.0250,
            k2=0.0125,
            k3=0.0000,
            p1=0.0002,
            p2=-0.0001,
            cx=0.0012,
            cy=-0.0008,
        ),
        "iphone_14_pro_ultra_wide": CameraProfile(
            name="iPhone 14 Pro Ultra Wide",
            manufacturer="Apple",
            model="iPhone 14 Pro",
            sensor_width=5.32,
            sensor_height=4.0,
            focal_length=2.55,
            crop_factor=6.77,
            distortion_model="brown_conrady",
            k1=-0.0850,
            k2=0.0450,
            k3=-0.0120,
            p1=0.0010,
            p2=-0.0005,
            cx=0.0025,
            cy=-0.0015,
        ),
        "iphone_15_pro_main": CameraProfile(
            name="iPhone 15 Pro Main",
            manufacturer="Apple",
            model="iPhone 15 Pro",
            sensor_width=8.28,
            sensor_height=6.22,
            focal_length=6.78,
            crop_factor=4.35,
            distortion_model="brown_conrady",
            k1=-0.0220,
            k2=0.0108,
            k3=0.0000,
            p1=0.00015,
            p2=-0.00008,
            cx=0.0010,
            cy=-0.0006,
        ),
        "iphone_15_pro_ultra_wide": CameraProfile(
            name="iPhone 15 Pro Ultra Wide",
            manufacturer="Apple",
            model="iPhone 15 Pro",
            sensor_width=5.35,
            sensor_height=4.02,
            focal_length=2.55,
            crop_factor=6.73,
            distortion_model="brown_conrady",
            k1=-0.0820,
            k2=0.0420,
            k3=-0.0110,
            p1=0.0009,
            p2=-0.0004,
            cx=0.0022,
            cy=-0.0013,
        ),

        # RED Cameras
        "red_komodo": CameraProfile(
            name="RED Komodo",
            manufacturer="RED",
            model="Komodo 6K",
            sensor_width=27.03,
            sensor_height=14.26,
            focal_length=50.0,
            crop_factor=1.33,
            distortion_model="brown_conrady",
            k1=-0.0080,
            k2=0.0035,
            k3=0.0000,
        ),
        "red_v_raptor": CameraProfile(
            name="RED V-Raptor",
            manufacturer="RED",
            model="V-Raptor 8K",
            sensor_width=40.96,
            sensor_height=21.60,
            focal_length=50.0,
            crop_factor=0.88,
            distortion_model="brown_conrady",
            k1=-0.0060,
            k2=0.0025,
            k3=0.0000,
        ),

        # ARRI Cameras
        "arri_alexa_mini_lf": CameraProfile(
            name="ARRI Alexa Mini LF",
            manufacturer="ARRI",
            model="Alexa Mini LF",
            sensor_width=36.70,
            sensor_height=25.54,
            focal_length=50.0,
            crop_factor=0.98,
            distortion_model="brown_conrady",
            k1=-0.0040,
            k2=0.0018,
            k3=0.0000,
        ),
        "arri_alexa_35": CameraProfile(
            name="ARRI Alexa 35",
            manufacturer="ARRI",
            model="Alexa 35",
            sensor_width=27.99,
            sensor_height=19.22,
            focal_length=50.0,
            crop_factor=1.29,
            distortion_model="brown_conrady",
            k1=-0.0035,
            k2=0.0015,
            k3=0.0000,
        ),

        # Blackmagic Cameras
        "blackmagic_ursa_12k": CameraProfile(
            name="Blackmagic URSA Mini Pro 12K",
            manufacturer="Blackmagic Design",
            model="URSA Mini Pro 12K",
            sensor_width=27.03,
            sensor_height=14.25,
            focal_length=50.0,
            crop_factor=1.33,
            distortion_model="brown_conrady",
            k1=-0.0100,
            k2=0.0045,
            k3=0.0000,
        ),
        "blackmagic_pocket_6k": CameraProfile(
            name="Blackmagic Pocket 6K Pro",
            manufacturer="Blackmagic Design",
            model="Pocket Cinema Camera 6K Pro",
            sensor_width=23.10,
            sensor_height=12.99,
            focal_length=50.0,
            crop_factor=1.56,
            distortion_model="brown_conrady",
            k1=-0.0120,
            k2=0.0055,
            k3=0.0000,
        ),

        # Sony Cameras
        "sony_a7s_iii": CameraProfile(
            name="Sony A7S III",
            manufacturer="Sony",
            model="Alpha 7S III",
            sensor_width=35.60,
            sensor_height=23.80,
            focal_length=50.0,
            crop_factor=1.01,
            distortion_model="brown_conrady",
            k1=-0.0055,
            k2=0.0024,
            k3=0.0000,
        ),
        "sony_fx6": CameraProfile(
            name="Sony FX6",
            manufacturer="Sony",
            model="FX6",
            sensor_width=35.60,
            sensor_height=23.80,
            focal_length=50.0,
            crop_factor=1.01,
            distortion_model="brown_conrady",
            k1=-0.0055,
            k2=0.0024,
            k3=0.0000,
        ),

        # Canon Cameras
        "canon_eos_r5": CameraProfile(
            name="Canon EOS R5",
            manufacturer="Canon",
            model="EOS R5",
            sensor_width=36.00,
            sensor_height=24.00,
            focal_length=50.0,
            crop_factor=1.0,
            distortion_model="brown_conrady",
            k1=-0.0050,
            k2=0.0022,
            k3=0.0000,
        ),
        "canon_c70": CameraProfile(
            name="Canon C70",
            manufacturer="Canon",
            model="Cinema EOS C70",
            sensor_width=26.20,
            sensor_height=13.80,
            focal_length=50.0,
            crop_factor=1.37,
            distortion_model="brown_conrady",
            k1=-0.0070,
            k2=0.0032,
            k3=0.0000,
        ),

        # Drone Cameras
        "dji_mavic_3_pro": CameraProfile(
            name="DJI Mavic 3 Pro",
            manufacturer="DJI",
            model="Mavic 3 Pro",
            sensor_width=17.30,
            sensor_height=13.00,
            focal_length=12.29,
            crop_factor=2.08,
            distortion_model="brown_conrady",
            k1=-0.0350,
            k2=0.0180,
            k3=-0.0050,
            p1=0.0003,
            p2=-0.0002,
            cx=0.0015,
            cy=-0.0010,
        ),

        # Action Cameras
        "gopro_hero_12": CameraProfile(
            name="GoPro Hero 12",
            manufacturer="GoPro",
            model="Hero 12 Black",
            sensor_width=6.17,
            sensor_height=4.55,
            focal_length=2.92,
            crop_factor=5.83,
            distortion_model="brown_conrady",
            k1=-0.1200,
            k2=0.0650,
            k3=-0.0250,
            p1=0.0010,
            p2=-0.0008,
            cx=0.0050,
            cy=-0.0035,
        ),

        # Generic Profile
        "generic": CameraProfile(
            name="Generic Full Frame",
            manufacturer="Generic",
            model="35mm Full Frame",
            sensor_width=36.0,
            sensor_height=24.0,
            focal_length=50.0,
            crop_factor=1.0,
            distortion_model="none",
        ),
    }

    def __init__(self, custom_profiles_path: Optional[str] = None):
        """
        Initialize profile manager.

        Args:
            custom_profiles_path: Optional path to custom profiles YAML
        """
        self._profiles = dict(self.BUILTIN_PROFILES)
        self._custom_profiles_path = custom_profiles_path

        if custom_profiles_path:
            self.load_custom_profiles(custom_profiles_path)

    def get_profile(self, name: str) -> Optional[CameraProfile]:
        """
        Get camera profile by name.

        Args:
            name: Profile name (case-insensitive partial match)

        Returns:
            CameraProfile if found, None otherwise
        """
        # Try exact match first
        if name in self._profiles:
            return self._profiles[name]

        # Try case-insensitive match
        name_lower = name.lower()
        for key, profile in self._profiles.items():
            if key.lower() == name_lower:
                return profile
            if name_lower in profile.name.lower():
                return profile
            if name_lower in profile.manufacturer.lower():
                return profile
            if name_lower in profile.model.lower():
                return profile

        return None

    def list_profiles(self, manufacturer: Optional[str] = None) -> List[CameraProfile]:
        """
        List available profiles, optionally filtered by manufacturer.

        Args:
            manufacturer: Optional manufacturer filter

        Returns:
            List of matching profiles
        """
        profiles = list(self._profiles.values())

        if manufacturer:
            manufacturer_lower = manufacturer.lower()
            profiles = [
                p for p in profiles
                if manufacturer_lower in p.manufacturer.lower()
            ]

        return sorted(profiles, key=lambda p: (p.manufacturer, p.model))

    def list_manufacturers(self) -> List[str]:
        """Get list of unique manufacturers."""
        manufacturers = set(p.manufacturer for p in self._profiles.values())
        return sorted(manufacturers)

    def add_profile(self, profile: CameraProfile) -> None:
        """
        Add a custom profile.

        Args:
            profile: CameraProfile to add
        """
        key = profile.name.lower().replace(" ", "_").replace("-", "_")
        self._profiles[key] = profile

    def remove_profile(self, name: str) -> bool:
        """
        Remove a profile.

        Args:
            name: Profile name to remove

        Returns:
            True if removed, False if not found
        """
        if name in self._profiles:
            del self._profiles[name]
            return True
        return False

    def load_custom_profiles(self, path: str) -> int:
        """
        Load custom profiles from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Number of profiles loaded
        """
        try:
            import yaml

            with open(path, "r") as f:
                data = yaml.safe_load(f)

            if not data or "camera_profiles" not in data:
                return 0

            count = 0
            for key, profile_data in data["camera_profiles"].items():
                profile = CameraProfile.from_dict(profile_data)
                self._profiles[key] = profile
                count += 1

            return count

        except Exception:
            return 0

    def save_profiles(self, path: str, include_builtin: bool = False) -> bool:
        """
        Save profiles to YAML file.

        Args:
            path: Output path
            include_builtin: Include built-in profiles

        Returns:
            True if successful
        """
        try:
            import yaml

            if include_builtin:
                profiles_to_save = self._profiles
            else:
                # Only save profiles not in BUILTIN_PROFILES
                profiles_to_save = {
                    k: v for k, v in self._profiles.items()
                    if k not in self.BUILTIN_PROFILES
                }

            data = {
                "camera_profiles": {
                    k: v.to_dict() for k, v in profiles_to_save.items()
                }
            }

            with open(path, "w") as f:
                yaml.dump(data, f, default_flow_style=False)

            return True

        except Exception:
            return False

    def get_distortion_coefficients(self, name: str) -> Optional[DistortionCoefficients]:
        """
        Get distortion coefficients for a profile.

        Args:
            name: Profile name

        Returns:
            DistortionCoefficients if profile found, None otherwise
        """
        profile = self.get_profile(name)
        if profile:
            return DistortionCoefficients.from_profile(profile)
        return None

    def apply_distortion(
        self,
        x: float,
        y: float,
        profile_name: str,
    ) -> Tuple[float, float]:
        """
        Apply lens distortion to coordinates.

        Args:
            x, y: Normalized coordinates (-1 to 1, centered)
            profile_name: Camera profile name

        Returns:
            Distorted coordinates
        """
        coeffs = self.get_distortion_coefficients(profile_name)
        if coeffs:
            return LensDistortion.apply_brown_conrady(x, y, coeffs)
        return x, y

    def remove_distortion(
        self,
        x: float,
        y: float,
        profile_name: str,
    ) -> Tuple[float, float]:
        """
        Remove lens distortion from coordinates.

        Args:
            x, y: Distorted normalized coordinates
            profile_name: Camera profile name

        Returns:
            Undistorted coordinates
        """
        coeffs = self.get_distortion_coefficients(profile_name)
        if coeffs:
            return LensDistortion.remove_brown_conrady(x, y, coeffs)
        return x, y

    def find_matching_profile(
        self,
        sensor_width: float,
        sensor_height: float,
        tolerance: float = 0.5,
    ) -> Optional[CameraProfile]:
        """
        Find profile matching sensor dimensions.

        Args:
            sensor_width: Sensor width in mm
            sensor_height: Sensor height in mm
            tolerance: Tolerance in mm for matching

        Returns:
            Best matching profile or None
        """
        best_match = None
        best_diff = float("inf")

        for profile in self._profiles.values():
            diff = (
                abs(profile.sensor_width - sensor_width) +
                abs(profile.sensor_height - sensor_height)
            )

            if diff < best_diff and diff < tolerance * 2:
                best_diff = diff
                best_match = profile

        return best_match


# Global profile manager instance
_profile_manager: Optional[CameraProfileManager] = None


def get_profile_manager() -> CameraProfileManager:
    """Get or create global profile manager instance."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = CameraProfileManager()
    return _profile_manager


def get_camera_profile(name: str) -> Optional[CameraProfile]:
    """Convenience function to get a camera profile."""
    return get_profile_manager().get_profile(name)
