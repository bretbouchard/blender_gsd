"""
Asset Vault Category & Tag Management

YAML-driven categorization and auto-tagging system.
"""

from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .enums import AssetCategory
from .types import AssetInfo


# Default path for categories configuration
DEFAULT_CATEGORIES_YAML: str = "config/asset_categories.yaml"


@dataclass
class CategoryRule:
    """Rule for auto-categorizing assets."""
    patterns: List[str] = field(default_factory=list)  # Filename patterns (glob)
    keywords: List[str] = field(default_factory=list)  # Keyword matches
    category: AssetCategory = AssetCategory.UNKNOWN
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.8  # Default confidence for this rule

    def matches(self, asset: AssetInfo) -> Tuple[bool, float]:
        """
        Check if rule matches an asset.

        Args:
            asset: Asset to check

        Returns:
            Tuple of (matches, confidence)
        """
        # Check filename patterns
        for pattern in self.patterns:
            if fnmatch(asset.name.lower(), pattern.lower()):
                return True, self.confidence
            if fnmatch(str(asset.path).lower(), f"*{pattern.lower()}*"):
                return True, self.confidence * 0.9

        # Check keywords in name and path
        name_lower = asset.name.lower()
        path_lower = str(asset.path).lower()

        for keyword in self.keywords:
            if keyword.lower() in name_lower:
                return True, self.confidence * 0.95
            if keyword.lower() in path_lower:
                return True, self.confidence * 0.85

        return False, 0.0


