"""
Costume Bible Generator

Generate production costume bible documents.

Requirements:
- REQ-WARD-05: Costume bible generation

Part of Phase 10.1: Wardrobe System
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from .wardrobe_types import (
    Costume,
    CostumePiece,
    CostumeAssignment,
    WardrobeRegistry,
    CostumeCondition,
)


@dataclass
class ShoppingItem:
    """Item to purchase/acquire for production."""
    name: str
    category: str
    color: str
    material: str
    quantity: int = 1
    estimated_cost: float = 0.0
    vendor: str = ""
    status: str = "needed"  # needed, ordered, acquired, unavailable
    notes: str = ""
    for_costume: str = ""
    for_character: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "color": self.color,
            "material": self.material,
            "quantity": self.quantity,
            "estimated_cost": self.estimated_cost,
            "vendor": self.vendor,
            "status": self.status,
            "notes": self.notes,
            "for_costume": self.for_costume,
            "for_character": self.for_character,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShoppingItem":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            category=data.get("category", ""),
            color=data.get("color", ""),
            material=data.get("material", ""),
            quantity=data.get("quantity", 1),
            estimated_cost=data.get("estimated_cost", 0.0),
            vendor=data.get("vendor", ""),
            status=data.get("status", "needed"),
            notes=data.get("notes", ""),
            for_costume=data.get("for_costume", ""),
            for_character=data.get("for_character", ""),
        )


@dataclass
class CharacterWardrobe:
    """Complete wardrobe for a character."""
    character: str
    total_costumes: int
    costumes: List[Costume] = field(default_factory=list)
    scene_breakdown: List[Tuple[int, str, str]] = field(default_factory=list)  # scene, costume, condition
    color_theme: List[str] = field(default_factory=list)
    total_estimated_cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "character": self.character,
            "total_costumes": self.total_costumes,
            "costumes": [c.to_dict() for c in self.costumes],
            "scene_breakdown": [
                {"scene": s, "costume": c, "condition": cond}
                for s, c, cond in self.scene_breakdown
            ],
            "color_theme": self.color_theme,
            "total_estimated_cost": self.total_estimated_cost,
        }


@dataclass
class CostumeBible:
    """Production costume bible document."""
    production: str
    characters: Dict[str, CharacterWardrobe] = field(default_factory=dict)
    color_palettes: Dict[str, List[str]] = field(default_factory=dict)
    shopping_list: List[ShoppingItem] = field(default_factory=list)
    scene_breakdown: Dict[int, Dict[str, str]] = field(default_factory=dict)  # scene -> character -> costume
    generated_at: datetime = field(default_factory=datetime.now)
    total_budget: float = 0.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "production": self.production,
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "color_palettes": self.color_palettes,
            "shopping_list": [s.to_dict() for s in self.shopping_list],
            "scene_breakdown": {
                str(k): v for k, v in self.scene_breakdown.items()
            },
            "generated_at": self.generated_at.isoformat(),
            "total_budget": self.total_budget,
            "notes": self.notes,
        }


def generate_costume_bible(
    registry: WardrobeRegistry,
    production_name: str = "",
) -> CostumeBible:
    """Generate complete costume bible.

    Args:
        registry: Wardrobe registry
        production_name: Production name (defaults to registry name)

    Returns:
        Complete CostumeBible document
    """
    if not production_name:
        production_name = registry.production_name

    bible = CostumeBible(production=production_name)

    # Build character wardrobes
    for character in registry.get_all_characters():
        wardrobe = _build_character_wardrobe(character, registry)
        bible.characters[character] = wardrobe
        bible.total_budget += wardrobe.total_estimated_cost

    # Build color palettes per character
    for character, wardrobe in bible.characters.items():
        colors = _extract_color_palette(wardrobe)
        bible.color_palettes[character] = colors

    # Build scene breakdown
    scenes = registry.get_all_scenes()
    for scene in scenes:
        scene_assignments = registry.get_assignments_for_scene(scene)
        bible.scene_breakdown[scene] = {
            a.character: a.costume for a in scene_assignments
        }

    # Generate shopping list
    bible.shopping_list = generate_shopping_list(registry)

    return bible


def _build_character_wardrobe(
    character: str,
    registry: WardrobeRegistry,
) -> CharacterWardrobe:
    """Build wardrobe for a single character."""
    costumes = registry.get_costumes_for_character(character)
    assignments = sorted(
        registry.get_assignments_for_character(character),
        key=lambda a: a.scene,
    )

    # Build scene breakdown
    scene_breakdown = [
        (a.scene, a.costume, a.condition)
        for a in assignments
    ]

    # Extract color theme
    color_theme = _extract_character_colors(costumes)

    # Calculate total cost
    total_cost = sum(c.get_total_cost() for c in costumes)

    return CharacterWardrobe(
        character=character,
        total_costumes=len(costumes),
        costumes=costumes,
        scene_breakdown=scene_breakdown,
        color_theme=color_theme,
        total_estimated_cost=total_cost,
    )


def _extract_character_colors(costumes: List[Costume]) -> List[str]:
    """Extract dominant colors from character's costumes."""
    colors = set()
    for costume in costumes:
        colors.update(costume.colors)
        for piece in costume.get_all_pieces():
            colors.add(piece.color.lower())
    return sorted(list(colors))


