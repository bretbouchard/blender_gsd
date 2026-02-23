"""
HDRI Asset Downloader

Downloads free HDRI environment maps from Poly Haven.
These provide realistic global illumination for scenes.

Usage:
    python -m lib.charlotte_digital_twin.assets.download_hdri
"""

import os
import urllib.request
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# HDRI presets from Poly Haven (CC0 license)
# These are direct download links to 1k resolution (good balance of quality/size)
HDRI_ASSETS = {
    # Sunny daytime
    "sunny_afternoon": {
        "name": "Kloppenheim Part Cloudy",
        "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/kloppenheim_partly_cloudy_1k.hdr",
        "description": "Sunny afternoon with partial clouds",
        "sun_direction": "afternoon",
    },
    "golden_hour": {
        "name": "Hansa Tower Sunset",
        "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/hansa_tower_sunset_1k.hdr",
        "description": "Golden hour warm lighting",
        "sun_direction": "sunset",
    },
    "overcast": {
        "name": "Mossy Forest",
        "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/mossy_forest_1k.hdr",
        "description": "Overcast diffuse lighting",
        "sun_direction": "diffuse",
    },
    "clear_sky": {
        "name": "Blue Lagoon",
        "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/blue_lagoon_1k.hdr",
        "description": "Clear blue sky",
        "sun_direction": "midday",
    },
    "night": {
        "name": "Music Hall",
        "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/music_hall_01_1k.hdr",
        "description": "Indoor night ambient",
        "sun_direction": "none",
    },
    "sunrise": {
        "name": "Autumn Park",
        "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/autumn_park_1k.hdr",
        "description": "Morning sunrise warm tones",
        "sun_direction": "morning",
    },
    "dawn": {
        "name": "Lake Dwelling Dawn",
        "url": "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/lake_dwelling_dawn_1k.hdr",
        "description": "Early morning dawn light",
        "sun_direction": "dawn",
    },
}

# Asset directory
ASSET_DIR = Path(__file__).parent.parent.parent.parent / "assets" / "hdri"


def get_hdri_path(preset_name: str) -> Optional[Path]:
    """
    Get the path to an HDRI file.

    Args:
        preset_name: Name of HDRI preset

    Returns:
        Path to HDRI file or None if not found
    """
    if preset_name not in HDRI_ASSETS:
        return None

    filename = HDRI_ASSETS[preset_name]["url"].split("/")[-1]
    return ASSET_DIR / filename


def download_hdri(
    preset_name: str,
    force: bool = False,
) -> Optional[Path]:
    """
    Download an HDRI file.

    Args:
        preset_name: Name of HDRI preset
        force: Re-download even if exists

    Returns:
        Path to downloaded file or None on failure
    """
    if preset_name not in HDRI_ASSETS:
        print(f"Unknown HDRI preset: {preset_name}")
        print(f"Available: {list(HDRI_ASSETS.keys())}")
        return None

    # Ensure directory exists
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    asset = HDRI_ASSETS[preset_name]
    filename = asset["url"].split("/")[-1]
    filepath = ASSET_DIR / filename

    # Check if already downloaded
    if filepath.exists() and not force:
        print(f"HDRI already exists: {filepath}")
        return filepath

    # Download
    print(f"Downloading: {asset['name']}")
    print(f"From: {asset['url']}")
    print(f"To: {filepath}")

    try:
        urllib.request.urlretrieve(asset["url"], filepath)
        print(f"✓ Downloaded: {filepath}")
        return filepath
    except Exception as e:
        print(f"✗ Download failed: {e}")
        return None


def download_all_hdri(force: bool = False) -> Dict[str, Path]:
    """
    Download all HDRI presets.

    Args:
        force: Re-download even if exists

    Returns:
        Dict mapping preset names to file paths
    """
    results = {}

    print("Downloading HDRI Environment Maps")
    print("=" * 50)
    print(f"Target directory: {ASSET_DIR}")
    print()

    for name in HDRI_ASSETS:
        print(f"\n[{name}]")
        path = download_hdri(name, force)
        if path:
            results[name] = path

    print("\n" + "=" * 50)
    print(f"Downloaded {len(results)}/{len(HDRI_ASSETS)} HDRI files")

    return results


def list_hdri_assets() -> List[Dict]:
    """
    List available HDRI assets.

    Returns:
        List of asset info dicts
    """
    assets = []

    for name, info in HDRI_ASSETS.items():
        path = get_hdri_path(name)
        assets.append({
            "preset": name,
            "name": info["name"],
            "description": info["description"],
            "downloaded": path.exists() if path else False,
            "path": str(path) if path else None,
        })

    return assets


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Download HDRI environment maps")
    parser.add_argument(
        "preset",
        nargs="?",
        default="all",
        help="HDRI preset to download (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if file exists",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available presets",
    )

    args = parser.parse_args()

    if args.list:
        print("\nAvailable HDRI Presets:")
        print("-" * 60)
        for asset in list_hdri_assets():
            status = "✓" if asset["downloaded"] else " "
            print(f" [{status}] {asset['preset']}: {asset['description']}")
        print()
        return

    if args.preset == "all":
        download_all_hdri(args.force)
    else:
        download_hdri(args.preset, args.force)


if __name__ == "__main__":
    main()
