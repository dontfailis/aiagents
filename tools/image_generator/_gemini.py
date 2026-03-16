"""Shared Gemini Imagen helpers used by all image generation tools.

This module provides common utility functions for reading API keys, initializing
the Gemini client, generating images using Imagen 3, and saving the output bytes.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Load .env from project root if present
_root = Path(__file__).resolve().parent.parent.parent
_env_file = _root / ".env"
if _env_file.exists():
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

try:
    from google import genai
    from google.genai import types
except ImportError:
    sys.exit("Missing dependency. Run:  pip install google-genai")

IMAGEN_MODEL = "imagen-4.0-generate-001"


def get_api_key(cli_override: Optional[str] = None) -> str:
    """Retrieves the Gemini API key from the CLI or environment variables.

    Args:
        cli_override: An optional API key provided via command-line arguments.

    Returns:
        The validated API key string.

    SystemExit:
        If no API key is found either in `cli_override` or `GEMINI_API_KEY`.
    """
    key = cli_override or os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit(
            "Error: GEMINI_API_KEY not set.\n"
            "  Add it to ../.env, set it in the environment, or pass --api-key <key>"
        )
    return key


def make_client(api_key: str) -> genai.Client:
    """Initializes and returns a Gemini client.

    Args:
        api_key: The authenticated API key.

    Returns:
        A configured `genai.Client` instance.
    """
    return genai.Client(api_key=api_key)


def generate_images(
    client: genai.Client,
    prompt: str,
    count: int,
    aspect_ratio: str,
) -> list[bytes]:
    """Generates images using the Gemini Imagen model.

    Args:
        client: The initialized `genai.Client`.
        prompt: The descriptive language prompt to generate the image.
        count: The number of images to generate (1-4).
        aspect_ratio: The string aspect ratio to use (e.g., '16:9', '4:3', '1:1', '3:4', '9:16').

    Returns:
        A list of raw image bytes for each generated image.
    """
    response = client.models.generate_images(
        model=IMAGEN_MODEL,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=count,
            aspect_ratio=aspect_ratio,
            person_generation="allow_adult",
        ),
    )
    return [img.image.image_bytes for img in response.generated_images]  # type: ignore[union-attr]


def save_images(
    image_bytes_list: list[bytes],
    output_dir: Path,
    prefix: str,
) -> list[Path]:
    """Saves raw image bytes to the specified output directory.

    Filenames are formatted with a safe prefix, a timestamp, and an index.

    Args:
        image_bytes_list: A list of raw PNG image bytes.
        output_dir: A `Path` object representing the destination directory.
        prefix: A string used as the prefix for the generated filenames.

    Returns:
        A list of `Path` objects representing the locations of the saved files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_prefix = "".join(c if c.isalnum() or c in "-_" else "_" for c in prefix.lower())
    saved: list[Path] = []
    for i, data in enumerate(image_bytes_list):
        path = output_dir / f"{safe_prefix}_{timestamp}_{i + 1}.png"
        path.write_bytes(data)
        print(f"  Saved: {path}")
        saved.append(path)
    return saved


def run_generation(
    *,
    prompt: str,
    count: int,
    aspect_ratio: str,
    output_dir: Path,
    prefix: str,
    api_key: str,
    label: str,
) -> list[Path]:
    """Coordinates the end-to-end image generation and saving process.

    This acts as the primary pipeline, initializing the client, calling the API,
    and handling the file output logic while printing progress to stdout.

    Args:
        prompt: The descriptive language prompt for the image.
        count: The number of images to generate.
        aspect_ratio: The desired aspect ratio string (e.g., '16:9').
        output_dir: The destination directory `Path`.
        prefix: A string used to prefix the output filenames.
        api_key: The authenticated Gemini API key.
        label: A human-readable label used for progress logging.

    Returns:
        A list of `Path` objects referencing the downloaded images.
    """
    print(f"Generating {count} {label}(s)...")
    print(f"Prompt: {prompt}\n")
    client = make_client(api_key)
    images = generate_images(client, prompt, count, aspect_ratio)
    saved = save_images(images, output_dir, prefix)
    print(f"\nDone. {len(saved)} image(s) saved to {output_dir.resolve()}")
    return saved