def _extract_color_palette(wardrobe: CharacterWardrobe) -> List[str]:
    """Extract color palette from wardrobe."""
    return wardrobe.color_theme


def generate_shopping_list(registry: WardrobeRegistry) -> List[ShoppingItem]:
    """Generate shopping/acquisition list.

    Creates a consolidated list of all costume pieces needed,
    with quantities and estimated costs.

    Args:
        registry: Wardrobe registry

    Returns:
        List of shopping items
    """
    # Track pieces by unique identifier
    items_by_key: Dict[str, ShoppingItem] = {}

    for costume_name, costume in registry.costumes.items():
        for piece in costume.get_all_pieces():
            key = _make_piece_key(piece)

            if key in items_by_key:
                # Increment quantity
                items_by_key[key].quantity += piece.quantity
            else:
                # Create new item
                items_by_key[key] = ShoppingItem(
                    name=piece.name,
                    category=piece.category,
                    color=piece.color,
                    material=piece.material,
                    quantity=piece.quantity,
                    estimated_cost=piece.estimated_cost,
                    vendor=piece.brand,
                    status="needed",
                    notes=piece.notes,
                    for_costume=costume_name,
                    for_character=costume.character,
                )

    return list(items_by_key.values())


def _make_piece_key(piece: CostumePiece) -> str:
    """Create unique key for a costume piece."""
    return f"{piece.name}|{piece.category}|{piece.color}|{piece.material}".lower()


