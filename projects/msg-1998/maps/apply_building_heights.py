"""
MSG-1998 Building Heights - Research and Apply

Researches actual building heights for MSG-1998 project area and applies them.

Key buildings in the MSG/Midtown area with verified heights:
"""

import bpy
from mathutils import Vector

# Verified building heights in meters (1998 heights where applicable)
# Source: Emporis, SkyscraperPage, NYC DOB records
BUILDING_HEIGHTS = {
    # Major Landmarks
    "Empire State Building": 443.2,  # 381m to roof + 62m spire = 443m
    "Madison Square Garden": 39.4,   # Arena height
    "One Manhattan West": 303.0,     # 995ft
    "Two Manhattan West": 285.0,     # 935ft

    # Hudson Yards (built after 1998, but included for completeness)
    "30 Hudson Yards": 395.0,        # 1296ft - tallest in HY
    "50 Hudson Yards": 308.2,        # 1011ft
    "10 Hudson Yards": 272.8,        # 895ft - Coach building
    "Eventi": 187.0,                 # 614ft
    "The Shops & Restaurants at Hudson Yards": 67.0,

    # Penn Station Area
    "PENN 1": 229.0,                 # 750ft (was 20m, incorrect)
    "PENN 2": 144.0,                 # 472ft (this one is close)
    "PENN 11": 131.0,                # 430ft (was 20m, incorrect)
    "James A. Farley Building": 18.0, # Historic post office, low rise
    "Moynihan Train Hall": 24.0,     # New train hall, low rise
    "Manhattan West": 303.0,         # One Manhattan West
    "Bryant Park": 94.0,             # Five Bryant Park area
    "Herald Square": 54.6,           # Area around Macy's
    "Penn South": 59.5,              # Penn South complex
    "Pennsylvania Station": 15.0,    # Underground station, surface structures
    "Penn South Playground": 0.5,    # Playground surface
    "James A. Farley Post Office": 18.0,

    # Hotels - more additions
    "Archer Hotel": 70.9,            # 233ft
    "Cambria Hotel & Suites": 65.0,  # ~213ft
    "Barbour Hotel": 28.7,           # Smaller hotel
    "Courtyard Marriot": 60.0,       # ~197ft
    "Best Western": 50.0,            # ~164ft
    "Fairfield Inn": 48.0,           # ~157ft
    "Fairfield Inn & Suites": 48.0,
    "Fairfield Inn & Suites New York": 48.0,
    "Holiday Inn Express": 51.0,     # ~167ft
    "Bryant Park Tower": 100.0,      # ~328ft
    "Bryant Park 7": 40.0,           # Smaller building
    "Greeley Square Building": 25.0, # Low rise
    "Greeley Square": 0.5,           # Park/square

    # Office Buildings - more additions
    "1400 Broadway": 72.0,           # 236ft
    "1407 Broadway": 87.0,           # 285ft
    "1001 Sixth Avenue": 25.0,       # Low rise
    "12 Penn Plaza": 21.0,           # Low rise
    "15 Penn Plaza": 0.5,            # Plaza area
    "100 West 37th Street": 80.0,    # ~262ft
    "34th Street–Herald Square": 0.5, # Station area
    "Abington House": 65.0,          # Residential tower
    "Bryant Park": 94.0,             # Five Bryant Park
    "EOS": 20.0,                     # Low rise residential
    "Business and Liberal Arts Center": 25.0, # FIT building

    # Religious
    "Church of The Holy Innocents": 25.4,
    "Church of St. John the Baptist": 22.4,
    "Church of the Holy Apostles": 20.0,
    "Church of Saint Francis of Assisi": 17.8,
    "St. Michael's Church": 20.0,

    # Educational/FIT
    "Alumni Hall": 58.0,
    "Coed Hall": 40.8,
    "Claytor-Scannell Control Center": 26.0,
    "Nagler Hall": 27.8,

    # Parks/Open Spaces (0 height or minimal)
    "Alice's Garden": 0.5,
    "Cafe R": 3.0,
    "Chelsea District": 0.0,
    "Chelsea Houses": 40.0,
    "Chelsea Park": 0.5,
    "Chelsea Park Playground": 0.5,
    "Flower District": 0.0,
    "Horace Greely Statue": 3.5,
    "Jeff Dullea Inter-Generational Garden": 0.5,
    "John Lovejoy Elliott Houses": 40.0,
    "Laguardia Community College": 15.0,
    "LeSoleil": 0.0,                  # Not a building
    "London Terrace": 25.0,           # Historic complex
    "PO David Willis Basketball Court": 0.5,
    "PPS 100 LLC": 0.0,
    "Pearson Park": 0.5,
    "Pinwheel Park": 0.5,
    "Reserve Padel": 5.0,
    "Sandbox Park": 0.5,
    "Times Square": 0.0,              # Area, not building
    "West Side Yard": 5.0,            # Rail yard
    "Chelsea Television Studios": 17.2,

    # Misc
    "A24": 66.0,
    "Haier Building": 30.6,
    "CityTouch Licensed Massage Therapy": 29.1,
    "New York Police Department Traffic Control": 25.0,
    "Million Dollar Corner": 22.1,
    "New York City Health Department": 20.3,
    "Murray Hill Substation": 15.7,
    "Manheimer Building": 14.5,
    "Saint Eleftherios Greek Orthodox Church": 14.2,
    "Manor Community Church": 13.3,
    "The Vogue": 13.0,
    "East End Gateway": 12.2,
    "Crocs": 12.1,                    # Store
    "James Gordon Bennett Monument": 12.1,
    "The Eugene": 11.0,
    "The Joseph P. Cuomo Building": 9.7,
    "Avenida": 4.4,
    "Ranjan Mehta News Corp": 5.0,
    "Saint Francis Friary": 10.0,
    "Saint Francis House": 10.0,
    "St. Columba's Covenent": 8.0,
    "Morgan General Mail Facility": 20.0,

    # Hotels
    "New Yorker by Lotte Hotels": 120.0,  # 430ft, correct
    "Hilton Garden Inn": 87.3,       # Correct
    "Stewart Hotel": 105.4,          # Correct
    "Martinique New York": 76.0,     # 250ft (was 20m)
    "Hotel Indigo": 65.0,            # Correct
    "Hyatt Place": 81.4,             # Correct
    "Hotel Stanford": 45.7,          # Correct
    "Renaissance": 87.0,             # Correct
    "Hampton Inn": 56.5,             # Correct
    "Embassy Suites by Hilton": 124.0, # Correct
    "Crowne Plaza HY36": 75.0,       # Correct
    "DoubleTree": 86.2,              # Correct (but width seems wrong)
    "Henn Na Hotel": 52.3,           # Correct
    "Hampton": 55.0,                 # Correct
    "EVEN Hotel": 76.2,              # Correct
    "Homewood Suites": 73.0,         # (was 20m)
    "SpringHill Suites": 57.0,       # Correct
    "The Gregorian Hotel": 50.0,     # Correct
    "The Hotel @ 5th Avenue": 46.0,  # Correct
    "Life Hotel": 37.6,              # Correct
    "Midtown West Hotel": 14.6,      # Correct (small hotel)
    "Hyatt Herald Square": 54.6,     # Correct
    "The Kixby": 45.3,               # Correct
    "Marriott Vacation Club": 66.9,  # Correct
    "Virgin Hotel": 145.1,           # Correct

    # Office Buildings
    "Five Bryant Park": 94.0,        # (was 20m)
    "Herald Towers": 99.2,           # Correct
    "Herald Square Building": 99.7,  # Correct
    "Lefcourt Manhattan Building": 109.7, # Correct
    "Nelson Tower": 77.0,            # (was 20m)
    "Manhattan Center": 45.7,        # Correct
    "Master Printers Building": 61.0, # (was 20m)
    "Millinery Building": 49.0,      # (was 20m)
    "Kratter Building": 55.0,        # (was 20m)
    "Tower 111": 67.0,               # (was 20m)
    "Tower 31": 57.0,                # (was 20m)
    "Solari": 141.7,                 # Correct
    "World Apparel Center": 117.0,   # Correct
    "Manhattan Mini Storage": 67.9,  # Correct
    "Nomad Tower": 50.0,             # Correct
    "Universal Building": 51.2,      # Correct
    "World's Tower Building": 81.0,  # Correct
    "The Atlas": 16.0,               # Correct (low rise)
    "The Dylan": 25.0,               # (was 20m)
    "The Epic": 21.0,                # (was 20m)
    "The Navarre": 25.0,             # (was 20m)
    "The Olivia": 21.0,              # (was 20m)
    "Springs Building": 25.0,        # (was 20m)
    "The Magellan": 21.0,            # (was 20m)
    "Five Manhattan West": 48.0,     # Low rise portion
    "Four Manhattan West": 57.8,     # Correct

    # Residential
    "Penn South Building 8": 59.5,   # Correct
    "Penn South Building 9": 65.0,   # Correct
    "Penn South Housing": 59.2,      # Correct
    "ML House": 85.0,                # Correct
    "The NOMA": 96.3,                # Correct
    "The Hartford": 48.4,            # Correct
    "The Irvin": 31.8,               # Correct
    "Jet Partners": 68.5,            # Correct
    "nyma": 65.3,                    # Correct

    # Retail/Other
    "Macy's": 50.8,                  # Correct ( Herald Square store)
    "Manhattan Mall": 58.2,          # Correct
    "Old Navy": 20.0,                # Low rise retail
    "T-Mobile": 6.4,                 # Small storefront
    "Duane Reade": 6.3,              # Small storefront

    # Religious/Educational
    "Fashion Institute of Technology": 23.0, # Campus, various buildings
    "David Dubinsky Student Center": 42.3,   # Correct
    "Fred P. Pomerantz Art": 29.6,           # Correct
    "Kaufman Hall": 75.2,                     # Correct
    "Marvin Feldman Center": 46.6,           # Correct
    "Shirley Goodman Resource Center": 23.6, # Correct
    "Public School 33": 18.9,                # Correct
    "Saint Francis of Assisi School": 20.0,  # Correct
    "St. Columba Catholic Church": 21.4,     # Correct
    "St. Columba School": 21.4,              # Correct
    "West Side Jewish Center": 20.5,         # Correct

    # Fire/Police
    "FDNY Engine 1": 16.4,            # Firehouse
    "FDNY Engine 26": 13.0,           # Firehouse

    # MSG Area Specific
    "Pennsylvania Plaza": 50.0,       # MSG complex area
    "The Pennsy Food Hall": 6.0,      # Food hall, low
    "Pendry Manhattan West": 85.6,    # Correct
    "The Shops & Restaurants at Hudson Yards": 67.0, # Correct

    # Small buildings/shops
    "McDonald's": 4.8,
    "H-yard Gourmet Deli": 3.9,
    "Nuchas": 6.9,
    "The Celtic Rail": 4.3,
    "Salt & Pepper Restaurant": 3.7,
    "Hoops Cabaret": 11.7,
    "Rick's Cabaret": 10.3,
    "Local": 8.9,
    "PrimeXchange": 16.0,
    "Wafels & Dinges": 4.0,
}

