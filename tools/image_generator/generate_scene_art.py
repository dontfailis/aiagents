"""Scene Illustration Generator.

Generates an atmospheric illustration for a story scene during a play session.

Used on:
  * Story Play screen (one illustration per scene or per session opening)
  * End-of-Session Summary screen

Each scene gets a mood-setting background illustration that matches the narrative
without dominating the text - no foreground characters so the player's character
description remains primary.

Examples:
    Generate a tavern illustration:
        $ python generate_scene_art.py \\
            --description "A rain-soaked dockside tavern at midnight, shadowy figures huddled at tables" \\
            --location "Harbor District" \\
            --world "Medieval Fantasy" \\
            --tone "Intrigue" \\
            --output ./scenes

Attributes:
    PROMPT_TEMPLATE (str): The prompt template used to generate the scene.
"""

import argparse
from pathlib import Path

try:
    from ._gemini import get_api_key, run_generation
except ImportError:
    from _gemini import get_api_key, run_generation

PROMPT_TEMPLATE = (
    "Atmospheric scene illustration for a {world} story with a {tone} tone. "
    "Location: {location}. Scene: {description}. "
    "Style: painterly illustration, cinematic composition, dramatic atmospheric lighting, "
    "detailed environment, no foreground characters, immersive background, "
    "concept art quality, no text, no watermarks."
)


def main() -> None:
    """Parses command-line arguments and runs the scene illustration generator."""
    parser = argparse.ArgumentParser(description="Generate a story scene illustration")
    parser.add_argument("--description", required=True,
                        help="Narrative description of the scene environment")
    parser.add_argument("--location",    required=True,
                        help="Named location in the world (e.g. Harbor District)")
    parser.add_argument("--world",       default="Medieval Fantasy")
    parser.add_argument("--tone",        default="Adventure",
                        choices=["Adventure", "Exploration", "Intrigue", "Survival"])
    parser.add_argument("--session-id",  default="scene",
                        help="Used as filename prefix (e.g. session ID or scene number)")
    parser.add_argument("--output",      default="./scenes")
    parser.add_argument("--api-key",     default=None)
    args = parser.parse_args()

    prompt = PROMPT_TEMPLATE.format(
        world=args.world,
        tone=args.tone,
        location=args.location,
        description=args.description,
    )

    run_generation(
        prompt=prompt,
        count=1,
        aspect_ratio="16:9",
        output_dir=Path(args.output),
        prefix=args.session_id,
        api_key=get_api_key(args.api_key),
        label="scene illustration",
    )


if __name__ == "__main__":
    main()
