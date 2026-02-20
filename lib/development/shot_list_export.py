"""
Shot List Export - Export shot lists in various formats.

Implements REQ-SHOT-04
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
import csv
import io

from .shot_gen_types import ShotList, SceneShotList, ShotSuggestion


def export_shot_list_csv(shot_list: ShotList, path: str) -> None:
    """Export shot list as CSV file.

    Args:
        shot_list: ShotList to export
        path: File path to write to
    """
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow([
            "Scene",
            "Shot",
            "Label",
            "Shot Size",
            "Camera Angle",
            "Subject",
            "Purpose",
            "Duration (s)",
            "Priority",
            "Camera Move",
            "Description",
            "Notes"
        ])

        # Write shots
        for scene_num in sorted(shot_list.scenes.keys()):
            scene_shots = shot_list.scenes[scene_num]
            for shot in scene_shots.shots:
                writer.writerow([
                    shot.scene_number,
                    shot.shot_number,
                    shot.get_shot_label(),
                    shot.get_shot_size_name(),
                    _format_angle(shot.camera_angle),
                    shot.subject,
                    _format_purpose(shot.purpose),
                    f"{shot.estimated_duration:.1f}",
                    shot.priority.capitalize(),
                    _format_camera_move(shot.camera_move),
                    shot.description,
                    shot.notes
                ])


def export_shot_list_csv_string(shot_list: ShotList) -> str:
    """Export shot list as CSV string.

    Args:
        shot_list: ShotList to export

    Returns:
        CSV formatted string
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Scene",
        "Shot",
        "Label",
        "Shot Size",
        "Camera Angle",
        "Subject",
        "Purpose",
        "Duration (s)",
        "Priority",
        "Camera Move",
        "Description",
        "Notes"
    ])

    # Write shots
    for scene_num in sorted(shot_list.scenes.keys()):
        scene_shots = shot_list.scenes[scene_num]
        for shot in scene_shots.shots:
            writer.writerow([
                shot.scene_number,
                shot.shot_number,
                shot.get_shot_label(),
                shot.get_shot_size_name(),
                _format_angle(shot.camera_angle),
                shot.subject,
                _format_purpose(shot.purpose),
                f"{shot.estimated_duration:.1f}",
                shot.priority.capitalize(),
                _format_camera_move(shot.camera_move),
                shot.description,
                shot.notes
            ])

    return output.getvalue()


def export_shot_list_yaml(shot_list: ShotList, path: str) -> None:
    """Export shot list as YAML file.

    Args:
        shot_list: ShotList to export
        path: File path to write to
    """
    try:
        import yaml
    except ImportError:
        # Fallback to JSON if PyYAML not available
        import json
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(shot_list.to_dict(), f, indent=2)
        return

    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(shot_list.to_dict(), f, default_flow_style=False, sort_keys=False)


