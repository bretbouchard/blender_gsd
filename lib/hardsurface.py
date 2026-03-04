"""
Hard Surface Validation Module - Codified from Tutorials 8, 9

Implements hard surface modeling validation including non-destructive
boolean workflows, proper beveling, and topology checks.

Based on tutorials:
- Default Cube: Hard Surface Mistakes (Section 8)
- Default Cube: Hard Surface Tips (Section 9)

Usage:
    from lib.hardsurface import HardSurfaceValidator, BooleanWorkflow

    # Validate hard surface model
    validator = HardSurfaceValidator(obj)
    issues = validator.check_all()

    # Create non-destructive boolean setup
    boolean = BooleanWorkflow.create("CutterSystem")
    boolean.add_cutter(cutter_obj)
    boolean.set_operation('DIFFERENCE')
"""

from __future__ import annotations
import bpy
import bmesh
from typing import Optional, List, Dict, Tuple
from pathlib import Path


class HardSurfaceValidator:
    """
    Validates hard surface models for common issues.

    Cross-references:
    - KB Section 8: Hard Surface Mistakes
    - KB Section 9: Hard Surface Tips
    """

    def __init__(self, obj: bpy.types.Object):
        self.obj = obj
        self._issues: List[Dict] = []
        self._warnings: List[Dict] = []

    def check_all(self) -> Dict:
        """
        Run all validation checks.

        KB Reference: Section 8-9 - Complete validation

        Returns:
            Dictionary with issues and warnings
        """
        self._issues = []
        self._warnings = []

        self.check_ngons()
        self.check_non_planar_faces()
        self.check_bevel_width()
        self.check_boolean_order()
        self.check_shading_issues()
        self.check_subdivision_issues()

        return {
            "object": self.obj.name,
            "issues": self._issues,
            "warnings": self._warnings,
            "passed": len(self._issues) == 0
        }

    def check_ngons(self) -> bool:
        """
        Check for ngons (faces with more than 4 vertices).

        KB Reference: Section 8 - Ngons are bad for hard surface

        Returns:
            True if no ngons found
        """
        if self.obj.type != 'MESH':
            return True

        mesh = self.obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        ngons = []
        for face in bm.faces:
            if len(face.verts) > 4:
                ngons.append(face.index)

        bm.free()

        if ngons:
            self._issues.append({
                "type": "ngons",
                "severity": "high",
                "message": f"Found {len(ngons)} ngons (faces with >4 vertices)",
                "faces": ngons[:10],  # Limit to first 10
                "fix": "Use triangulate or manually resolve ngons"
            })
            return False
        return True

    def check_non_planar_faces(self) -> bool:
        """
        Check for non-planar faces.

        KB Reference: Section 8 - Non-planar faces cause shading issues

        Returns:
            True if all faces are planar
        """
        if self.obj.type != 'MESH':
            return True

        mesh = self.obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        non_planar = []
        threshold = 0.001  # Tolerance for planarity

        for face in bm.faces:
            if not face.is_valid:
                continue
            # Check if face is planar
            if face.calc_area() > 0:
                normal = face.normal
                center = face.calc_center_median()
                for vert in face.verts:
                    dist = abs((vert.co - center).dot(normal))
                    if dist > threshold:
                        non_planar.append(face.index)
                        break

        bm.free()

        if non_planar:
            self._warnings.append({
                "type": "non_planar",
                "severity": "medium",
                "message": f"Found {len(non_planar)} non-planar faces",
                "faces": non_planar[:10],
                "fix": "Use triangulate or adjust vertex positions"
            })
            return False
        return True

    def check_bevel_width(self) -> bool:
        """
        Check if bevel modifier width is appropriate.

        KB Reference: Section 9 - Bevel width best practices

        Returns:
            True if bevel settings are appropriate
        """
        bevel_mods = [m for m in self.obj.modifiers if m.type == 'BEVEL']

        if not bevel_mods:
            return True

        issues = []
        for mod in bevel_mods:
            # Check for too large bevel
            if mod.width > 0.5:
                issues.append({
                    "modifier": mod.name,
                    "width": mod.width,
                    "issue": "Bevel width > 0.5 may cause artifacts"
                })

            # Check for too many segments (performance)
            if mod.segments > 6:
                issues.append({
                    "modifier": mod.name,
                    "segments": mod.segments,
                    "issue": "More than 6 segments may impact performance"
                })

        if issues:
            self._warnings.append({
                "type": "bevel_settings",
                "severity": "low",
                "message": "Bevel settings could be optimized",
                "details": issues
            })
            return False
        return True

    def check_boolean_order(self) -> bool:
        """
        Check boolean modifier order.

        KB Reference: Section 8 - Boolean order matters

        Returns:
            True if boolean order is correct
        """
        boolean_mods = [(i, m) for i, m in enumerate(self.obj.modifiers)
                        if m.type == 'BOOLEAN']

        if len(boolean_mods) < 2:
            return True

        # Check if booleans come before bevels
        bevel_indices = [i for i, m in enumerate(self.obj.modifiers)
                        if m.type == 'BEVEL']

        issues = []
        for bi, _ in boolean_mods:
            for bevel_i in bevel_indices:
                if bi > bevel_i:
                    issues.append({
                        "boolean_index": bi,
                        "bevel_index": bevel_i,
                        "issue": "Boolean should come before bevel"
                    })

        if issues:
            self._issues.append({
                "type": "modifier_order",
                "severity": "high",
                "message": "Boolean/bevel order is incorrect",
                "details": issues,
                "fix": "Move boolean modifiers above bevel modifiers"
            })
            return False
        return True

    def check_shading_issues(self) -> bool:
        """
        Check for shading-related issues.

        KB Reference: Section 8 - Shading problems

        Returns:
            True if no shading issues
        """
        issues = []

        # Check for flat shaded faces on curved surfaces
        if self.obj.type == 'MESH':
            mesh = self.obj.data
            flat_faces = [f for f in mesh.polygons if not f.use_smooth]

            # This is just a heuristic - many flat faces is normal for hard surface
            # But if ALL faces are flat, might need autosmooth
            if len(flat_faces) == len(mesh.polygons):
                issues.append("All faces are flat shaded - consider autosmooth")

        if issues:
            self._warnings.append({
                "type": "shading",
                "severity": "low",
                "message": "Potential shading issues",
                "details": issues
            })
            return False
        return True

    def check_subdivision_issues(self) -> bool:
        """
        Check for subdivision surface issues.

        KB Reference: Section 9 - Subsurf best practices

        Returns:
            True if no subdivision issues
        """
        subsurf_mods = [m for m in self.obj.modifiers
                       if m.type == 'SUBSURF']

        if not subsurf_mods:
            return True

        issues = []
        for mod in subsurf_mods:
            # Check for too high subdivision levels
            if mod.levels > 4:
                issues.append({
                    "modifier": mod.name,
                    "levels": mod.levels,
                    "issue": "Subdivision level > 4 is usually overkill"
                })

            # Check render vs viewport mismatch
            if mod.render_levels != mod.levels:
                issues.append({
                    "modifier": mod.name,
                    "viewport": mod.levels,
                    "render": mod.render_levels,
                    "issue": "Viewport and render levels differ"
                })

        if issues:
            self._warnings.append({
                "type": "subdivision",
                "severity": "low",
                "message": "Subdivision settings could be optimized",
                "details": issues
            })
            return False
        return True


