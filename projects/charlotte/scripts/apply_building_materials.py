"""
Charlotte Digital Twin - Building Material Application

Applies researched materials to buildings based on:
- Building name (for known skyscrapers)
- Building type (office, residential, hotel, etc.)
- Year built / era
- Height (taller = more modern materials)

Also creates material slots for:
- Primary facade
- Secondary facade
- Ground floor / base
- Window glazing
- Mullions / trim
"""

import bpy
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.building_materials import (
    BuildingMaterialType,
    BuildingEra,
    BuildingUse,
    BuildingStyle,
    BuildingMaterialParams,
    BUILDING_MATERIAL_DEFINITIONS,
    CHARLOTTE_BUILDING_STYLES,
    create_building_material,
    get_style_for_building,
    get_materials_for_style,
    create_all_building_materials,
)


class BuildingMaterialApplicator:
    """
    Applies materials to building objects in Blender.

    Works with buildings imported via 3_import_buildings.py
    """

    # Known building name to style mappings
    BUILDING_STYLE_OVERRIDES = {
        # Major Skyscrapers
        "bank of america corporate center": "modern_glass_tower",
        "bank of america corporate": "modern_glass_tower",
        "boa corporate center": "modern_glass_tower",
        "550 south tryon": "contemporary_glass_tower",
        "duke energy center": "contemporary_glass_tower",
        "duke energy plaza": "sustainable_tower",
        "truist center": "modern_glass_tower",
        "hearst tower": "modern_glass_tower",
        "one wells fargo": "postmodern_granite_office",
        "two wells fargo": "postmodern_granite_office",
        "three wells fargo": "postmodern_granite_office",
        "wells fargo center": "postmodern_granite_office",
        "charlotte plaza": "postmodern_mixed",
        "301 south college": "postmodern_granite_office",
        "201 south college": "postmodern_granite_office",

        # Residential Towers
        "the vue": "modern_residential_tower",
        "vue charlotte": "modern_residential_tower",
        "catalyst": "modern_residential_tower",
        "ascent": "contemporary_residential",
        "museum tower": "contemporary_residential",
        "the elan": "modern_residential_tower",
        "avenir": "contemporary_residential",
        "oleander": "contemporary_residential",

        # Hotels
        "ritz carlton": "luxury_hotel_glass",
        "ritz-carlton": "luxury_hotel_glass",
        "the ritz": "luxury_hotel_glass",
        "westin": "luxury_hotel_glass",
        "westin charlotte": "luxury_hotel_glass",
        "marriott": "business_hotel",
        "charlotte marriott": "business_hotel",
        "jw marriott": "luxury_hotel_glass",
        "hilton": "business_hotel",
        "hilton garden inn": "business_hotel",
        "hyatt": "business_hotel",
        "hyatt place": "business_hotel",
        "aloft": "business_hotel",
        "indigo": "business_hotel",
        "hotel indigo": "business_hotel",
        "doubletree": "business_hotel",
        "embassy suites": "business_hotel",
        "sheraton": "business_hotel",
        "intercontinental": "luxury_hotel_glass",
        "kimpton": "luxury_hotel_glass",

        # Historic
        "112 tryon": "historic_limestone",
        "112 tryon plaza": "historic_limestone",
        "johnston building": "historic_limestone",
        "johnston": "historic_limestone",
        "200 south tryon": "mid_century_modern",

        # Parking
        "parking": "parking_structure",
        "parking deck": "parking_structure",
        "parking garage": "parking_structure",

        # Government
        "charlotte-mecklenburg": "government_building",
        "government center": "government_building",
        "city hall": "government_building",
        "federal building": "government_building",
        "courthouse": "government_building",
        "county courthouse": "government_building",
    }

    def __init__(self):
        self.stats = {
            'total_buildings': 0,
            'materials_applied': 0,
            'styles_matched': 0,
            'default_applied': 0,
        }

    def apply_to_all_buildings(self):
        """Apply materials to all buildings in the scene."""
        print("\n" + "=" * 60)
        print("APPLYING BUILDING MATERIALS")
        print("=" * 60)

        # First create all base materials
        print("\nCreating base materials...")
        create_all_building_materials()

        # Get all building objects
        buildings = self._get_building_objects()
        self.stats['total_buildings'] = len(buildings)

        print(f"\nFound {len(buildings)} building objects")

        # Apply materials
        for i, obj in enumerate(buildings):
            self._apply_materials_to_building(obj)

            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(buildings)} buildings...")

        # Print summary
        self._print_summary()

    def _get_building_objects(self) -> List[bpy.types.Object]:
        """Get all building objects from the scene."""
        buildings = []

        for obj in bpy.context.scene.objects:
            # Check if it's a building by custom property
            if obj.get('building_type') or obj.get('osm_id'):
                # Exclude roads, etc.
                if not obj.get('road_class'):
                    buildings.append(obj)

        return buildings

    def _apply_materials_to_building(self, obj: bpy.types.Object):
        """Apply appropriate materials to a building object."""
        # Get building info
        building_name = obj.get('building_name', obj.name)
        building_type = obj.get('building_type', 'yes')
        height = obj.get('height', 10.0)
        levels = obj.get('building_levels', 3)

        # Get style
        style = self._get_building_style(building_name, building_type, height, levels)

        if style:
            self.stats['styles_matched'] += 1
        else:
            self.stats['default_applied'] += 1

        # Get materials for style
        materials = get_materials_for_style(style)

        # Clear existing materials
        obj.data.materials.clear()

        # Apply primary material
        if 'primary' in materials and materials['primary']:
            obj.data.materials.append(materials['primary'])

            # Store style info
            obj['material_style'] = style.name if style else 'default'
            obj['material_type'] = style.primary_material.value if style else 'unknown'

        # Add secondary material slot if present
        if 'secondary' in materials and materials['secondary']:
            obj.data.materials.append(materials['secondary'])

        # Add base material for ground floor
        if 'base' in materials and materials['base']:
            obj.data.materials.append(materials['base'])

        self.stats['materials_applied'] += 1

    def _get_building_style(
        self,
        building_name: str,
        building_type: str,
        height: float,
        levels: int
    ) -> BuildingStyle:
        """Determine the appropriate style for a building."""

        # Check for exact name match
        name_lower = building_name.lower()

        for known_name, style_key in self.BUILDING_STYLE_OVERRIDES.items():
            if known_name in name_lower:
                return CHARLOTTE_BUILDING_STYLES.get(style_key)

        # Determine by building type and characteristics
        use = self._determine_use(building_type, building_name)
        era = self._determine_era(height, levels, building_name)

        # Find matching style
        for style in CHARLOTTE_BUILDING_STYLES.values():
            if style.use == use and style.era == era:
                return style

        # Fallback by era
        for style in CHARLOTTE_BUILDING_STYLES.values():
            if style.era == era:
                return style

        # Final fallback
        return CHARLOTTE_BUILDING_STYLES.get("contemporary_glass_tower")

    def _determine_use(self, building_type: str, name: str) -> BuildingUse:
        """Determine building use from type and name."""
        name_lower = name.lower()

        # Check name for hints
        if any(h in name_lower for h in ['hotel', 'inn', 'suites', 'marriott', 'hilton', 'hyatt', 'westin', 'ritz']):
            return BuildingUse.HOTEL

        if any(r in name_lower for r in ['apartment', 'condo', 'residential', 'tower', 'the vue', 'catalyst', 'ascent']):
            return BuildingUse.RESIDENTIAL_TOWER

        if 'parking' in name_lower:
            return BuildingUse.PARKING

        if any(g in name_lower for g in ['government', 'courthouse', 'city hall', 'federal']):
            return BuildingUse.GOVERNMENT

        if any(r in name_lower for r in ['retail', 'shop', 'store', 'plaza']):
            return BuildingUse.RETAIL

        # Check building type
        type_mappings = {
            'apartments': BuildingUse.RESIDENTIAL_TOWER,
            'residential': BuildingUse.RESIDENTIAL_TOWER,
            'hotel': BuildingUse.HOTEL,
            'retail': BuildingUse.RETAIL,
            'commercial': BuildingUse.MIXED_USE,
            'office': BuildingUse.OFFICE_TOWER,
            'parking': BuildingUse.PARKING,
            'civic': BuildingUse.GOVERNMENT,
            'public': BuildingUse.GOVERNMENT,
        }

        return type_mappings.get(building_type, BuildingUse.OFFICE_TOWER)

    def _determine_era(self, height: float, levels: int, name: str) -> BuildingEra:
        """Estimate building era from characteristics."""
        name_lower = name.lower()

        # Historic names
        if any(h in name_lower for h in ['historic', '1920', '1930', '1940', 'classic']):
            return BuildingEra.HISTORIC

        # Very tall buildings are usually modern
        if height > 150:  # Over ~50 floors
            return BuildingEra.CONTEMPORARY

        if height > 100:  # Over ~30 floors
            return BuildingEra.MODERN

        if height > 60:  # Over ~18 floors
            return BuildingEra.POSTMODERN

        if height > 30:  # Over ~10 floors
            return BuildingEra.MODERN

        # Default to mid-century for shorter buildings
        return BuildingEra.MID_CENTURY

    def _print_summary(self):
        """Print application summary."""
        print("\n" + "=" * 60)
        print("MATERIAL APPLICATION SUMMARY")
        print("=" * 60)
        print(f"Total buildings: {self.stats['total_buildings']}")
        print(f"Materials applied: {self.stats['materials_applied']}")
        print(f"Styles matched: {self.stats['styles_matched']}")
        print(f"Default styles: {self.stats['default_applied']}")