def export_shot_list_yaml_string(shot_list: ShotList) -> str:
    """Export shot list as YAML string.

    Args:
        shot_list: ShotList to export

    Returns:
        YAML formatted string
    """
    try:
        import yaml
        return yaml.dump(shot_list.to_dict(), default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback to JSON
        import json
        return json.dumps(shot_list.to_dict(), indent=2)


def export_shot_list_json(shot_list: ShotList, path: str) -> None:
    """Export shot list as JSON file.

    Args:
        shot_list: ShotList to export
        path: File path to write to
    """
    with open(path, 'w', encoding='utf-8') as f:
        f.write(shot_list.to_json(indent=2))


def export_shot_list_pdf(shot_list: ShotList, path: str) -> None:
    """Export shot list as PDF file.

    Note: Requires reportlab for PDF generation.
    Falls back to text-based output if not available.

    Args:
        shot_list: ShotList to export
        path: File path to write to
    """
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch

        doc = SimpleDocTemplate(
            path,
            pagesize=landscape(letter),
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )

        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20
        )
        elements.append(Paragraph(f"Shot List: {shot_list.production}", title_style))

        # Metadata
        meta_style = ParagraphStyle(
            'Meta',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=10
        )
        elements.append(Paragraph(
            f"Date: {shot_list.date_created or datetime.now().strftime('%Y-%m-%d')} | "
            f"Total Shots: {shot_list.total_shots} | "
            f"Est. Duration: {shot_list.estimated_total_duration / 60:.1f} min",
            meta_style
        ))
        elements.append(Spacer(1, 20))

        # Table data
        table_data = [
            ["Scene", "Shot", "Size", "Angle", "Subject", "Purpose", "Duration", "Priority"]
        ]

        for scene_num in sorted(shot_list.scenes.keys()):
            scene_shots = shot_list.scenes[scene_num]
            for shot in scene_shots.shots:
                table_data.append([
                    str(shot.scene_number),
                    shot.get_shot_label(),
                    shot.shot_size.upper(),
                    _format_angle(shot.camera_angle),
                    shot.subject[:20] + "..." if len(shot.subject) > 20 else shot.subject,
                    _format_purpose(shot.purpose),
                    f"{shot.estimated_duration:.1f}s",
                    shot.priority.capitalize()
                ])

        # Create table
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(table)
        doc.build(elements)

    except ImportError:
        # Fallback to HTML that can be printed to PDF
        html_content = generate_shot_list_html(shot_list)
        html_path = path.replace('.pdf', '.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)


def generate_shot_list_html(shot_list: ShotList) -> str:
    """Generate HTML representation of shot list.

    Args:
        shot_list: ShotList to format

    Returns:
        HTML string
    """
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "    <meta charset='UTF-8'>",
        "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
        f"    <title>Shot List - {shot_list.production}</title>",
        "    <style>",
        "        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #e0e0e0; }",
        "        h1 { color: #ffffff; border-bottom: 2px solid #4a90d9; padding-bottom: 10px; }",
        "        .meta { color: #888; margin-bottom: 20px; }",
        "        table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }",
        "        th, td { border: 1px solid #333; padding: 8px 12px; text-align: left; }",
        "        th { background-color: #2a2a2a; color: #fff; font-weight: bold; }",
        "        tr:nth-child(even) { background-color: #252525; }",
        "        tr:hover { background-color: #333; }",
        "        .essential { color: #ff6b6b; font-weight: bold; }",
        "        .recommended { color: #feca57; }",
        "        .optional { color: #888; }",
        "        .scene-header { background-color: #4a90d9 !important; color: white; font-weight: bold; }",
        "        .scene-heading { margin-top: 30px; padding: 10px; background: #2a2a2a; border-left: 4px solid #4a90d9; }",
        "        @media print { body { background: white; color: black; } th { background: #ddd; } }",
        "    </style>",
        "</head>",
        "<body>",
        f"    <h1>Shot List: {shot_list.production}</h1>",
        f"    <div class='meta'>",
        f"        Date: {shot_list.date_created or datetime.now().strftime('%Y-%m-%d')} | ",
        f"        Total Shots: {shot_list.total_shots} | ",
        f"        Est. Duration: {shot_list.estimated_total_duration / 60:.1f} minutes | ",
        f"        Version: {shot_list.version}",
        "    </div>",
    ]

    # Scene by scene
    for scene_num in sorted(shot_list.scenes.keys()):
        scene_shots = shot_list.scenes[scene_num]
        html_parts.append(f"    <div class='scene-heading'>Scene {scene_num}: {scene_shots.scene_heading}</div>")
        html_parts.append("    <table>")
        html_parts.append("        <tr>")
        html_parts.append("            <th>Shot</th>")
        html_parts.append("            <th>Size</th>")
        html_parts.append("            <th>Angle</th>")
        html_parts.append("            <th>Subject</th>")
        html_parts.append("            <th>Purpose</th>")
        html_parts.append("            <th>Duration</th>")
        html_parts.append("            <th>Priority</th>")
        html_parts.append("            <th>Camera</th>")
        html_parts.append("            <th>Description</th>")
        html_parts.append("        </tr>")

        for shot in scene_shots.shots:
            priority_class = shot.priority
            html_parts.append("        <tr>")
            html_parts.append(f"            <td>{shot.get_shot_label()}</td>")
            html_parts.append(f"            <td>{shot.get_shot_size_name()}</td>")
            html_parts.append(f"            <td>{_format_angle(shot.camera_angle)}</td>")
            html_parts.append(f"            <td>{shot.subject}</td>")
            html_parts.append(f"            <td>{_format_purpose(shot.purpose)}</td>")
            html_parts.append(f"            <td>{shot.estimated_duration:.1f}s</td>")
            html_parts.append(f"            <td class='{priority_class}'>{shot.priority.capitalize()}</td>")
            html_parts.append(f"            <td>{_format_camera_move(shot.camera_move)}</td>")
            html_parts.append(f"            <td>{shot.description}</td>")
            html_parts.append("        </tr>")

        html_parts.append("    </table>")

    html_parts.extend([
        "</body>",
        "</html>"
    ])

    return "\n".join(html_parts)