def export_bible_yaml(bible: CostumeBible, path: str) -> None:
    """Export bible as YAML.

    Args:
        bible: Costume bible
        path: Output file path
    """
    try:
        import yaml
        with open(path, "w") as f:
            yaml.dump(bible.to_dict(), f, default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback to JSON
        import json
        with open(path.replace(".yaml", ".json"), "w") as f:
            json.dump(bible.to_dict(), f, indent=2)


def export_bible_html(bible: CostumeBible, path: str) -> None:
    """Export bible as HTML.

    Args:
        bible: Costume bible
        path: Output file path
    """
    html = _generate_bible_html(bible)
    with open(path, "w") as f:
        f.write(html)


def _generate_bible_html(bible: CostumeBible) -> str:
    """Generate HTML content for costume bible."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Costume Bible - {bible.production}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 40px;
            background: #f5f5f5;
            color: #333;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .meta {{
            color: #666;
            margin-bottom: 30px;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        .character-section {{ margin-top: 30px; }}
        .costume-card {{
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            background: #fafafa;
        }}
        .costume-name {{
            font-weight: bold;
            color: #2980b9;
            font-size: 1.1em;
        }}
        .costume-condition {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            margin-left: 10px;
        }}
        .pristine {{ background: #d4edda; color: #155724; }}
        .worn {{ background: #fff3cd; color: #856404; }}
        .dirty {{ background: #d1ecf1; color: #0c5460; }}
        .damaged, .bloodied {{ background: #f8d7da; color: #721c24; }}
        .piece-list {{
            list-style: none;
            padding: 0;
            margin: 10px 0;
        }}
        .piece-list li {{
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }}
        .piece-category {{
            font-weight: bold;
            color: #666;
            width: 100px;
            display: inline-block;
        }}
        .color-swatch {{
            display: inline-block;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            margin-right: 5px;
            vertical-align: middle;
            border: 1px solid #ccc;
        }}
        .scene-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .scene-table th, .scene-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .scene-table th {{
            background: #3498db;
            color: white;
        }}
        .scene-table tr:nth-child(even) {{ background: #f9f9f9; }}
        .shopping-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .shopping-table th, .shopping-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        .shopping-table th {{ background: #27ae60; color: white; }}
        .status-needed {{ color: #e74c3c; }}
        .status-ordered {{ color: #f39c12; }}
        .status-acquired {{ color: #27ae60; }}
        .budget {{
            font-size: 1.5em;
            color: #27ae60;
            font-weight: bold;
        }}
        .color-palette {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin: 10px 0;
        }}
        .color-chip {{
            padding: 5px 15px;
            border-radius: 4px;
            background: #eee;
            font-size: 0.9em;
        }}
        @media print {{
            body {{ background: white; padding: 20px; }}
            .section {{ box-shadow: none; border: 1px solid #ddd; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Costume Bible</h1>
        <h2>{bible.production}</h2>
        <p class="meta">Generated: {bible.generated_at.strftime('%B %d, %Y at %H:%M')}</p>

        <div class="section">
            <h2>Overview</h2>
            <p><strong>Characters:</strong> {len(bible.characters)}</p>
            <p><strong>Total Scenes:</strong> {len(bible.scene_breakdown)}</p>
            <p><strong>Shopping Items:</strong> {len(bible.shopping_list)}</p>
            <p class="budget">Estimated Budget: ${bible.total_budget:,.2f}</p>
        </div>
"""

    # Character sections
    for character, wardrobe in bible.characters.items():
        html += f"""
        <div class="section character-section">
            <h2>{character}</h2>
            <p><strong>Costumes:</strong> {wardrobe.total_costumes}</p>
            <p><strong>Estimated Cost:</strong> ${wardrobe.total_estimated_cost:,.2f}</p>

            <div class="color-palette">
                <strong>Color Palette:</strong>
                {"".join(f'<span class="color-chip">{c}</span>' for c in wardrobe.color_theme[:10])}
            </div>
"""

        for costume in wardrobe.costumes:
            condition_class = costume.condition.lower()
            html += f"""
            <div class="costume-card">
                <span class="costume-name">{costume.name}</span>
                <span class="costume-condition {condition_class}">{costume.condition}</span>
                {f'<p><em>{costume.notes}</em></p>' if costume.notes else ''}

                <ul class="piece-list">
"""
            for piece in costume.pieces:
                html += f"""                    <li>
                        <span class="piece-category">{piece.category}:</span>
                        {piece.name} ({piece.color}, {piece.material})
                    </li>
"""
            if costume.accessories:
                html += """                    <li><strong>Accessories:</strong></li>
"""
                for acc in costume.accessories:
                    html += f"""                    <li style="padding-left: 20px;">
                        {acc.name} ({acc.color})
                    </li>
"""

            html += """                </ul>
            </div>
"""

        # Scene breakdown for character
        if wardrobe.scene_breakdown:
            html += """
            <h3>Scene Breakdown</h3>
            <table class="scene-table">
                <tr><th>Scene</th><th>Costume</th><th>Condition</th></tr>
"""
            for scene, costume, condition in wardrobe.scene_breakdown:
                html += f"""                <tr>
                    <td>{scene}</td>
                    <td>{costume}</td>
                    <td>{condition}</td>
                </tr>
"""
            html += """            </table>
"""

        html += """        </div>
"""

    # Shopping list
    if bible.shopping_list:
        html += f"""
        <div class="section">
            <h2>Shopping List</h2>
            <table class="shopping-table">
                <tr>
                    <th>Item</th>
                    <th>Category</th>
                    <th>Color</th>
                    <th>Qty</th>
                    <th>Est. Cost</th>
                    <th>For</th>
                    <th>Status</th>
                </tr>
"""
        for item in bible.shopping_list:
            status_class = f"status-{item.status}"
            html += f"""                <tr>
                    <td>{item.name}</td>
                    <td>{item.category}</td>
                    <td>{item.color}</td>
                    <td>{item.quantity}</td>
                    <td>${item.estimated_cost:,.2f}</td>
                    <td>{item.for_character}</td>
                    <td class="{status_class}">{item.status}</td>
                </tr>
"""

        html += """            </table>
        </div>
"""

    html += """
    </div>
</body>
</html>"""

    return html


def export_bible_pdf(bible: CostumeBible, path: str) -> bool:
    """Export bible as PDF.

    Requires either reportlab or weasyprint library.

    Args:
        bible: Costume bible
        path: Output file path

    Returns:
        True if successful, False otherwise
    """
    # Try weasyprint first
    try:
        from weasyprint import HTML
        html = _generate_bible_html(bible)
        HTML(string=html).write_pdf(path)
        return True
    except ImportError:
        pass

    # Try reportlab
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph(f"Costume Bible: {bible.production}", styles["Title"]))
        story.append(Paragraph(f"Generated: {bible.generated_at.strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 20))

        # Characters
        for character, wardrobe in bible.characters.items():
            story.append(Paragraph(f"{character}", styles["Heading2"]))
            story.append(Paragraph(f"Costumes: {wardrobe.total_costumes}", styles["Normal"]))
            story.append(Paragraph(f"Estimated Cost: ${wardrobe.total_estimated_cost:,.2f}", styles["Normal"]))
            story.append(Spacer(1, 10))

            for costume in wardrobe.costumes:
                story.append(Paragraph(f"  - {costume.name} ({costume.condition})", styles["Normal"]))

            story.append(Spacer(1, 20))

        doc.build(story)
        return True

    except ImportError:
        return False


def generate_scene_breakdown_csv(bible: CostumeBible) -> str:
    """Generate scene breakdown as CSV.

    Args:
        bible: Costume bible

    Returns:
        CSV string
    """
    lines = ["scene," + ",".join(sorted(bible.characters.keys()))]

    for scene in sorted(bible.scene_breakdown.keys()):
        row = [str(scene)]
        for character in sorted(bible.characters.keys()):
            costume = bible.scene_breakdown[scene].get(character, "")
            row.append(costume)
        lines.append(",".join(row))

    return "\n".join(lines)


def generate_costume_summary_csv(bible: CostumeBible) -> str:
    """Generate costume summary as CSV.

    Args:
        bible: Costume bible

    Returns:
        CSV string
    """
    lines = ["character,costume,pieces,condition,estimated_cost"]

    for character, wardrobe in bible.characters.items():
        for costume in wardrobe.costumes:
            lines.append(
                f'"{character}","{costume.name}",{costume.get_piece_count()},'
                f'"{costume.condition}",{costume.get_total_cost():.2f}'
            )

    return "\n".join(lines)
