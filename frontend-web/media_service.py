import hashlib
import os
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.image_generator._gemini import generate_images, get_api_key, make_client
from tools.image_generator.generate_portrait import PROMPT_TEMPLATE as PORTRAIT_PROMPT_TEMPLATE
from tools.image_generator.generate_scene_art import PROMPT_TEMPLATE as SCENE_PROMPT_TEMPLATE
from tools.image_generator.generate_world_banner import PROMPT_TEMPLATE as WORLD_PROMPT_TEMPLATE

GENERATED_MEDIA_DIR = ROOT_DIR / "generated_media"
WORLD_MEDIA_DIR = GENERATED_MEDIA_DIR / "worlds"
CHARACTER_MEDIA_DIR = GENERATED_MEDIA_DIR / "characters"
SESSION_MEDIA_DIR = GENERATED_MEDIA_DIR / "sessions"


def ensure_media_dirs() -> None:
    for directory in (GENERATED_MEDIA_DIR, WORLD_MEDIA_DIR, CHARACTER_MEDIA_DIR, SESSION_MEDIA_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def _write_png(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _build_url(relative_path: Path, public_base_url: str) -> str:
    normalized_base = public_base_url.rstrip("/")
    return f"{normalized_base}/generated/{relative_path.as_posix()}"


def _hash_payload(*parts: str) -> str:
    digest = hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


def ensure_world_banner(world: dict[str, Any], public_base_url: str) -> str | None:
    ensure_media_dirs()
    prompt = WORLD_PROMPT_TEMPLATE.format(
        name=world.get("name", "Unnamed World"),
        setting=world.get("era", "Medieval Fantasy"),
        environment=world.get("environment", "kingdom"),
        era=world.get("era", "medieval"),
        tone=world.get("tone", "Adventure"),
    )
    world_hash = _hash_payload(
        world.get("id", ""),
        world.get("name", ""),
        world.get("era", ""),
        world.get("environment", ""),
        world.get("tone", ""),
        world.get("description", "") or "",
    )
    relative_path = Path("worlds") / world.get("id", world_hash) / f"{world_hash}.png"
    absolute_path = GENERATED_MEDIA_DIR / relative_path
    if not absolute_path.exists():
        try:
            client = make_client(get_api_key())
            image_bytes = generate_images(client, prompt, 1, "16:9")[0]
            _write_png(absolute_path, image_bytes)
        except Exception:
            return None

    return _build_url(relative_path, public_base_url)


def ensure_character_portraits(
    character: dict[str, Any],
    world: dict[str, Any],
    public_base_url: str,
    count: int = 4,
) -> list[str]:
    ensure_media_dirs()
    prompt = PORTRAIT_PROMPT_TEMPLATE.format(
        name=character.get("name", "Unnamed Character"),
        archetype=character.get("archetype", "Wanderer"),
        description=character.get("visual_description", "distinctive appearance"),
        world=world.get("era", "Medieval Fantasy"),
        tone=world.get("tone", "Adventure"),
    )
    character_hash = _hash_payload(
        character.get("id", ""),
        character.get("name", ""),
        character.get("archetype", ""),
        character.get("visual_description", ""),
        world.get("era", ""),
        world.get("tone", ""),
    )
    directory = CHARACTER_MEDIA_DIR / character.get("id", character_hash)
    paths = [directory / f"{character_hash}_{index + 1}.png" for index in range(count)]

    if not all(path.exists() for path in paths):
        try:
            client = make_client(get_api_key())
            generated = generate_images(client, prompt, count, "3:4")
            for path, image_bytes in zip(paths, generated):
                _write_png(path, image_bytes)
        except Exception:
            fallback = character.get("portrait_url")
            return [fallback] if fallback else []

    return [_build_url(path.relative_to(GENERATED_MEDIA_DIR), public_base_url) for path in paths]


def ensure_scene_image(
    session_id: str,
    scene_number: int,
    narrative: str,
    world: dict[str, Any],
    public_base_url: str,
) -> str | None:
    ensure_media_dirs()
    prompt = SCENE_PROMPT_TEMPLATE.format(
        world=world.get("era", "Medieval Fantasy"),
        tone=world.get("tone", "Adventure"),
        location=world.get("environment", "Unknown Region"),
        description=narrative,
    )
    scene_hash = _hash_payload(session_id, str(scene_number), narrative, world.get("environment", ""))
    relative_path = Path("sessions") / session_id / f"scene_{scene_number}_{scene_hash}.png"
    absolute_path = GENERATED_MEDIA_DIR / relative_path

    if not absolute_path.exists():
        try:
            client = make_client(get_api_key())
            image_bytes = generate_images(client, prompt, 1, "16:9")[0]
            _write_png(absolute_path, image_bytes)
        except Exception:
            return None

    return _build_url(relative_path, public_base_url)