def export_shot_list_html(shot_list: ShotList, path: str) -> None:
    """Export shot list as HTML file.

    Args:
        shot_list: ShotList to export
        path: File path to write to
    """
    html_content = generate_shot_list_html(shot_list)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def generate_shot_report(shot_list: ShotList) -> str:
    """Generate human-readable shot report.

    Args:
        shot_list: ShotList to report on

    Returns:
        Formatted report string
    """
    lines = []
    stats = shot_list.get_statistics()

    # Header
    lines.append("=" * 70)
    lines.append(f"SHOT LIST REPORT: {shot_list.production}")
    lines.append("=" * 70)
    lines.append("")

    # Summary
    lines.append("SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Total Scenes: {stats['total_scenes']}")
    lines.append(f"  Total Shots: {stats['total_shots']}")
    lines.append(f"  Estimated Duration: {stats['estimated_duration_minutes']:.1f} minutes")
    lines.append("")
    lines.append("  By Priority:")
    lines.append(f"    Essential: {stats['essential_shots']}")
    lines.append(f"    Recommended: {stats['recommended_shots']}")
    lines.append(f"    Optional: {stats['optional_shots']}")
    lines.append("")

    # Shots by size
    lines.append("  By Shot Size:")
    for size, count in sorted(stats['shots_by_size'].items()):
        lines.append(f"    {size.upper()}: {count}")
    lines.append("")

    # Shots by purpose
    lines.append("  By Purpose:")
    for purpose, count in sorted(stats['shots_by_purpose'].items()):
        lines.append(f"    {purpose.capitalize()}: {count}")
    lines.append("")

    # Scene details
    lines.append("")
    lines.append("=" * 70)
    lines.append("SCENE BREAKDOWN")
    lines.append("=" * 70)

    for scene_num in sorted(shot_list.scenes.keys()):
        scene = shot_list.scenes[scene_num]
        lines.append("")
        lines.append(f"SCENE {scene_num}: {scene.scene_heading}")
        lines.append("-" * 60)
        lines.append(f"  Shots: {scene.get_shot_count()} | Duration: {scene.estimated_duration:.1f}s")
        lines.append("")

        for shot in scene.shots:
            priority_marker = {
                "essential": "[!]",
                "recommended": "[*]",
                "optional": "[ ]"
            }.get(shot.priority, "[ ]")

            lines.append(f"  {priority_marker} {shot.get_shot_label()}: {shot.get_shot_size_name()}")
            lines.append(f"      Subject: {shot.subject}")
            lines.append(f"      Purpose: {_format_purpose(shot.purpose)} | {_format_camera_move(shot.camera_move)}")
            if shot.description:
                lines.append(f"      {shot.description}")
            if shot.notes:
                lines.append(f"      Notes: {shot.notes}")
            lines.append("")

    # Legend
    lines.append("")
    lines.append("=" * 70)
    lines.append("LEGEND")
    lines.append("-" * 40)
    lines.append("  [!] Essential - Must have for basic coverage")
    lines.append("  [*] Recommended - Adds depth and flexibility")
    lines.append("  [ ] Optional - Nice to have, time permitting")
    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)


def generate_producer_summary(shot_list: ShotList) -> str:
    """Generate producer-friendly summary.

    Args:
        shot_list: ShotList to summarize

    Returns:
        Formatted summary string
    """
    stats = shot_list.get_statistics()

    lines = []
    lines.append(f"PRODUCTION: {shot_list.production}")
    lines.append(f"Date: {shot_list.date_created or datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("SHOT LIST OVERVIEW")
    lines.append("-" * 40)
    lines.append(f"Scenes: {stats['total_scenes']}")
    lines.append(f"Total Shots: {stats['total_shots']}")
    lines.append(f"Estimated Shoot Time: {stats['estimated_duration_minutes']:.1f} minutes")
    lines.append("")
    lines.append("COVERAGE BREAKDOWN")
    lines.append(f"  Minimum (Essential): {stats['essential_shots']} shots")
    lines.append(f"  Standard (+Recommended): {stats['essential_shots'] + stats['recommended_shots']} shots")
    lines.append(f"  Full Coverage (+Optional): {stats['total_shots']} shots")

    return "\n".join(lines)


def _format_angle(angle: str) -> str:
    """Format camera angle for display."""
    angle_names = {
        "eye_level": "Eye Level",
        "high": "High",
        "low": "Low",
        "dutch": "Dutch",
        "birds_eye": "Bird's Eye",
        "worms_eye": "Worm's Eye"
    }
    return angle_names.get(angle.lower(), angle.title())


def _format_purpose(purpose: str) -> str:
    """Format purpose for display."""
    purpose_names = {
        "coverage": "Coverage",
        "reaction": "Reaction",
        "insert": "Insert",
        "establishing": "Establishing",
        "transition": "Transition",
        "cutaway": "Cutaway",
        "point_of_view": "POV",
        "over_shoulder": "OTS"
    }
    return purpose_names.get(purpose.lower(), purpose.title())


def _format_camera_move(move: str) -> str:
    """Format camera move for display."""
    if not move:
        return "Static"
    move_names = {
        "static": "Static",
        "pan": "Pan",
        "tilt": "Tilt",
        "dolly": "Dolly",
        "crane": "Crane",
        "handheld": "Handheld",
        "steadicam": "Steadicam",
        "zoom": "Zoom"
    }
    return move_names.get(move.lower(), move.title())


# Export all
__all__ = [
    "export_shot_list_csv",
    "export_shot_list_csv_string",
    "export_shot_list_yaml",
    "export_shot_list_yaml_string",
    "export_shot_list_json",
    "export_shot_list_pdf",
    "export_shot_list_html",
    "generate_shot_list_html",
    "generate_shot_report",
    "generate_producer_summary",
]