class BooleanWorkflow:
    """
    Non-destructive boolean workflow for hard surface.

    Cross-references:
    - KB Section 8-9: Boolean best practices
    """

    def __init__(self, obj: bpy.types.Object):
        self.obj = obj
        self._cutters: List[bpy.types.Object] = []

    @classmethod
    def create(cls, name: str = "BooleanBase") -> "BooleanWorkflow":
        """
        Create a new mesh for boolean operations.

        Args:
            name: Name for the base object

        Returns:
            Configured BooleanWorkflow instance
        """
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        obj.name = name

        return cls(obj)

    @classmethod
    def from_object(cls, obj: bpy.types.Object) -> "BooleanWorkflow":
        """
        Create workflow from existing object.

        Args:
            obj: Existing mesh object

        Returns:
            Configured BooleanWorkflow instance
        """
        return cls(obj)

    def add_cutter(
        self,
        cutter: bpy.types.Object,
        operation: str = 'DIFFERENCE',
        solver: str = 'FAST'
    ) -> "BooleanWorkflow":
        """
        Add a cutter object with boolean modifier.

        KB Reference: Section 8-9 - Non-destructive booleans

        Args:
            cutter: Object to use as cutter
            operation: 'DIFFERENCE', 'UNION', 'INTERSECT'
            solver: 'FAST' or 'EXACT'

        Returns:
            Self for chaining
        """
        mod = self.obj.modifiers.new(name=f"Boolean_{cutter.name}", type='BOOLEAN')
        mod.operation = operation
        mod.object = cutter
        mod.solver = solver

        self._cutters.append(cutter)
        return self

    def add_bevel(
        self,
        width: float = 0.05,
        segments: int = 3,
        limit_method: str = 'ANGLE'
    ) -> "BooleanWorkflow":
        """
        Add bevel modifier after booleans.

        KB Reference: Section 9 - Bevel after boolean

        Args:
            width: Bevel width
            segments: Number of segments
            limit_method: 'ANGLE', 'WEIGHT', 'NONE'

        Returns:
            Self for chaining
        """
        mod = self.obj.modifiers.new(name="Bevel", type='BEVEL')
        mod.width = width
        mod.segments = segments
        mod.limit_method = limit_method
        mod.angle_limit = 30.0  # Good default for hard surface

        return self

    def add_weighted_normal(self) -> "BooleanWorkflow":
        """
        Add weighted normal modifier for smooth shading.

        KB Reference: Section 9 - Weighted normals for hard surface

        Returns:
            Self for chaining
        """
        mod = self.obj.modifiers.new(name="WeightedNormal", type='WEIGHTED_NORMAL')
        return self

    def get_cutters(self) -> List[bpy.types.Object]:
        """Get list of cutter objects."""
        return self._cutters.copy()