class BuildingAccessoryGenerator:
    """
    Generates building accessories for visual detail.

    Creates:
    - Window frames (as separate geometry nodes input)
    - Rooftop mechanical units
    - Balconies for residential
    - Ground floor retail glazing
    """

    def __init__(self):
        self.accessory_stats = {
            'window_frames': 0,
            'rooftop_units': 0,
            'balconies': 0,
            'ground_glazing': 0,
        }

    def generate_accessories(self):
        """Generate accessories for all buildings."""
        print("\n" + "=" * 60)
        print("GENERATING BUILDING ACCESSORIES")
        print("=" * 60)

        buildings = self._get_tall_buildings()

        print(f"\nProcessing {len(buildings)} tall buildings for accessories...")

        for obj in buildings:
            self._generate_for_building(obj)

        self._print_summary()

    def _get_tall_buildings(self) -> List[bpy.types.Object]:
        """Get buildings tall enough to need accessories."""
        return [
            obj for obj in bpy.context.scene.objects
            if obj.get('height', 0) > 20  # Only buildings > 20m
            and obj.get('building_type')
            and not obj.get('road_class')
        ]

    def _generate_for_building(self, obj: bpy.types.Object):
        """Generate accessories for a single building."""
        height = obj.get('height', 10)
        building_type = obj.get('building_type', 'office')
        name = obj.get('building_name', obj.name).lower()

        # Rooftop units for tall buildings
        if height > 50:
            self._add_rooftop_unit(obj)

        # Balconies for residential
        if building_type in ('apartments', 'residential') or any(
            r in name for r in ['vue', 'catalyst', 'ascent', 'residential', 'tower']
        ):
            self._mark_for_balconies(obj)

        # Mark for window generation
        self._mark_for_window_frames(obj)

    def _add_rooftop_unit(self, obj: bpy.types.Object):
        """Add rooftop mechanical unit marker."""
        obj['has_rooftop_mech'] = True
        obj['rooftop_mech_type'] = 'hvac'
        self.accessory_stats['rooftop_units'] += 1

    def _mark_for_balconies(self, obj: bpy.types.Object):
        """Mark building for balcony generation."""
        obj['has_balconies'] = True
        obj['balcony_type'] = 'glass_railing'
        self.accessory_stats['balconies'] += 1

    def _mark_for_window_frames(self, obj: bpy.types.Object):
        """Mark building for window frame generation."""
        height = obj.get('height', 10)

        # Determine window pattern
        if height > 100:
            obj['window_pattern'] = 'curtain_wall'
        elif height > 50:
            obj['window_pattern'] = 'ribbon'
        else:
            obj['window_pattern'] = 'punched'

        self.accessory_stats['window_frames'] += 1

    def _print_summary(self):
        """Print accessory generation summary."""
        print("\n" + "=" * 60)
        print("ACCESSORY GENERATION SUMMARY")
        print("=" * 60)
        print(f"Window frame markers: {self.accessory_stats['window_frames']}")
        print(f"Rooftop unit markers: {self.accessory_stats['rooftop_units']}")
        print(f"Balcony markers: {self.accessory_stats['balconies']}")


def main():
    """Main entry point for material application."""
    import argparse

    parser = argparse.ArgumentParser(description='Apply materials to Charlotte buildings')
    parser.add_argument(
        '--accessories', '-a',
        action='store_true',
        help='Also generate accessory markers'
    )

    args = parser.parse_args()

    # Apply materials
    applicator = BuildingMaterialApplicator()
    applicator.apply_to_all_buildings()

    # Generate accessories if requested
    if args.accessories:
        generator = BuildingAccessoryGenerator()
        generator.generate_accessories()

    print("\nMaterial application complete!")


if __name__ == '__main__':
    main()