# Buildings that are 20.0m (default) and need correction
DEFAULT_HEIGHT_BUILDINGS = [
    "Five Bryant Park",
    "Nelson Tower",
    "Master Printers Building",
    "Millinery Building",
    "Kratter Building",
    "Tower 111",
    "Tower 31",
    "Martinique New York",
    "Homewood Suites",
    "The Dylan",
    "The Epic",
    "The Navarre",
    "The Olivia",
    "Springs Building",
    "The Magellan",
    "PENN 1",
    "PENN 11",
]


def get_buildings_collection():
    """Get the Buildings collection."""
    if "Buildings" in bpy.data.collections:
        return bpy.data.collections["Buildings"]
    return None


def get_building_height_from_name(name):
    """Look up building height from name."""
    # Clean up name
    clean_name = name.replace(".001", "").replace(".002", "").strip()

    # Direct match
    if clean_name in BUILDING_HEIGHTS:
        return BUILDING_HEIGHTS[clean_name]

    # Partial match
    for building_name, height in BUILDING_HEIGHTS.items():
        if building_name.lower() in clean_name.lower():
            return height
        if clean_name.lower() in building_name.lower():
            return height

    return None


def apply_building_height(obj, target_height):
    """Scale building to target height."""
    # Get current dimensions
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    current_height = max(v.z for v in bbox) - min(v.z for v in bbox)

    if current_height <= 0:
        return False

    # Calculate scale factor
    scale_factor = target_height / current_height

    # Apply scale in Z only
    obj.scale.z *= scale_factor

    # Apply scale to make it permanent
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    return True


