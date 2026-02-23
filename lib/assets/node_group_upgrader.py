"""
Node Group Upgrader - Expose inputs on procedural assets.

This module ensures all procedural node groups have properly exposed inputs
for style, color, and seed control. It can scan assets, report missing inputs,
and automatically upgrade them.

Usage:
    from lib.assets.node_group_upgrader import NodeGroupUpgrader

    # Scan and report
    upgrader = NodeGroupUpgrader()
    report = upgrader.scan_blend("assets/vehicles/procedural_car_wired.blend")
    print(report)

    # Upgrade all node groups in a blend
    upgrader.upgrade_blend("assets/vehicles/procedural_car_wired.blend")

    # Batch upgrade all assets
    upgrader.upgrade_directory("assets/")

CLI Usage:
    blender --background --python lib/assets/node_group_upgrader.py -- \
        --scan assets/vehicles/
    blender --background --python lib/assets/node_group_upgrader.py -- \
        --upgrade assets/vehicles/procedural_car_wired.blend
"""

import bpy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import json


# Standard input definitions for procedural assets
STANDARD_INPUTS = {
    # Style Selection (1-indexed for user-friendliness)
    "Front Base": {"type": "INT", "min": 1, "max": 14, "default": 1, "description": "Front body style"},
    "Back Base": {"type": "INT", "min": 1, "max": 20, "default": 1, "description": "Rear body style"},
    "Central Base": {"type": "INT", "min": 1, "max": 3, "default": 1, "description": "Central body section"},
    "Front Bumper": {"type": "INT", "min": 1, "max": 10, "default": 1, "description": "Front bumper style"},
    "Back Bumper": {"type": "INT", "min": 1, "max": 9, "default": 1, "description": "Rear bumper style"},
    "Front Lights": {"type": "INT", "min": 1, "max": 11, "default": 1, "description": "Front headlights style"},
    "Back Lights": {"type": "INT", "min": 1, "max": 13, "default": 1, "description": "Rear taillights style"},
    "Wheel Style": {"type": "INT", "min": 1, "max": 11, "default": 1, "description": "Wheel rim style"},
    "Mirror Style": {"type": "INT", "min": 1, "max": 5, "default": 1, "description": "Side mirror style"},
    "Handle Style": {"type": "INT", "min": 1, "max": 5, "default": 1, "description": "Door handle style"},
    "Grill Style": {"type": "INT", "min": 1, "max": 9, "default": 1, "description": "Front grill style"},

    # Colors (RGBA)
    "Body Color": {"type": "RGBA", "default": (0.5, 0.5, 0.5, 1.0), "description": "Main body color"},
    "Secondary Color": {"type": "RGBA", "default": (0.3, 0.3, 0.3, 1.0), "description": "Secondary/accent color"},
    "Glass Color": {"type": "RGBA", "default": (0.2, 0.3, 0.4, 0.5), "description": "Window glass color"},
    "Metal Color": {"type": "RGBA", "default": (0.8, 0.8, 0.8, 1.0), "description": "Chrome/metal trim color"},
    "Rubber Color": {"type": "RGBA", "default": (0.1, 0.1, 0.1, 1.0), "description": "Tire/rubber color"},
    "Light Color Front": {"type": "RGBA", "default": (1.0, 1.0, 0.9, 1.0), "description": "Headlight color"},
    "Light Color Back": {"type": "RGBA", "default": (1.0, 0.2, 0.1, 1.0), "description": "Taillight color"},

    # Material Properties
    "Metalness": {"type": "FLOAT", "min": 0.0, "max": 1.0, "default": 0.8, "description": "Body metalness"},
    "Roughness": {"type": "FLOAT", "min": 0.0, "max": 1.0, "default": 0.3, "description": "Body roughness"},
    "Clearcoat": {"type": "FLOAT", "min": 0.0, "max": 1.0, "default": 0.5, "description": "Clearcoat strength"},

    # Random/Seed
    "Seed": {"type": "INT", "min": 0, "max": 999999, "default": 0, "description": "Random seed for variation"},

    # Scale/Transform
    "Scale": {"type": "FLOAT", "min": 0.1, "max": 10.0, "default": 1.0, "description": "Overall scale"},
}

