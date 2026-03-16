import hashlib
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
PREVIEW_MEDIA_DIR = GENERATED_MEDIA_DIR / "previews"
PRESET_MEDIA_DIR = GENERATED_MEDIA_DIR / "presets"

WORLD_SETTING_PRESETS: dict[str, dict[str, str]] = {
    "medieval-fantasy": {
        "label": "Medieval Fantasy",
        "name": "Vesperhold",
        "era": "Medieval Fantasy",
        "environment": "a torchlit citadel above a misty harbor",
        "tone": "Adventure",
        "description": "Ancient kingdoms, magic, and mythical danger converge around a windswept stronghold at the edge of untamed lands.",
    },
    "post-apocalyptic": {
        "label": "Post-Apocalyptic",
        "name": "Afterglass",
        "era": "Post-Apocalyptic",
        "environment": "collapsed towers and a scavenger market under a yellow sky",
        "tone": "Survival",
        "description": "Civilization survives in hard fragments among brutal ruins, scavenger routes, and improvised settlements fighting over scarce resources.",
    },
    "modern-mystery": {
        "label": "Modern Mystery",
        "name": "Greywatch",
        "era": "Modern Mystery",
        "environment": "rain-slick downtown streets, shadowed alleys, and glowing office towers",
        "tone": "Intrigue",
        "description": "A contemporary city conceals conspiracies, secret societies, and investigative tension behind ordinary facades and cold streetlights.",
    },
}


def ensure_media_dirs() -> None:
    for directory in (
        GENERATED_MEDIA_DIR,
        WORLD_MEDIA_DIR,
        CHARACTER_MEDIA_DIR,
        SESSION_MEDIA_DIR,
        PREVIEW_MEDIA_DIR,
        PRESET_MEDIA_DIR,
    ):
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


def _generate_cached_images(
    *,
    paths: list[Path],
    prompt: str,
    count: int,
    aspect_ratio: str,
) -> bool:
    if all(path.exists() for path in paths):
        return True

    try:
        client = make_client(get_api_key())
        generated = generate_images(client, prompt, count, aspect_ratio)
    except Exception:
        return False

    for path, image_bytes in zip(paths, generated):
        _write_png(path, image_bytes)

    return all(path.exists() for path in paths)


def _world_prompt(payload: dict[str, Any]) -> str:
    return WORLD_PROMPT_TEMPLATE.format(
        name=payload.get("name", "Unnamed World"),
        setting=payload.get("era", "Medieval Fantasy"),
        environment=payload.get("environment", "kingdom"),
        era=payload.get("era", "medieval"),
        tone=payload.get("tone", "Adventure"),
    )


def _character_prompt(character: dict[str, Any], world: dict[str, Any]) -> str:
    description_parts = [character.get("visual_description", "distinctive appearance")]
    if character.get("backstory"):
        description_parts.append(character["backstory"])

    return PORTRAIT_PROMPT_TEMPLATE.format(
        name=character.get("name", "Unnamed Character"),
        archetype=character.get("archetype", "Wanderer"),
        description=". ".join(part.strip() for part in description_parts if part),
        world=world.get("era", "Medieval Fantasy"),
        tone=world.get("tone", "Adventure"),
    )


def ensure_world_banner(world: dict[str, Any], public_base_url: str) -> str | None:
    ensure_media_dirs()
    prompt = _world_prompt(world)
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
    if not _generate_cached_images(
        paths=[absolute_path],
        prompt=prompt,
        count=1,
        aspect_ratio="16:9",
    ):
        return None

    return _build_url(relative_path, public_base_url)


def ensure_character_portraits(
    character: dict[str, Any],
    world: dict[str, Any],
    public_base_url: str,
    count: int = 4,
) -> list[str]:
    ensure_media_dirs()
    prompt = _character_prompt(character, world)
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

    if not _generate_cached_images(
        paths=paths,
        prompt=prompt,
        count=count,
        aspect_ratio="3:4",
    ):
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

    if not _generate_cached_images(
        paths=[absolute_path],
        prompt=prompt,
        count=1,
        aspect_ratio="16:9",
    ):
        return None

    return _build_url(relative_path, public_base_url)


def ensure_world_setting_preset(setting_id: str, public_base_url: str) -> str | None:
    ensure_media_dirs()
    preset = WORLD_SETTING_PRESETS.get(setting_id)
    if not preset:
        return None

    relative_path = Path("presets") / "world-settings" / f"{setting_id}.png"
    absolute_path = GENERATED_MEDIA_DIR / relative_path
    if not _generate_cached_images(
        paths=[absolute_path],
        prompt=_world_prompt(preset),
        count=1,
        aspect_ratio="16:9",
    ):
        return None

    return _build_url(relative_path, public_base_url)


def generate_world_preview(world: dict[str, Any], public_base_url: str) -> str | None:
    ensure_media_dirs()
    preview_hash = _hash_payload(
        world.get("setting_id", "") or "",
        world.get("name", "") or "",
        world.get("era", "") or "",
        world.get("environment", "") or "",
        world.get("tone", "") or "",
        world.get("description", "") or "",
    )
    relative_path = Path("previews") / "worlds" / f"{preview_hash}.png"
    absolute_path = GENERATED_MEDIA_DIR / relative_path

    if not _generate_cached_images(
        paths=[absolute_path],
        prompt=_world_prompt(world),
        count=1,
        aspect_ratio="16:9",
    ):
        return None

    return _build_url(relative_path, public_base_url)


def generate_character_preview(
    character: dict[str, Any],
    world: dict[str, Any],
    public_base_url: str,
    count: int = 4,
) -> list[str]:
    ensure_media_dirs()
    preview_hash = _hash_payload(
        character.get("world_id", "") or "",
        character.get("name", "") or "",
        character.get("archetype", "") or "",
        character.get("visual_description", "") or "",
        character.get("backstory", "") or "",
        world.get("era", "") or "",
        world.get("tone", "") or "",
    )
    directory = PREVIEW_MEDIA_DIR / "characters"
    paths = [directory / f"{preview_hash}_{index + 1}.png" for index in range(count)]

    if not _generate_cached_images(
        paths=paths,
        prompt=_character_prompt(character, world),
        count=count,
        aspect_ratio="3:4",
    ):
        return []

    return [_build_url(path.relative_to(GENERATED_MEDIA_DIR), public_base_url) for path in paths]
