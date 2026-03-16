"""Character Portrait Generator.

Generates 3-4 portrait options for a character, used in the Portrait Selection screen.
The generated images are 3:4 portrait-oriented PNGs showing the upper body and face.

Examples:
    Generate 4 portrait options:
        $ python generate_portrait.py \\
            --name "Kira" --archetype "Rogue" \\
            --description "A nimble woman in her 30s, dark hair, leather armor, scar on cheek" \\
            --world "Medieval Fantasy" --tone "Adventure" \\
            --count 4 --output ./portraits

Attributes:
    PROMPT_TEMPLATE (str): The base prompt template used for the Imagen portrait model.
"""

import argparse
from pathlib import Path

from _gemini import get_api_key, run_generation

PROMPT_TEMPLATE = (
    "Character portrait for a {world} setting with a {tone} tone. "
    "Character: {name}, a {archetype}. {description}. "
    "Style: detailed fantasy portrait, painterly illustration, dramatic lighting, "
    "high quality, face clearly visible, upper body shot, no text, no watermarks."
)


def main() -> None:
    """Parses command-line arguments and runs the character portrait generator."""
    parser = argparse.ArgumentParser(description="Generate character portrait options")
    parser.add_argument("--name",        required=True)
    parser.add_argument("--archetype",   required=True, help="e.g. Rogue, Scholar, Warrior")
    parser.add_argument("--description", required=True, help="Visual description / style cues")
    parser.add_argument("--world",       default="Medieval Fantasy")
    parser.add_argument("--tone",        default="Adventure")
    parser.add_argument("--count",       type=int, default=4, help="Number of options (1–4)")
    parser.add_argument("--output",      default="./portraits")
    parser.add_argument("--api-key",     default=None)
    args = parser.parse_args()

    prompt = PROMPT_TEMPLATE.format(
        name=args.name,
        archetype=args.archetype,
        description=args.description,
        world=args.world,
        tone=args.tone,
    )

    run_generation(
        prompt=prompt,
        count=max(1, min(4, args.count)),
        aspect_ratio="3:4",
        output_dir=Path(args.output),
        prefix=args.name,
        api_key=get_api_key(args.api_key),
        label="portrait",
    )


if __name__ == "__main__":
    main()