# Legacy input names that map to standard names
LEGACY_INPUT_MAPPING = {
    "front": "Front Base",
    "back": "Back Base",
    "central": "Central Base",
    "front bumper": "Front Bumper",
    "back bumper": "Back Bumper",
    "front headlights": "Front Lights",
    "back headlights": "Back Lights",
    "wheels": "Wheel Style",
    "mirrors": "Mirror Style",
    "handles": "Handle Style",
    "grid": "Grill Style",
    "random": "Seed",
}


@dataclass
class NodeGroupReport:
    """Report on a node group's input status."""
    name: str
    blend_file: str
    existing_inputs: List[str]
    missing_inputs: List[str]
    node_count: int
    uses_collections: bool
    collection_refs: List[str]
    needs_upgrade: bool

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "blend_file": self.blend_file,
            "existing_inputs": self.existing_inputs,
            "missing_inputs": self.missing_inputs,
            "node_count": self.node_count,
            "uses_collections": self.uses_collections,
            "collection_refs": self.collection_refs,
            "needs_upgrade": self.needs_upgrade,
        }


@dataclass
class BlendUpgradeReport:
    """Report on a blend file's upgrade status."""
    blend_file: str
    node_groups: List[NodeGroupReport]
    upgraded: bool = False
    errors: List[str] = field(default_factory=list)

    @property
    def total_missing_inputs(self) -> int:
        return sum(len(ng.missing_inputs) for ng in self.node_groups)

    @property
    def needs_upgrade(self) -> bool:
        return any(ng.needs_upgrade for ng in self.node_groups)

    def to_dict(self) -> Dict:
        return {
            "blend_file": self.blend_file,
            "node_groups": [ng.to_dict() for ng in self.node_groups],
            "upgraded": self.upgraded,
            "errors": self.errors,
            "total_missing_inputs": self.total_missing_inputs,
            "needs_upgrade": self.needs_upgrade,
        }