class HardSurfaceTips:
    """
    Quick reference for hard surface best practices.

    Cross-references:
    - KB Section 8: Common mistakes
    - KB Section 9: Pro tips
    """

    @staticmethod
    def get_common_mistakes() -> List[Dict]:
        """Get list of common hard surface mistakes."""
        return [
            {
                "mistake": "Applying booleans too early",
                "fix": "Keep booleans as modifiers until final",
                "why": "Non-destructive allows easy changes"
            },
            {
                "mistake": "Bevel before boolean",
                "fix": "Boolean first, then bevel",
                "why": "Bevel after gives clean edges"
            },
            {
                "mistake": "Using EXACT solver for everything",
                "fix": "Use FAST for most cases, EXACT only when needed",
                "why": "FAST is faster and works for most shapes"
            },
            {
                "mistake": "Ignoring ngons",
                "fix": "Resolve ngons before detailed work",
                "why": "Ngons cause shading and boolean issues"
            },
            {
                "mistake": "Too high bevel segments",
                "fix": "Use 2-4 segments typically",
                "why": "More segments = more geometry, slower"
            }
        ]

    @staticmethod
    def get_workflow_order() -> List[str]:
        """Get recommended modifier order."""
        return [
            "1. Armature (if rigging)",
            "2. Boolean modifiers",
            "3. Bevel modifier",
            "4. Weighted Normal",
            "5. Subdivision Surface (optional)",
            "6. Mirror (if needed)"
        ]

    @staticmethod
    def get_bevel_settings() -> Dict:
        """Get recommended bevel settings."""
        return {
            "width": {"min": 0.01, "max": 0.1, "typical": 0.05},
            "segments": {"min": 2, "max": 6, "typical": 3},
            "limit_method": "ANGLE (most control)",
            "angle_limit": "30° (good default)",
            "profile": "0.5 (circular arc)"
        }

    @staticmethod
    def get_boolean_solver_comparison() -> Dict:
        """Compare boolean solvers."""
        return {
            "FAST": {
                "pros": ["Fast", "Handles most shapes", "Predictable"],
                "cons": ["Can fail on complex geometry"],
                "use_when": "Most hard surface work"
            },
            "EXACT": {
                "pros": ["More accurate", "Handles complex overlaps"],
                "cons": ["Slower", "Can create weird topology"],
                "use_when": "FAST fails or need precision"
            }
        }


class HardSurfacePresets:
    """
    Preset configurations for hard surface styles.

    Cross-references:
    - KB Section 9: Style presets
    """

    @staticmethod
    def sci_fi_panel() -> Dict:
        """Configuration for sci-fi panel style."""
        return {
            "bevel_width": 0.02,
            "bevel_segments": 2,
            "boolean_solver": "FAST",
            "description": "Clean, hard edges for sci-fi panels"
        }

    @staticmethod
    def mechanical_part() -> Dict:
        """Configuration for mechanical parts."""
        return {
            "bevel_width": 0.05,
            "bevel_segments": 3,
            "boolean_solver": "FAST",
            "weighted_normals": True,
            "description": "Medium bevels for mechanical look"
        }

    @staticmethod
    def organic_hard_surface() -> Dict:
        """Configuration for organic hard surface (like armor)."""
        return {
            "bevel_width": 0.08,
            "bevel_segments": 4,
            "boolean_solver": "EXACT",
            "weighted_normals": True,
            "subdivision_levels": 1,
            "description": "Smoother transitions for organic shapes"
        }


