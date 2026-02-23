#!/usr/bin/env python3
"""
Recover Blend Files from .blend1 Backups

The re-conversion script created corrupted 17-byte files and Blender
saved the originals as .blend1 backups. This script restores them.

Usage:
    python3 recover_from_backups.py
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
CONVERTED_ROOT = Path("/Volumes/Storage/3d/kitbash/converted_assets")
CORRUPTED_SIZE = 17  # bytes


def find_recoverable_files(root: Path) -> list[tuple[Path, Path]]:
    """
    Find files where:
    - .blend is corrupted (17 bytes)
    - .blend1 backup exists and is valid

    Returns list of (corrupted_path, backup_path) tuples.
    """
    recoverable = []

    for backup_file in root.rglob("*.blend1"):
        # Check if backup is valid (not corrupted)
        if backup_file.stat().st_size <= CORRUPTED_SIZE:
            continue

        # Check if corresponding .blend is corrupted
        # .blend1 -> .blend (remove the "1" from end)
        main_file = Path(str(backup_file)[:-1])  # Remove trailing "1"

        if main_file.exists() and main_file.stat().st_size == CORRUPTED_SIZE:
            recoverable.append((main_file, backup_file))

    return recoverable


def main():
    print("=" * 60)
    print("RECOVER FROM .blend1 BACKUPS")
    print("=" * 60)

    # Find recoverable files
    print("\nScanning for recoverable files...")
    recoverable = find_recoverable_files(CONVERTED_ROOT)
    print(f"Found {len(recoverable)} files to recover")

    if not recoverable:
        print("No recoverable files found.")
        return

    # Confirm
    print(f"\nThis will:")
    print(f"  1. Delete {len(recoverable)} corrupted .blend files (17 bytes)")
    print(f"  2. Rename .blend1 backups to .blend")
    print(f"\nContinue? (y/n): ", end="")

    response = input().strip().lower()
    if response != 'y':
        print("Cancelled.")
        return

    # Recover
    success = 0
    fail = 0

    for i, (corrupted, backup) in enumerate(recoverable):
        print(f"[{i+1}/{len(recoverable)}] {corrupted.relative_to(CONVERTED_ROOT)}")

        try:
            # Delete corrupted file
            corrupted.unlink()

            # Rename backup to main file
            backup.rename(corrupted)

            success += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            fail += 1

    print("\n" + "=" * 60)
    print("COMPLETE")
    print(f"  Recovered: {success}")
    print(f"  Failed:    {fail}")


if __name__ == "__main__":
    main()