class NodeGroupUpgrader:
    """
    Scan and upgrade node groups to expose standard inputs.

    This ensures all procedural assets have consistent, controllable inputs
    for style selection, colors, and other parameters.
    """

    def __init__(self, standard_inputs: Dict = None):
        self.standard_inputs = standard_inputs or STANDARD_INPUTS
        self._current_file = None

    def scan_blend(self, blend_path: str) -> BlendUpgradeReport:
        """
        Scan a blend file and report on node group inputs.

        Args:
            blend_path: Path to the blend file

        Returns:
            BlendUpgradeReport with details on each node group
        """
        blend_path = str(Path(blend_path).resolve())
        reports = []

        # Load the blend file's node groups without opening full file
        with bpy.data.libraries.load(blend_path) as (data_from, data_to):
            node_group_names = list(data_from.node_groups)

        # We need to actually load to inspect
        # Create a temporary scene to load into
        original_file = bpy.data.filepath

        try:
            # Link node groups
            with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                data_to.node_groups = node_group_names

            # Inspect each loaded node group
            for ng_name in node_group_names:
                ng = bpy.data.node_groups.get(ng_name)
                if ng and ng.type == 'GEOMETRY':
                    report = self._analyze_node_group(ng, blend_path)
                    reports.append(report)

        finally:
            # Clean up loaded node groups
            for ng_name in node_group_names:
                ng = bpy.data.node_groups.get(ng_name)
                if ng:
                    bpy.data.node_groups.remove(ng)

        return BlendUpgradeReport(
            blend_file=blend_path,
            node_groups=reports,
        )

    def _analyze_node_group(self, ng: bpy.types.NodeGroup, blend_path: str) -> NodeGroupReport:
        """Analyze a single node group for missing inputs."""
        existing_inputs = []
        collection_refs = []

        # Get existing inputs
        for item in ng.interface.items():
            if hasattr(item, 'in_out') and item.in_out == 'INPUT':
                existing_inputs.append(item.name)

        # Check for collection info nodes
        for node in ng.nodes:
            if node.bl_idname == 'GeometryNodeCollectionInfo':
                for inp in node.inputs:
                    if inp.type == 'COLLECTION' and inp.default_value:
                        collection_refs.append(inp.default_value.name)

        # Determine missing inputs
        missing = []
        for std_name in self.standard_inputs:
            if std_name not in existing_inputs:
                # Also check legacy names
                legacy_found = False
                for legacy, standard in LEGACY_INPUT_MAPPING.items():
                    if standard == std_name and legacy in existing_inputs:
                        legacy_found = True
                        break
                if not legacy_found:
                    missing.append(std_name)

        return NodeGroupReport(
            name=ng.name,
            blend_file=blend_path,
            existing_inputs=existing_inputs,
            missing_inputs=missing,
            node_count=len(ng.nodes),
            uses_collections=len(collection_refs) > 0,
            collection_refs=collection_refs,
            needs_upgrade=len(missing) > 0,
        )

    def upgrade_blend(self, blend_path: str, save: bool = True) -> BlendUpgradeReport:
        """
        Upgrade all node groups in a blend file to expose standard inputs.

        Args:
            blend_path: Path to the blend file
            save: Whether to save the file after upgrading

        Returns:
            BlendUpgradeReport with upgrade results
        """
        blend_path = str(Path(blend_path).resolve())

        # Open the blend file
        bpy.ops.wm.open_mainfile(filepath=blend_path)

        reports = []
        errors = []
        upgraded_count = 0

        for ng in bpy.data.node_groups:
            if ng.type == 'GEOMETRY':
                report = self._analyze_node_group(ng, blend_path)
                reports.append(report)

                if report.needs_upgrade:
                    try:
                        added = self._add_missing_inputs(ng, report.missing_inputs)
                        if added > 0:
                            upgraded_count += 1
                            print(f"  Added {added} inputs to '{ng.name}'")
                    except Exception as e:
                        errors.append(f"Error upgrading '{ng.name}': {e}")

        # Save if requested and changes were made
        if save and upgraded_count > 0:
            bpy.ops.wm.save_mainfile()
            print(f"Saved upgraded file: {blend_path}")

        return BlendUpgradeReport(
            blend_file=blend_path,
            node_groups=reports,
            upgraded=upgraded_count > 0,
            errors=errors,
        )

    def _add_missing_inputs(self, ng: bpy.types.NodeGroup, missing_inputs: List[str]) -> int:
        """
        Add missing inputs to a node group.

        Args:
            ng: The node group to upgrade
            missing_inputs: List of input names to add

        Returns:
            Number of inputs actually added
        """
        added = 0

        for input_name in missing_inputs:
            if input_name not in self.standard_inputs:
                continue

            spec = self.standard_inputs[input_name]
            input_type = spec["type"]

            try:
                # Create the interface socket
                if input_type == "INT":
                    socket = ng.interface.new_socket(
                        name=input_name,
                        in_out='INPUT',
                        socket_type='INT',
                    )
                    # Set default and range via the socket
                    socket.default_value = spec.get("default", 1)
                    if hasattr(socket, 'min_value'):
                        socket.min_value = spec.get("min", 0)
                        socket.max_value = spec.get("max", 100)

                elif input_type == "FLOAT":
                    socket = ng.interface.new_socket(
                        name=input_name,
                        in_out='INPUT',
                        socket_type='FLOAT',
                    )
                    socket.default_value = spec.get("default", 0.5)
                    if hasattr(socket, 'min_value'):
                        socket.min_value = spec.get("min", 0.0)
                        socket.max_value = spec.get("max", 1.0)

                elif input_type == "RGBA":
                    socket = ng.interface.new_socket(
                        name=input_name,
                        in_out='INPUT',
                        socket_type='RGBA',
                    )
                    socket.default_value = spec.get("default", (0.5, 0.5, 0.5, 1.0))

                elif input_type == "BOOLEAN":
                    socket = ng.interface.new_socket(
                        name=input_name,
                        in_out='INPUT',
                        socket_type='BOOLEAN',
                    )
                    socket.default_value = spec.get("default", False)

                elif input_type == "VECTOR":
                    socket = ng.interface.new_socket(
                        name=input_name,
                        in_out='INPUT',
                        socket_type='VECTOR',
                    )
                    socket.default_value = spec.get("default", (0.0, 0.0, 0.0))

                else:
                    print(f"  Unknown input type '{input_type}' for '{input_name}'")
                    continue

                # Add description if available
                if hasattr(socket, 'description'):
                    socket.description = spec.get("description", "")

                added += 1

            except Exception as e:
                print(f"  Error adding input '{input_name}': {e}")

        return added

    def upgrade_directory(self, directory: str, pattern: str = "*.blend") -> List[BlendUpgradeReport]:
        """
        Upgrade all blend files in a directory.

        Args:
            directory: Directory to scan
            pattern: Glob pattern for blend files

        Returns:
            List of upgrade reports for each file
        """
        reports = []
        dir_path = Path(directory)

        for blend_file in dir_path.rglob(pattern):
            print(f"\nProcessing: {blend_file}")
            report = self.upgrade_blend(str(blend_file))
            reports.append(report)

            if report.needs_upgrade and not report.upgraded:
                print(f"  WARNING: Needed upgrade but failed")
            elif report.upgraded:
                print(f"  Upgraded: {report.total_missing_inputs} inputs added")

        return reports

    def generate_report_json(self, reports: List[BlendUpgradeReport]) -> str:
        """Generate a JSON report of all scanned/upgraded files."""
        return json.dumps(
            [r.to_dict() for r in reports],
            indent=2,
        )


