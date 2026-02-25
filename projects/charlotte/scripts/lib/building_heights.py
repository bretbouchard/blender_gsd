"""
Charlotte Digital Twin - Building Heights Database

Accurate heights for Charlotte Uptown buildings from public records.
Source: Wikipedia, CTBUH, Charlotte Business Journal
Last updated: 2026-02-24
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class BuildingHeight:
    """Data structure for a building's height information."""
    name: str
    height_m: float  # Height in meters
    height_ft: float  # Height in feet
    floors: int
    year_built: int
    lat: Optional[float] = None  # Approximate latitude
    lon: Optional[float] = None  # Approximate longitude
    address: Optional[str] = None
    neighborhood: str = "Uptown"
    notes: str = ""


# =============================================================================
# CHARLOTTE UPTOWN SKYCRAPERS - Complete Height Database
# =============================================================================

CHARLOTTE_BUILDINGS: List[BuildingHeight] = [
    # =========================================================================
    # TIER 1: SUPERTALL (500+ ft / 150+ m)
    # =========================================================================

    BuildingHeight(
        name="Bank of America Corporate Center",
        height_m=265.0,
        height_ft=871,
        floors=60,
        year_built=1992,
        lat=35.2274,
        lon=-80.8435,
        address="100 N Tryon St",
        notes="Tallest in NC, 56th tallest in USA, tallest between Philadelphia and Atlanta"
    ),

    BuildingHeight(
        name="550 South Tryon",
        height_m=240.0,
        height_ft=786,
        floors=54,
        year_built=2010,
        lat=35.2248,
        lon=-80.8472,
        address="550 S Tryon St",
        notes="Formerly Duke Energy Center, largest by leasable sq ft (1.37M)"
    ),

    BuildingHeight(
        name="Truist Center",
        height_m=201.0,
        height_ft=659,
        floors=47,
        year_built=2002,
        lat=35.2269,
        lon=-80.8462,
        address="200 N College St",
        notes="Formerly Hearst Tower, tallest built in 2000s"
    ),

    BuildingHeight(
        name="Bank of America Tower",
        height_m=193.0,
        height_ft=632,
        floors=33,
        year_built=2019,
        lat=35.2261,
        lon=-80.8489,
        address="198 S College St",
        notes="Formerly Charlotte Metro Tower"
    ),

    BuildingHeight(
        name="Duke Energy Plaza",
        height_m=191.7,
        height_ft=629,
        floors=40,
        year_built=2023,
        lat=35.2278,
        lon=-80.8452,
        address="400 S Tryon St",
        notes="New Duke Energy HQ, completed 2023"
    ),

    # =========================================================================
    # TIER 2: HIGH-RISE (400-500 ft / 120-150 m)
    # =========================================================================

    BuildingHeight(
        name="301 South College",
        height_m=179.0,
        height_ft=588,
        floors=42,
        year_built=1988,
        lat=35.2252,
        lon=-80.8450,
        address="301 S College St",
        notes="Tallest built in 1980s"
    ),

    BuildingHeight(
        name="The Vue",
        height_m=175.5,
        height_ft=576,
        floors=50,
        year_built=2010,
        lat=35.2301,
        lon=-80.8495,
        address="229 W 5th St",
        notes="Tallest residential in NC"
    ),

    BuildingHeight(
        name="One South at The Plaza",
        height_m=153.0,
        height_ft=503,
        floors=40,
        year_built=1974,
        lat=35.2258,
        lon=-80.8440,
        address="212 S Tryon St",
        notes="Also known as 1 Financial Place"
    ),

    BuildingHeight(
        name="1 Bank of America Center",
        height_m=148.0,
        height_ft=484,
        floors=32,
        year_built=2010,
        lat=35.2276,
        lon=-80.8491,
        address="150 N College St",
        notes="Connected to Ritz-Carlton"
    ),

    BuildingHeight(
        name="300 South Tryon",
        height_m=141.0,
        height_ft=463,
        floors=25,
        year_built=2017,
        lat=35.2238,
        lon=-80.8465,
        address="300 S Tryon St",
        notes="Anchored by Barings"
    ),

    BuildingHeight(
        name="121 West Trade",
        height_m=141.0,
        height_ft=462,
        floors=32,
        year_built=1990,
        lat=35.2279,
        lon=-80.8468,
        address="121 W Trade St",
        notes="Also known as Interstate Tower"
    ),

    BuildingHeight(
        name="Three Wells Fargo Center",
        height_m=137.0,
        height_ft=450,
        floors=32,
        year_built=2000,
        lat=35.2265,
        lon=-80.8458,
        address="401 S Tryon St",
        notes="Formerly Three First Union Center"
    ),

    BuildingHeight(
        name="201 North Tryon",
        height_m=136.3,
        height_ft=447,
        floors=30,
        year_built=1997,
        lat=35.2281,
        lon=-80.8438,
        address="201 N Tryon St",
        notes="Also known as IJL Financial Center"
    ),

    BuildingHeight(
        name="Museum Tower",
        height_m=136.3,
        height_ft=447,
        floors=42,
        year_built=2017,
        lat=35.2239,
        lon=-80.8421,
        address="401 S Brevard St",
        notes="Apartment tower atop Mint Museum"
    ),

    BuildingHeight(
        name="Two Wells Fargo Center",
        height_m=132.0,
        height_ft=433,
        floors=32,
        year_built=1971,
        lat=35.2262,
        lon=-80.8450,
        address="301 S College St",
        notes="Formerly Two First Union Center"
    ),

    BuildingHeight(
        name="Avenue",
        height_m=129.5,
        height_ft=425,
        floors=36,
        year_built=2007,
        lat=35.2245,
        lon=-80.8445,
        address="200 S Church St",
        notes=""
    ),

    BuildingHeight(
        name="400 South Tryon",
        height_m=128.0,
        height_ft=420,
        floors=32,
        year_built=1974,
        lat=35.2242,
        lon=-80.8468,
        address="400 S Tryon St",
        notes="Entered foreclosure 2024"
    ),

    # =========================================================================
    # TIER 3: MID-RISE (300-400 ft / 90-120 m)
    # =========================================================================

    BuildingHeight(
        name="Carillon Tower",
        height_m=120.0,
        height_ft=394,
        floors=24,
        year_built=1991,
        lat=35.2247,
        lon=-80.8438,
        address="227 W Trade St",
        notes=""
    ),

    BuildingHeight(
        name="Charlotte Plaza",
        height_m=119.0,
        height_ft=388,
        floors=28,
        year_built=1982,
        lat=35.2251,
        lon=-80.8432,
        address="201 S College St",
        notes=""
    ),

    BuildingHeight(
        name="The Ellis",
        height_m=117.0,
        height_ft=384,
        floors=33,
        year_built=2021,
        lat=35.2282,
        lon=-80.8425,
        address="220 E 4th St",
        notes="549 apartment units"
    ),

    BuildingHeight(
        name="Ally Charlotte Center",
        height_m=115.2,
        height_ft=378,
        floors=26,
        year_built=2021,
        lat=35.2254,
        lon=-80.8415,
        address="129 W Trade St",
        notes="Includes JW Marriott"
    ),

    BuildingHeight(
        name="FNB Tower Charlotte",
        height_m=113.0,
        height_ft=371,
        floors=30,
        year_built=2021,
        lat=35.2268,
        lon=-80.8410,
        address="401 S Brevard St",
        notes="196 luxury apartments + office"
    ),

    BuildingHeight(
        name="Honeywell Tower",
        height_m=101.0,
        height_ft=331,
        floors=23,
        year_built=2021,
        lat=35.2271,
        lon=-80.8428,
        address="855 S Mint St",
        notes="Honeywell HQ"
    ),

    BuildingHeight(
        name="525 North Tryon",
        height_m=100.6,
        height_ft=330,
        floors=19,
        year_built=1999,
        lat=35.2295,
        lon=-80.8425,
        address="525 N Tryon St",
        notes=""
    ),

    BuildingHeight(
        name="TradeMark",
        height_m=99.1,
        height_ft=325,
        floors=28,
        year_built=2007,
        lat=35.2285,
        lon=-80.8472,
        address="200 E Trade St",
        notes=""
    ),

    BuildingHeight(
        name="First Citizens Plaza",
        height_m=97.5,
        height_ft=320,
        floors=23,
        year_built=1987,
        lat=35.2267,
        lon=-80.8442,
        address="128 S Tryon St",
        notes=""
    ),

    # =========================================================================
    # HOTELS
    # =========================================================================

    BuildingHeight(
        name="The Westin Charlotte",
        height_m=89.3,
        height_ft=293,
        floors=25,
        year_built=2003,
        lat=35.2240,
        lon=-80.8415,
        address="601 S College St",
        notes="Largest hotel in Charlotte (700 rooms)"
    ),

    BuildingHeight(
        name="550 South",
        height_m=89.3,
        height_ft=293,
        floors=20,
        year_built=2009,
        lat=35.2232,
        lon=-80.8485,
        address="550 S Mint St",
        notes="Near Bank of America Stadium"
    ),

    BuildingHeight(
        name="Hilton Charlotte Center City",
        height_m=89.0,
        height_ft=292,
        floors=22,
        year_built=1990,
        lat=35.2258,
        lon=-80.8425,
        address="222 E 3rd St",
        notes="400 rooms"
    ),

    BuildingHeight(
        name="JW Marriott Charlotte",
        height_m=85.3,
        height_ft=280,
        floors=22,
        year_built=2021,
        lat=35.2255,
        lon=-80.8412,
        address="215 E Trade St",
        notes="381 rooms, part of Ally Charlotte Center"
    ),

    BuildingHeight(
        name="112 Tryon Plaza",
        height_m=85.3,
        height_ft=280,
        floors=22,
        year_built=1927,
        lat=35.2268,
        lon=-80.8436,
        address="112 N Tryon St",
        notes="Tallest built in 1920s, historic building"
    ),

    BuildingHeight(
        name="Charlotte Marriott City Center",
        height_m=76.8,
        height_ft=252,
        floors=19,
        year_built=1984,
        lat=35.2253,
        lon=-80.8430,
        address="100 W Trade St",
        notes="446 rooms, 2nd largest hotel"
    ),

    BuildingHeight(
        name="Ritz-Carlton Charlotte",
        height_m=69.1,
        height_ft=225,
        floors=17,
        year_built=2009,
        lat=35.2275,
        lon=-80.8490,
        address="201 E College St",
        notes="150 room luxury hotel"
    ),

    BuildingHeight(
        name="Kimpton Tryon Park",
        height_m=69.0,
        height_ft=226,
        floors=18,
        year_built=2017,
        lat=35.2250,
        lon=-80.8475,
        address="303 S Church St",
        notes="217 rooms"
    ),

    BuildingHeight(
        name="Le Méridien Charlotte",
        height_m=72.5,
        height_ft=238,
        floors=18,
        year_built=1973,
        lat=35.2235,
        lon=-80.8445,
        address="555 S McDowell St",
        notes="Formerly Blake Hotel, 300 rooms"
    ),

    # =========================================================================
    # RESIDENTIAL TOWERS
    # =========================================================================

    BuildingHeight(
        name="Ascent Uptown",
        height_m=103.0,
        height_ft=338,
        floors=33,
        year_built=2017,
        lat=35.2225,
        lon=-80.8405,
        address="315 E 2nd St",
        notes="32-story apartment tower"
    ),

    BuildingHeight(
        name="Catalyst",
        height_m=103.0,
        height_ft=338,
        floors=27,
        year_built=2009,
        lat=35.2220,
        lon=-80.8430,
        address="400 W Hill St",
        notes="462 units"
    ),

    BuildingHeight(
        name="The Arlington",
        height_m=94.5,
        height_ft=310,
        floors=24,
        year_built=2002,
        lat=35.2215,
        lon=-80.8420,
        address="421 N Cedar St",
        notes=""
    ),

    BuildingHeight(
        name="Skye",
        height_m=94.0,
        height_ft=310,
        floors=23,
        year_built=2013,
        lat=35.2230,
        lon=-80.8410,
        address="220 E 3rd St",
        notes="Condominiums"
    ),

    BuildingHeight(
        name="Bell Uptown Charlotte",
        height_m=84.9,
        height_ft=278,
        floors=22,
        year_built=2014,
        lat=35.2245,
        lon=-80.8400,
        address="425 N Church St",
        notes="352 apartment units"
    ),

    BuildingHeight(
        name="The Ascher North Tower",
        height_m=80.5,
        height_ft=264,
        floors=24,
        year_built=2015,
        lat=35.2290,
        lon=-80.8405,
        address="410 E 7th St",
        notes="Twin towers, 672 apartments combined"
    ),

    BuildingHeight(
        name="The Ascher South Tower",
        height_m=80.5,
        height_ft=264,
        floors=24,
        year_built=2017,
        lat=35.2285,
        lon=-80.8400,
        address="420 E 7th St",
        notes="Twin towers, 672 apartments combined"
    ),

    BuildingHeight(
        name="Uptown 550",
        height_m=68.0,
        height_ft=223,
        floors=21,
        year_built=2019,
        lat=35.2235,
        lon=-80.8385,
        address="550 N Stonewall St",
        notes="421 apartments"
    ),

    BuildingHeight(
        name="The Francis Apartments",
        height_m=70.1,
        height_ft=230,
        floors=19,
        year_built=1973,
        lat=35.2240,
        lon=-80.8395,
        address="400 N Church St",
        notes=""
    ),

    # =========================================================================
    # HISTORIC / SMALLER BUILDINGS
    # =========================================================================

    BuildingHeight(
        name="129 West Trade",
        height_m=76.2,
        height_ft=250,
        floors=17,
        year_built=1958,
        lat=35.2275,
        lon=-80.8458,
        address="129 W Trade St",
        notes="Tallest built in 1950s"
    ),

    BuildingHeight(
        name="Johnston Building",
        height_m=69.1,
        height_ft=225,
        floors=17,
        year_built=1924,
        lat=35.2265,
        lon=-80.8445,
        address="212 S Tryon St",
        notes="Historic landmark, was tallest when built"
    ),

    BuildingHeight(
        name="Charlotte-Mecklenburg Government Center",
        height_m=65.2,
        height_ft=214,
        floors=14,
        year_built=1988,
        lat=35.2230,
        lon=-80.8400,
        address="600 E 4th St",
        notes="Government building"
    ),

    BuildingHeight(
        name="440 South Church",
        height_m=64.7,
        height_ft=212,
        floors=16,
        year_built=2009,
        lat=35.2225,
        lon=-80.8470,
        address="440 S Church St",
        notes=""
    ),

    BuildingHeight(
        name="Regions 615",
        height_m=79.1,
        height_ft=260,
        floors=19,
        year_built=2017,
        lat=35.2242,
        lon=-80.8455,
        address="615 S College St",
        notes=""
    ),

    BuildingHeight(
        name="650 S Tryon",
        height_m=88.6,
        height_ft=291,
        floors=18,
        year_built=2020,
        lat=35.2220,
        lon=-80.8470,
        address="650 S Tryon St",
        notes="Legacy Union development"
    ),

    BuildingHeight(
        name="200 South Tryon",
        height_m=91.1,
        height_ft=299,
        floors=18,
        year_built=1961,
        lat=35.2255,
        lon=-80.8440,
        address="200 S Tryon St",
        notes="Tallest built in 1960s"
    ),

    # =========================================================================
    # SOUTH END (just outside Uptown, visible from race loop)
    # =========================================================================

    BuildingHeight(
        name="110 East",
        height_m=92.9,
        height_ft=305,
        floors=23,
        year_built=2024,
        lat=35.2180,
        lon=-80.8480,
        address="110 E Bland St",
        neighborhood="South End",
        notes="Largest building in South End"
    ),

    BuildingHeight(
        name="Lowe's Global Technology Center",
        height_m=108.8,
        height_ft=357,
        floors=23,
        year_built=2021,
        lat=35.2120,
        lon=-80.8520,
        address="243 S Brevard St",
        neighborhood="South End",
        notes="Tallest building outside Uptown"
    ),

    BuildingHeight(
        name="The Line",
        height_m=64.7,
        height_ft=212,
        floors=16,
        year_built=2022,
        lat=35.2170,
        lon=-80.8510,
        address="2150 Hawkins St",
        neighborhood="South End",
        notes="Next to Sycamore Brewing"
    ),
]


