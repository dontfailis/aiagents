"""Location Thumbnail Generator.

Generates a thumbnail image for each named location in the world map / region model.

Used on:
  * World Map / Region Model display (5-8 locations per world)
  * Location cards in session context header

Each world has 5-8 named locations (e.g., Harbor District, North City, Old Forest).
This tool generates one thumbnail per location, called once during world creation.

Examples:
    Generate one location:
        $ python generate_location_art.py \\
            --name "Harbor District" \\
            --description "A bustling port with crowded docks, fishing boats, and merchant warehouses" \\
            --world "Medieval Fantasy" \\
            --tone "Adventure" \\
            --output ./locations

    Generate all default locations for a world type at once:
        $ python generate_location_art.py \\
            --world "Medieval Fantasy" \\
            --generate-defaults \\
            --output ./locations

Attributes:
    PROMPT_TEMPLATE (str): The base prompt template used for the Imagen model.
    DEFAULT_LOCATIONS (dict[str, list[dict]]): A mapping of world types to default region locations.
"""

import argparse
from pathlib import Path

try:
    from ._gemini import get_api_key, run_generation
except ImportError:
    from _gemini import get_api_key, run_generation

PROMPT_TEMPLATE = (
    "Location thumbnail for '{name}' in a {world} world with a {tone} tone. "
    "{description}. "
    "Style: painterly illustration, establishing shot, detailed environment, "
    "atmospheric lighting, no characters visible, thumbnail composition, "
    "no text, no watermarks."
)

# Default locations from PRD Section 5.8 with descriptions per world type
DEFAULT_LOCATIONS: dict[str, list[dict]] = {
    "Medieval Fantasy": [
        {"name": "North City",         "description": "A fortified medieval city with stone walls and a central keep"},
        {"name": "Old Forest",         "description": "An ancient dense forest with gnarled trees and misty paths"},
        {"name": "Harbor District",    "description": "A bustling port with crowded docks, fishing boats, and merchant warehouses"},
        {"name": "Desert Pass",        "description": "A narrow canyon pass through a scorched desert with crumbling ruins"},
        {"name": "Mountain Keep",      "description": "A solitary fortress perched on a snow-capped mountain peak"},
        {"name": "River Settlement",   "description": "A small village built along a wide river with wooden bridges and mills"},
        {"name": "Borderlands",        "description": "Lawless frontier plains with scattered camps and watchtowers"},
        {"name": "Market Square",      "description": "A lively open-air market in the heart of a medieval town"},
    ],
    "Post-Apocalyptic": [
        {"name": "Ruins District",     "description": "Collapsed skyscrapers and rubble-strewn streets of a destroyed city"},
        {"name": "Survivor Camp",      "description": "A fortified camp of survivors built from scavenged materials"},
        {"name": "Wasteland Highway",  "description": "A cracked highway cutting through a barren radioactive wasteland"},
        {"name": "Underground Vault",  "description": "A dimly lit underground bunker with rusted corridors"},
        {"name": "Scavenger Market",   "description": "A chaotic outdoor market where survivors trade salvaged goods"},
        {"name": "Quarantine Zone",    "description": "A fenced-off area of the city marked with warning signs and hazmat tape"},
        {"name": "Power Plant",        "description": "An abandoned nuclear power plant with cooling towers and glowing pools"},
        {"name": "Outpost Bravo",      "description": "A remote military outpost on the edge of a toxic zone"},
    ],
    "Modern Mystery": [
        {"name": "Downtown",           "description": "Glass towers and busy streets of a modern city center at night"},
        {"name": "Old Quarter",        "description": "Narrow cobblestone streets lined with aged brick buildings"},
        {"name": "Police Precinct",    "description": "A grey brutalist police station with flickering fluorescent lights"},
        {"name": "Harbor Docks",       "description": "Fog-covered shipping docks with cranes and container stacks"},
        {"name": "Underground",        "description": "A labyrinthine network of tunnels beneath the city"},
        {"name": "University Campus",  "description": "Gothic university buildings surrounded by overgrown ivy"},
        {"name": "Industrial Zone",    "description": "Abandoned factories and warehouses on the edge of the city"},
        {"name": "Luxury District",    "description": "Gleaming penthouses and manicured streets of the wealthy elite"},
    ],
}


def main() -> None:
    """Parses arguments and runs the location thumbnail generator.

    Raises:
        SystemExit: If the required arguments (--name and --description) are missing
            when --generate-defaults is not specified.
    """
    parser = argparse.ArgumentParser(description="Generate world location thumbnails")
    parser.add_argument("--name",              default=None, help="Location name (single generation)")
    parser.add_argument("--description",       default=None, help="Visual description of the location")
    parser.add_argument("--world",             default="Medieval Fantasy",
                        choices=["Medieval Fantasy", "Post-Apocalyptic", "Modern Mystery"])
    parser.add_argument("--tone",              default="Adventure",
                        choices=["Adventure", "Exploration", "Intrigue", "Survival"])
    parser.add_argument("--generate-defaults", action="store_true",
                        help="Generate thumbnails for all default locations of the selected world type")
    parser.add_argument("--output",            default="./locations")
    parser.add_argument("--api-key",           default=None)
    args = parser.parse_args()

    api_key = get_api_key(args.api_key)
    output_dir = Path(args.output)

    if args.generate_defaults:
        locations = DEFAULT_LOCATIONS.get(args.world, [])
        for loc in locations:
            prompt = PROMPT_TEMPLATE.format(
                name=loc["name"],
                world=args.world,
                tone=args.tone,
                description=loc["description"],
            )
            run_generation(
                prompt=prompt,
                count=1,
                aspect_ratio="4:3",
                output_dir=output_dir / args.world.lower().replace(" ", "_"),
                prefix=loc["name"],
                api_key=api_key,
                label=f"location thumbnail ({loc['name']})",
            )
    else:
        if not args.name or not args.description:
            parser.error("--name and --description are required unless --generate-defaults is set")

        prompt = PROMPT_TEMPLATE.format(
            name=args.name,
            world=args.world,
            tone=args.tone,
            description=args.description,
        )
        run_generation(
            prompt=prompt,
            count=1,
            aspect_ratio="4:3",
            output_dir=output_dir,
            prefix=args.name,
            api_key=api_key,
            label="location thumbnail",
        )


if __name__ == "__main__":
    main()