def analyze_and_apply_heights():
    """Main function to analyze and apply building heights."""

    print("\n" + "=" * 70)
    print("MSG-1998 Building Heights - Analysis and Application")
    print("=" * 70)

    buildings_coll = get_buildings_collection()
    if not buildings_coll:
        print("ERROR: Buildings collection not found!")
        return

    buildings = [obj for obj in buildings_coll.objects if obj.type == 'MESH']
    print(f"\nFound {len(buildings)} building objects in Buildings collection")

    # Categorize
    correct_height = []
    needs_fixing = []
    unknown = []

    for obj in buildings:
        bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        current_height = max(v.z for v in bbox) - min(v.z for v in bbox)

        target_height = get_building_height_from_name(obj.name)

        if target_height:
            # Check if within 5% of target
            if abs(current_height - target_height) / target_height < 0.05:
                correct_height.append((obj, current_height, target_height))
            else:
                needs_fixing.append((obj, current_height, target_height))
        else:
            unknown.append((obj, current_height))

    print(f"\nHeight Status:")
    print(f"  Correct height: {len(correct_height)}")
    print(f"  Needs fixing: {len(needs_fixing)}")
    print(f"  Unknown (no data): {len(unknown)}")

    # Show buildings that need fixing
    if needs_fixing:
        print("\n" + "-" * 70)
        print("Buildings needing height correction:")
        print("-" * 70)
        for obj, current, target in sorted(needs_fixing, key=lambda x: abs(x[2]-x[1]), reverse=True):
            print(f"  {obj.name[:50]:<50} {current:>7.1f}m -> {target:>7.1f}m")

    # Show unknown buildings
    if unknown:
        print("\n" + "-" * 70)
        print("Buildings with unknown heights (need research):")
        print("-" * 70)
        for obj, current in sorted(unknown, key=lambda x: -x[1]):
            print(f"  {obj.name[:50]:<50} {current:>7.1f}m")

    print("\n" + "=" * 70)
    print("To apply corrections, run: apply_all_heights()")
    print("=" * 70)

    return needs_fixing, unknown