def get_building_heights_dict() -> Dict[str, BuildingHeight]:
    """Get all building heights as a dictionary keyed by name."""
    return {b.name: b for b in CHARLOTTE_BUILDINGS}


def get_buildings_by_height() -> List[BuildingHeight]:
    """Get buildings sorted by height (tallest first)."""
    return sorted(CHARLOTTE_BUILDINGS, key=lambda b: b.height_m, reverse=True)


def get_buildings_by_neighborhood(neighborhood: str) -> List[BuildingHeight]:
    """Get buildings filtered by neighborhood."""
    return [b for b in CHARLOTTE_BUILDINGS if b.neighborhood == neighborhood]


def get_tallest_buildings(n: int = 10) -> List[BuildingHeight]:
    """Get the N tallest buildings."""
    return get_buildings_by_height()[:n]


def get_building_height_stats() -> Dict:
    """Get statistics about building heights."""
    heights = [b.height_m for b in CHARLOTTE_BUILDINGS]

    return {
        'total_buildings': len(CHARLOTTE_BUILDINGS),
        'tallest': max(heights) if heights else 0,
        'shortest': min(heights) if heights else 0,
        'average': sum(heights) / len(heights) if heights else 0,
        'supertall_count': len([h for h in heights if h >= 150]),  # 500+ ft
        'highrise_count': len([h for h in heights if 90 <= h < 150]),  # 300-500 ft
        'midrise_count': len([h for h in heights if h < 90]),  # < 300 ft
    }