# Convenience functions
def validate_hard_surface(obj: bpy.types.Object) -> Dict:
    """
    Quick validation of hard surface model.

    Args:
        obj: Object to validate

    Returns:
        Validation results
    """
    validator = HardSurfaceValidator(obj)
    return validator.check_all()


def create_boolean_setup(
    base_obj: bpy.types.Object,
    cutters: List[bpy.types.Object],
    operation: str = 'DIFFERENCE'
) -> BooleanWorkflow:
    """
    Quick setup for boolean workflow.

    Args:
        base_obj: Base mesh object
        cutters: List of cutter objects
        operation: Boolean operation

    Returns:
        Configured BooleanWorkflow
    """
    workflow = BooleanWorkflow.from_object(base_obj)
    for cutter in cutters:
        workflow.add_cutter(cutter, operation)
    workflow.add_bevel()
    workflow.add_weighted_normal()
    return workflow


def get_quick_reference() -> Dict:
    """Get quick reference for hard surface."""
    return {
        "modifier_order": ["Boolean", "Bevel", "Weighted Normal"],
        "bevel_defaults": {"width": 0.05, "segments": 3},
        "solver": "FAST for most cases",
        "key_principle": "Non-destructive until final"
    }


class HardSurfaceHUD:
    """
    Heads-Up Display for hard surface validation results.

    Provides formatted output for validation reports.

    Cross-references:
    - KB Section 8-9: Validation reporting
    """

    @staticmethod
    def format_report(results: Dict, style: str = "full") -> str:
        """
        Format validation results as readable report.

        KB Reference: Section 8-9 - Validation display

        Args:
            results: Results from HardSurfaceValidator.check_all()
            style: 'full', 'compact', or 'summary'

        Returns:
            Formatted report string
        """
        if style == "compact":
            return HardSurfaceHUD._format_compact(results)
        elif style == "summary":
            return HardSurfaceHUD._format_summary(results)
        else:
            return HardSurfaceHUD._format_full(results)

    @staticmethod
    def _format_summary(results: Dict) -> str:
        """Format as one-line summary."""
        obj = results.get("object", "Unknown")
        issues = len(results.get("issues", []))
        warnings = len(results.get("warnings", []))
        passed = results.get("passed", False)

        status = "✓ PASS" if passed else "✗ FAIL"
        return f"[{status}] {obj}: {issues} issues, {warnings} warnings"

    @staticmethod
    def _format_compact(results: Dict) -> str:
        """Format as compact multi-line."""
        lines = []
        obj = results.get("object", "Unknown")
        passed = results.get("passed", False)

        lines.append(f"═══════════════════════════════════════")
        lines.append(f"  HARD SURFACE VALIDATION: {obj}")
        lines.append(f"  Status: {'✓ PASSED' if passed else '✗ FAILED'}")
        lines.append(f"═══════════════════════════════════════")

        # Issues
        issues = results.get("issues", [])
        if issues:
            lines.append(f"\n  ❌ ISSUES ({len(issues)}):")
            for issue in issues:
                severity = issue.get("severity", "?").upper()
                msg = issue.get("message", "Unknown issue")
                lines.append(f"    [{severity}] {msg}")

        # Warnings
        warnings = results.get("warnings", [])
        if warnings:
            lines.append(f"\n  ⚠ WARNINGS ({len(warnings)}):")
            for warning in warnings:
                severity = warning.get("severity", "?").upper()
                msg = warning.get("message", "Unknown warning")
                lines.append(f"    [{severity}] {msg}")

        if not issues and not warnings:
            lines.append("\n  ✓ No issues found!")

        lines.append(f"\n═══════════════════════════════════════")
        return "\n".join(lines)

    @staticmethod
    def _format_full(results: Dict) -> str:
        """Format as detailed full report."""
        lines = []
        obj = results.get("object", "Unknown")
        passed = results.get("passed", False)

        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'HARD SURFACE VALIDATION REPORT':^50}║")
        lines.append("╠" + "═" * 50 + "╣")
        lines.append(f"║ Object: {obj:<42}║")
        lines.append(f"║ Status: {'✓ PASSED' if passed else '✗ FAILED':<42}║")
        lines.append("╚" + "═" * 50 + "╝")

        # Issues section
        issues = results.get("issues", [])
        lines.append(f"\n┌{' ISSUES ':─^48}┐" if issues else f"\n┌{' ✓ NO ISSUES ':─^48}┐")
        if issues:
            for i, issue in enumerate(issues, 1):
                itype = issue.get("type", "unknown")
                severity = issue.get("severity", "?").upper()
                msg = issue.get("message", "Unknown issue")
                fix = issue.get("fix", "No fix suggested")

                lines.append(f"│ {i}. [{severity}] {itype}")
                lines.append(f"│    {msg}")
                lines.append(f"│    Fix: {fix}")
                lines.append("│" + " " * 48 + "│")
        lines.append("└" + "─" * 48 + "┘")

        # Warnings section
        warnings = results.get("warnings", [])
        lines.append(f"\n┌{' WARNINGS ':─^48}┐" if warnings else f"\n┌{' ✓ NO WARNINGS ':─^48}┐")
        if warnings:
            for i, warning in enumerate(warnings, 1):
                wtype = warning.get("type", "unknown")
                severity = warning.get("severity", "?").upper()
                msg = warning.get("message", "Unknown warning")

                lines.append(f"│ {i}. [{severity}] {wtype}")
                lines.append(f"│    {msg}")
                lines.append("│" + " " * 48 + "│")
        lines.append("└" + "─" * 48 + "┘")

        # Quick reference
        lines.append("\n┌{' QUICK REFERENCE ':─^48}┐")
        lines.append("│ Modifier Order: Boolean → Bevel → Weighted Normal")
        lines.append("│ Bevel: width 0.05, segments 3, angle 30°")
        lines.append("│ Solver: FAST (most cases) / EXACT (complex)")
        lines.append("└" + "─" * 48 + "┘")

        return "\n".join(lines)

    @staticmethod
    def display_modifier_stack(obj: bpy.types.Object) -> str:
        """
        Display modifier stack visually.

        KB Reference: Section 8-9 - Modifier order visualization

        Args:
            obj: Object with modifiers

        Returns:
            Formatted modifier stack display
        """
        lines = []
        lines.append(f"┌{' MODIFIER STACK ':─^48}┐")
        lines.append(f"│ Object: {obj.name:<40}│")
        lines.append("├" + "─" * 48 + "┤")

        if not obj.modifiers:
            lines.append("│ (no modifiers)                                    │")
        else:
            for i, mod in enumerate(obj.modifiers):
                mod_type = mod.type
                status = ""

                # Check for common issues
                if mod_type == 'BOOLEAN':
                    status = " ← Check order"
                elif mod_type == 'BEVEL':
                    status = f" (w:{mod.width:.2f}, s:{mod.segments})"

                lines.append(f"│ {i+1}. {mod_type:<20}{status:<26}│")

        lines.append("└" + "─" * 48 + "┘")
        return "\n".join(lines)

    @staticmethod
    def display_checklist() -> str:
        """
        Display hard surface modeling checklist.

        KB Reference: Section 8-9 - Best practices checklist

        Returns:
            Formatted checklist
        """
        lines = []
        lines.append("╔" + "═" * 50 + "╗")
        lines.append(f"║{'HARD SURFACE MODELING CHECKLIST':^50}║")
        lines.append("╠" + "═" * 50 + "╣")

        checklist = [
            ("Topology", [
                "☐ No ngons (faces with >4 vertices)",
                "☐ All quads/tris where possible",
                "☐ No non-planar faces on curved surfaces",
            ]),
            ("Modifiers", [
                "☐ Booleans before bevels",
                "☐ Bevel width appropriate (<0.5)",
                "☐ Bevel segments reasonable (2-6)",
                "☐ Weighted normal for smooth shading",
            ]),
            ("Workflow", [
                "☐ Booleans non-destructive (not applied)",
                "☐ FAST solver for most cases",
                "☐ Test with different bevel widths",
            ]),
            ("Before Final", [
                "☐ Apply booleans only when ready",
                "☐ Check shading on curved areas",
                "☐ Verify render vs viewport match",
            ]),
        ]

        for category, items in checklist:
            lines.append(f"║ {category}:")
            for item in items:
                lines.append(f"║   {item}")

        lines.append("╚" + "═" * 50 + "╝")
        return "\n".join(lines)


def print_validation_report(obj: bpy.types.Object, style: str = "full") -> None:
    """
    Print validation report to console.

    Args:
        obj: Object to validate
        style: 'full', 'compact', or 'summary'
    """
    validator = HardSurfaceValidator(obj)
    results = validator.check_all()
    print(HardSurfaceHUD.format_report(results, style))
