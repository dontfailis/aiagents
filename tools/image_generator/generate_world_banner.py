"""World Banner Generator.

Generates a wide cinematic banner/hero image for a world.

Used on:
  * Landing Page (hero background)
  * Create World (world type preview cards)
  * Join World (world header)
  * World Chronicle header
  * "While You Were Away" header

Examples:
    Run the generation for a specific world:
        $ python generate_world_banner.py \\
            --name "The Shattered Realm" \\
            --setting "Medieval Fantasy" \\
            --environment "kingdom" \\
            --era "medieval" \\
            --tone "Adventure" \\
            --output ./banners

Attributes:
    PROMPT_TEMPLATE (str): The prompt template used for the Imagen model.
    WORLD_TYPE_PRESETS (dict[str, str]): Preset prompt overrides for specific world types.
"""

import argparse
from pathlib import Path

try:
    from ._gemini import get_api_key, run_generation
except ImportError:
    from _gemini import get_api_key, run_generation

PROMPT_TEMPLATE = (
    "Wide cinematic establishing shot for a world called '{name}'. "
    "Setting: {setting}, Era: {era}, Environment: {environment}, Tone: {tone}. "
    "Style: sweeping fantasy landscape, painterly illustration, dramatic atmospheric lighting, "
    "epic scale, rich detail, no characters in foreground, no text, no watermarks, "
    "wide panoramic view, concept art quality."
)

# Preset prompts for the three MVP world type preview cards on Create World screen
WORLD_TYPE_PRESETS = {
    "Medieval Fantasy": (
        "Wide cinematic fantasy landscape, ancient kingdom with castles and forests, "
        "golden hour light, epic scale, painterly illustration, no text, no watermarks."
    ),
    "Post-Apocalyptic": (
        "Wide cinematic post-apocalyptic wasteland, ruined city skyline, dramatic stormy sky, "
        "desolate and atmospheric, painterly illustration, no text, no watermarks."
    ),
    "Modern Mystery": (
        "Wide cinematic modern city at night, rain-slicked streets, moody noir atmosphere, "
        "dramatic shadows and neon reflections, painterly illustration, no text, no watermarks."
    ),
}


def main() -> None:
    """Parses command-line arguments and runs the world banner generator."""
    parser = argparse.ArgumentParser(description="Generate world banner / hero art")
    parser.add_argument("--name",        default="Unnamed World")
    parser.add_argument("--setting",     default="Medieval Fantasy",
                        choices=["Medieval Fantasy", "Post-Apocalyptic", "Modern Mystery"])
    parser.add_argument("--environment", default="kingdom",
                        help="e.g. city, wilderness, kingdom, wasteland, space colony")
    parser.add_argument("--era",         default="medieval")
    parser.add_argument("--tone",        default="Adventure",
                        choices=["Adventure", "Exploration", "Intrigue", "Survival"])
    parser.add_argument("--preset",      action="store_true",
                        help="Generate preset cards for all 3 MVP world types")
    parser.add_argument("--output",      default="./banners")
    parser.add_argument("--api-key",     default=None)
    args = parser.parse_args()

    api_key = get_api_key(args.api_key)
    output_dir = Path(args.output)

    if args.preset:
        # Generate one preview card for each of the 3 MVP world types
        for world_type, prompt in WORLD_TYPE_PRESETS.items():
            run_generation(
                prompt=prompt,
                count=1,
                aspect_ratio="16:9",
                output_dir=output_dir / "presets",
                prefix=world_type.lower().replace(" ", "_"),
                api_key=api_key,
                label=f"{world_type} preset",
            )
    else:
        prompt = PROMPT_TEMPLATE.format(
            name=args.name,
            setting=args.setting,
            environment=args.environment,
            era=args.era,
            tone=args.tone,
        )
        run_generation(
            prompt=prompt,
            count=1,
            aspect_ratio="16:9",
            output_dir=output_dir,
            prefix=args.name,
            api_key=api_key,
            label="world banner",
        )


if __name__ == "__main__":
    main()