def find_nearest_building(lat: float, lon: float) -> Optional[BuildingHeight]:
    """Find the nearest building to given coordinates."""
    import math

    best_building = None
    best_distance = float('inf')

    for building in CHARLOTTE_BUILDINGS:
        if building.lat is None or building.lon is None:
            continue

        # Simple distance calculation
        dlat = building.lat - lat
        dlon = building.lon - lon
        dist = math.sqrt(dlat**2 + dlon**2)

        if dist < best_distance:
            best_distance = dist
            best_building = building

    return best_building


def export_building_heights_csv(output_path: str):
    """Export building heights to CSV."""
    import csv

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'name', 'height_m', 'height_ft', 'floors', 'year_built',
            'lat', 'lon', 'address', 'neighborhood', 'notes'
        ])

        for b in CHARLOTTE_BUILDINGS:
            writer.writerow([
                b.name, b.height_m, b.height_ft, b.floors, b.year_built,
                b.lat or '', b.lon or '', b.address or '',
                b.neighborhood, b.notes
            ])


if __name__ == '__main__':
    # Print statistics
    stats = get_building_height_stats()
    print("=" * 60)
    print("CHARLOTTE BUILDING HEIGHTS DATABASE")
    print("=" * 60)
    print(f"\nTotal buildings: {stats['total_buildings']}")
    print(f"Tallest: {stats['tallest']:.1f}m ({stats['tallest']*3.28:.0f} ft)")
    print(f"Shortest: {stats['shortest']:.1f}m ({stats['shortest']*3.28:.0f} ft)")
    print(f"Average: {stats['average']:.1f}m ({stats['average']*3.28:.0f} ft)")
    print(f"\nSupertall (150m+): {stats['supertall_count']}")
    print(f"High-rise (90-150m): {stats['highrise_count']}")
    print(f"Mid-rise (<90m): {stats['midrise_count']}")

    print("\n" + "=" * 60)
    print("TOP 20 TALLEST BUILDINGS")
    print("=" * 60)

    for i, b in enumerate(get_tallest_buildings(20), 1):
        print(f"{i:2}. {b.name:35} {b.height_ft:4} ft / {b.height_m:5.1f} m  ({b.floors} fl)")
