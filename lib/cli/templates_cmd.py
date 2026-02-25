"""
Templates Command

Lists and describes available project templates.

Usage:
    blender-gsd templates list
    blender-gsd templates info control-surface
"""

from __future__ import annotations
from typing import Dict, List, Optional

from .types import TEMPLATE_REGISTRY, TemplateInfo


class TemplatesCommand:
    """
    Manage and display project templates.
    """

    def __init__(self, cli_config=None):
        """Initialize command."""
        self.cli_config = cli_config

    def list_templates(self, category: Optional[str] = None) -> List[TemplateInfo]:
        """
        List all available templates.

        Args:
            category: Optional category filter

        Returns:
            List of template info objects
        """
        templates = list(TEMPLATE_REGISTRY.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return templates

    def get_template(self, template_id: str) -> Optional[TemplateInfo]:
        """
        Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Template info or None if not found
        """
        return TEMPLATE_REGISTRY.get(template_id)

    def get_template_categories(self) -> Dict[str, List[str]]:
        """
        Get templates organized by category.

        Returns:
            Dict mapping category to list of template IDs
        """
        categories: Dict[str, List[str]] = {}

        for template_id, info in TEMPLATE_REGISTRY.items():
            if info.category not in categories:
                categories[info.category] = []
            categories[info.category].append(template_id)

        return categories

    def format_template_list(self, templates: List[TemplateInfo]) -> str:
        """
        Format template list for display.

        Args:
            templates: List of templates to format

        Returns:
            Formatted string
        """
        output = []
        output.append("Available Templates:")
        output.append("-" * 60)

        for template in templates:
            output.append(f"  {template.template_id:20s} {template.name}")
            output.append(f"  {'':20s} {template.description[:50]}...")
            output.append(f"  {'':20s} Category: {template.category}")
            output.append("")

        return "\n".join(output)

    def format_template_info(self, template: TemplateInfo) -> str:
        """
        Format detailed template info for display.

        Args:
            template: Template to format

        Returns:
            Formatted string
        """
        output = []
        output.append(f"Template: {template.name}")
        output.append("=" * 60)
        output.append(f"ID: {template.template_id}")
        output.append(f"Category: {template.category}")
        output.append(f"Description: {template.description}")
        output.append("")

        output.append("Features:")
        for feature in template.features:
            output.append(f"  - {feature}")
        output.append("")

        output.append("Files Created:")
        for file in template.files:
            output.append(f"  - {file}")
        output.append("")

        if template.requires:
            output.append("Requires:")
            for req in template.requires:
                output.append(f"  - {req}")
            output.append("")

        return "\n".join(output)