class CategoryManager:
    """
    Manages category rules and auto-categorization.

    Rules are loaded from YAML configuration files.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the category manager.

        Args:
            config_path: Path to YAML configuration file
        """
        self.rules: List[CategoryRule] = []
        self._load_builtin_rules()

        if config_path:
            self.load_config(config_path)

    def _load_builtin_rules(self) -> None:
        """Load built-in category rules for common patterns."""
        builtin = [
            # KitBash3D packs
            CategoryRule(
                patterns=["*KitBash*", "*KB3D*", "*kitbash*"],
                keywords=["kitbash", "modular", "kit"],
                category=AssetCategory.KITBASH,
                tags=["modular", "kit", "assets"],
                confidence=0.95,
            ),
            # Vehicles
            CategoryRule(
                patterns=["*car*", "*truck*", "*vehicle*", "*mech*", "*robot*"],
                keywords=["car", "truck", "vehicle", "mech", "robot", "auto", "vitaly"],
                category=AssetCategory.VEHICLE,
                tags=["transportation", "mechanical"],
                confidence=0.9,
            ),
            # Sci-Fi
            CategoryRule(
                patterns=["*cyberpunk*", "*scifi*", "*sci-fi*", "*futuristic*"],
                keywords=["cyberpunk", "scifi", "futuristic", "neon", "tech"],
                category=AssetCategory.SCI_FI,
                tags=["futuristic", "technology"],
                confidence=0.9,
            ),
            # Architecture
            CategoryRule(
                patterns=["*building*", "*house*", "*architecture*"],
                keywords=["building", "house", "architecture", "structure"],
                category=AssetCategory.ARCHITECTURE,
                tags=["structure", "environment"],
                confidence=0.85,
            ),
            # VFX elements
            CategoryRule(
                patterns=["*fx*", "*vfx*", "*particle*", "*explosion*"],
                keywords=["vfx", "fx", "particle", "simulation", "effect"],
                category=AssetCategory.VFX,
                tags=["effects", "simulation"],
                confidence=0.85,
            ),
            # Characters
            CategoryRule(
                patterns=["*character*", "*human*", "*person*", "*figure*"],
                keywords=["character", "human", "person", "figure", "rigged"],
                category=AssetCategory.CHARACTER,
                tags=["rigged", "animated"],
                confidence=0.85,
            ),
            # Furniture
            CategoryRule(
                patterns=["*chair*", "*table*", "*sofa*", "*furniture*", "*desk*"],
                keywords=["chair", "table", "sofa", "furniture", "desk", "interior"],
                category=AssetCategory.FURNITURE,
                tags=["interior", "prop"],
                confidence=0.85,
            ),
            # Fantasy
            CategoryRule(
                patterns=["*fantasy*", "*medieval*", "*castle*", "*dragon*"],
                keywords=["fantasy", "medieval", "magic", "castle", "dragon"],
                category=AssetCategory.FANTASY,
                tags=["fantasy", "medieval"],
                confidence=0.85,
            ),
            # Environment
            CategoryRule(
                patterns=["*terrain*", "*landscape*", "*environment*", "*nature*"],
                keywords=["terrain", "landscape", "environment", "nature", "outdoor"],
                category=AssetCategory.ENVIRONMENT,
                tags=["outdoor", "landscape"],
                confidence=0.8,
            ),
            # Props
            CategoryRule(
                patterns=["*prop*", "*object*"],
                keywords=["prop"],
                category=AssetCategory.PROP,
                tags=["prop"],
                confidence=0.6,
            ),
        ]

        self.rules.extend(builtin)

    def load_config(self, path: Path) -> None:
        """
        Load category rules from YAML file.

        Args:
            path: Path to YAML configuration
        """
        path = Path(path)
        if not path.exists():
            return

        try:
            with open(path) as f:
                config = yaml.safe_load(f)

            if not config or "categories" not in config:
                return

            for cat_config in config["categories"]:
                rule = self._parse_rule(cat_config)
                if rule:
                    self.rules.append(rule)

            # Sort rules by confidence (highest first)
            self.rules.sort(key=lambda r: r.confidence, reverse=True)

        except Exception:
            pass  # Silently ignore config errors

    def _parse_rule(self, config: Dict[str, Any]) -> Optional[CategoryRule]:
        """Parse a category rule from config dict."""
        try:
            category = AssetCategory.from_string(config.get("name", "unknown"))
            return CategoryRule(
                patterns=config.get("patterns", []),
                keywords=config.get("keywords", []),
                category=category,
                tags=config.get("tags", []),
                confidence=config.get("confidence", 0.8),
            )
        except Exception:
            return None

    def auto_categorize(
        self,
        asset: AssetInfo,
    ) -> Tuple[AssetCategory, List[str], float]:
        """
        Automatically categorize an asset.

        Args:
            asset: Asset to categorize

        Returns:
            Tuple of (category, tags, confidence)
        """
        best_category = AssetCategory.UNKNOWN
        best_tags: List[str] = []
        best_confidence = 0.0

        for rule in self.rules:
            matches, confidence = rule.matches(asset)
            if matches and confidence > best_confidence:
                best_category = rule.category
                best_tags = rule.tags.copy()
                best_confidence = confidence

        return best_category, best_tags, best_confidence

    def add_rule(self, rule: CategoryRule) -> None:
        """
        Add a new category rule.

        Args:
            rule: Rule to add
        """
        self.rules.append(rule)
        # Re-sort by confidence
        self.rules.sort(key=lambda r: r.confidence, reverse=True)

    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags from all rules.

        Returns:
            Sorted list of unique tags
        """
        tags = set()
        for rule in self.rules:
            tags.update(rule.tags)
        return sorted(tags)

    def get_categories_for_tags(self, tags: List[str]) -> List[AssetCategory]:
        """
        Get categories that match a set of tags.

        Args:
            tags: Tags to match

        Returns:
            List of matching categories
        """
        categories = []
        tag_set = set(t.lower() for t in tags)

        for rule in self.rules:
            rule_tags = set(t.lower() for t in rule.tags)
            if tag_set & rule_tags:  # Intersection
                if rule.category not in categories:
                    categories.append(rule.category)

        return categories


def load_categories_yaml(path: Path) -> List[CategoryRule]:
    """
    Load category rules from YAML file.

    Args:
        path: Path to YAML file

    Returns:
        List of CategoryRule objects
    """
    manager = CategoryManager(path)
    return manager.rules


def auto_categorize_asset(
    asset: AssetInfo,
    config_path: Optional[Path] = None,
) -> Tuple[AssetCategory, List[str], float]:
    """
    Convenience function to auto-categorize a single asset.

    Args:
        asset: Asset to categorize
        config_path: Optional path to categories config

    Returns:
        Tuple of (category, tags, confidence)
    """
    manager = CategoryManager(config_path)
    return manager.auto_categorize(asset)
