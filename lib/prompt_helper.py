"""
Prompt Helper System for Tutorial Knowledge

Generates actionable prompts from the tutorial knowledge base.
Use with AI assistants to quickly apply tutorial techniques.

Usage:
    from lib.prompt_helper import TutorialPromptHelper

    helper = TutorialPromptHelper()
    prompt = helper.get_prompt_for_technique("volumetric_fog")
    prompt = helper.get_prompt_for_section(30)
    prompt = helper.search_techniques("particle animation")
"""

from __future__ import annotations
from typing import Optional, List, Dict
from pathlib import Path


class TutorialPromptHelper:
    """
    Generate actionable prompts from tutorial knowledge.

    Cross-references:
    - docs/BLENDER_51_TUTORIAL_KNOWLEDGE.md - Source of truth
    - lib/*.py - Codified implementations
    """

    # Technique index with section numbers and module references
    TECHNIQUES = {
        # Volumetric (Sections 25, 28, 29, 33)
        "volumetric_fog": {
            "sections": [25, 28],
            "module": "lib.volumetric",
            "classes": ["WorldFog"],
            "description": "Global volumetric fog using world volume scatter"
        },
        "god_rays": {
            "sections": [25, 33],
            "module": "lib.volumetric",
            "classes": ["GodRays"],
            "description": "Light rays through volumetric fog"
        },
        "video_projection": {
            "sections": [29, 33],
            "module": "lib.volumetric",
            "classes": ["VolumetricProjector"],
            "description": "Video projection through fog creating god rays"
        },

        # Particles (Section 30)
        "seamless_particles": {
            "sections": [30],
            "module": "lib.particles",
            "classes": ["SeamlessParticles", "NoiseAnimator"],
            "description": "Perfect looping particle animations"
        },
        "noise_animation": {
            "sections": [30],
            "module": "lib.particles",
            "classes": ["NoiseAnimator"],
            "description": "4D noise for seamless animation loops"
        },

        # Simulation (Section 38)
        "footprint_simulation": {
            "sections": [38],
            "module": "lib.simulation",
            "classes": ["FootprintSimulation"],
            "description": "Footprints and tracks in mud/snow"
        },
        "proximity_detection": {
            "sections": [38],
            "module": "lib.simulation",
            "classes": ["ProximityDetector"],
            "description": "Detect object contact for simulation triggers"
        },

        # Motion Graphics (Section 37)
        "text_animation": {
            "sections": [37],
            "module": "lib.mograph",
            "classes": ["TextAnimator"],
            "description": "After Effects-style text animation"
        },
        "trail_effect": {
            "sections": [37],
            "module": "lib.mograph",
            "classes": ["TrailEffect"],
            "description": "Motion trail/ghosting effect"
        },
        "per_character_animation": {
            "sections": [37],
            "module": "lib.mograph",
            "classes": ["PerCharacterAnimator"],
            "description": "Animate each character independently"
        },

        # Paths (Section 35)
        "shortest_path_optimization": {
            "sections": [35],
            "module": "lib.paths",
            "classes": ["ShortestPathOptimizer"],
            "description": "Reduce millions of vertices to thousands"
        },
        "spline_domain": {
            "sections": [35],
            "module": "lib.paths",
            "classes": ["SplineDomain"],
            "description": "Per-curve operations in geometry nodes"
        },

        # Growth (Section 34)
        "procedural_fern": {
            "sections": [34],
            "module": "lib.growth",
            "classes": ["FernGrower"],
            "description": "Procedural fern/plant growth"
        },
        "index_taper": {
            "sections": [34],
            "module": "lib.growth",
            "classes": ["IndexTaper"],
            "description": "Index-based scaling for tapered effects"
        },
    }

    def __init__(self, knowledge_base_path: Optional[str] = None):
        self.kb_path = knowledge_base_path or "docs/BLENDER_51_TUTORIAL_KNOWLEDGE.md"

    def get_prompt_for_technique(self, technique: str) -> str:
        """
        Generate an actionable prompt for a technique.

        Args:
            technique: Technique key (e.g., "volumetric_fog")

        Returns:
            Actionable prompt string
        """
        if technique not in self.TECHNIQUES:
            available = list(self.TECHNIQUES.keys())
            return f"Unknown technique '{technique}'. Available: {available}"

        info = self.TECHNIQUES[technique]
        sections = ", ".join(f"Section {s}" for s in info["sections"])

        return f"""# Task: Implement {technique.replace('_', ' ').title()}

## Description
{info["description"]}

## Knowledge Base Reference
{sections} in docs/BLENDER_51_TUTORIAL_KNOWLEDGE.md

## Module Reference
Module: {info["module"]}
Classes: {', '.join(info["classes"])}

## Example Usage
```python
from {info["module"]} import {', '.join(info["classes"])}

# Implementation based on tutorial techniques
```

## Instructions
1. Read the relevant sections from the knowledge base
2. Import the appropriate class from {info["module"]}
3. Configure the technique parameters
4. Apply to the scene/object
5. Verify results match tutorial expectations
"""

    def get_prompt_for_section(self, section: int) -> str:
        """
        Generate prompt from knowledge base section number.

        Args:
            section: Section number (e.g., 30)

        Returns:
            Actionable prompt string
        """
        # Find techniques for this section
        techniques = [
            name for name, info in self.TECHNIQUES.items()
            if section in info["sections"]
        ]

        if not techniques:
            return f"No codified techniques found for Section {section}"

        prompts = [self.get_prompt_for_technique(t) for t in techniques]
        return "\n---\n".join(prompts)

    def search_techniques(self, query: str) -> List[Dict]:
        """
        Search for techniques matching a query.

        Args:
            query: Search term (e.g., "particle", "animation")

        Returns:
            List of matching techniques
        """
        query = query.lower()
        matches = []

        for name, info in self.TECHNIQUES.items():
            if query in name.lower() or query in info["description"].lower():
                matches.append({
                    "name": name,
                    "description": info["description"],
                    "module": info["module"],
                    "sections": info["sections"]
                })

        return matches

    def get_all_techniques(self) -> Dict:
        """Get all available techniques."""
        return self.TECHNIQUES.copy()

    def get_quick_reference(self) -> str:
        """
        Get a quick reference card for all techniques.

        Returns:
            Formatted quick reference string
        """
        lines = ["# Tutorial Techniques Quick Reference\n"]

        # Group by category
        categories = {
            "Volumetric": ["volumetric_fog", "god_rays", "video_projection"],
            "Particles": ["seamless_particles", "noise_animation"],
            "Simulation": ["footprint_simulation", "proximity_detection"],
            "Motion Graphics": ["text_animation", "trail_effect", "per_character_animation"],
            "Paths": ["shortest_path_optimization", "spline_domain"],
            "Growth": ["procedural_fern", "index_taper"],
        }

        for category, techniques in categories.items():
            lines.append(f"\n## {category}\n")
            for tech in techniques:
                if tech in self.TECHNIQUES:
                    info = self.TECHNIQUES[tech]
                    sections = ", ".join(str(s) for s in info["sections"])
                    lines.append(f"- **{tech}**: {info['description']} (KB {sections})")

        return "\n".join(lines)


# Convenience function
def get_technique_prompt(technique: str) -> str:
    """Quick access to technique prompt."""
    helper = TutorialPromptHelper()
    return helper.get_prompt_for_technique(technique)


def search_tutorials(query: str) -> List[Dict]:
    """Quick search of tutorial techniques."""
    helper = TutorialPromptHelper()
    return helper.search_techniques(query)