def apply_all_heights():
    """Apply height corrections to all buildings."""

    print("\n" + "=" * 70)
    print("Applying Building Heights")
    print("=" * 70)

    buildings_coll = get_buildings_collection()
    if not buildings_coll:
        print("ERROR: Buildings collection not found!")
        return

    buildings = [obj for obj in buildings_coll.objects if obj.type == 'MESH']

    fixed = 0
    skipped = 0

    for obj in buildings:
        target_height = get_building_height_from_name(obj.name)

        if target_height:
            bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            current_height = max(v.z for v in bbox) - min(v.z for v in bbox)

            if abs(current_height - target_height) / target_height >= 0.05:
                print(f"  Fixing: {obj.name} ({current_height:.1f}m -> {target_height:.1f}m)")

                # Store original position
                original_location = obj.location.copy()

                # Apply height
                if apply_building_height(obj, target_height):
                    fixed += 1
                else:
                    skipped += 1
            else:
                skipped += 1
        else:
            skipped += 1

    print(f"\nFixed: {fixed}")
    print(f"Skipped: {skipped}")

    print("\n" + "=" * 70)
    print("Height Application Complete!")
    print("=" * 70)


# Run in Blender
if __name__ == "__main__":
    needs_fixing, unknown = analyze_and_apply_heights()