def scan_command(blend_path: str):
    """Scan a blend file and print report."""
    upgrader = NodeGroupUpgrader()
    report = upgrader.scan_blend(blend_path)

    print(f"\n{'='*60}")
    print(f"SCAN REPORT: {blend_path}")
    print(f"{'='*60}")

    for ng_report in report.node_groups:
        print(f"\nNode Group: '{ng_report.name}'")
        print(f"  Nodes: {ng_report.node_count}")
        print(f"  Uses Collections: {ng_report.uses_collections}")
        if ng_report.collection_refs:
            print(f"  Collection Refs: {ng_report.collection_refs}")
        print(f"  Existing Inputs: {ng_report.existing_inputs}")
        if ng_report.missing_inputs:
            print(f"  MISSING Inputs: {ng_report.missing_inputs}")
            print(f"  Status: NEEDS UPGRADE")
        else:
            print(f"  Status: OK")

    return report


def upgrade_command(blend_path: str):
    """Upgrade a blend file."""
    upgrader = NodeGroupUpgrader()
    report = upgrader.upgrade_blend(blend_path)

    print(f"\n{'='*60}")
    print(f"UPGRADE REPORT: {blend_path}")
    print(f"{'='*60}")

    if report.upgraded:
        print(f"Status: UPGRADED")
        print(f"Inputs Added: {report.total_missing_inputs}")
    else:
        print(f"Status: NO CHANGES NEEDED")

    if report.errors:
        print(f"Errors: {report.errors}")

    return report


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Node Group Upgrader")
    parser.add_argument("--scan", metavar="PATH", help="Scan a blend file or directory")
    parser.add_argument("--upgrade", metavar="PATH", help="Upgrade a blend file")
    parser.add_argument("--upgrade-dir", metavar="PATH", help="Upgrade all blend files in directory")
    parser.add_argument("--report", metavar="FILE", help="Output JSON report to file")

    args = parser.parse_args()

    upgrader = NodeGroupUpgrader()

    if args.scan:
        path = Path(args.scan)
        if path.is_file():
            report = scan_command(str(path))
        else:
            # Directory scan
            reports = []
            for blend in path.rglob("*.blend"):
                r = upgrader.scan_blend(str(blend))
                reports.append(r)
                print(f"\n{blend}: {'NEEDS UPGRADE' if r.needs_upgrade else 'OK'}")

            if args.report:
                with open(args.report, 'w') as f:
                    f.write(upgrader.generate_report_json(reports))
                print(f"\nReport saved to: {args.report}")

    elif args.upgrade:
        upgrade_command(args.upgrade)

    elif args.upgrade_dir:
        reports = upgrader.upgrade_directory(args.upgrade_dir)
        summary = {
            "total": len(reports),
            "upgraded": sum(1 for r in reports if r.upgraded),
            "failed": len([r for r in reports if r.needs_upgrade and not r.upgraded]),
        }
        print(f"\nSummary: {summary}")
