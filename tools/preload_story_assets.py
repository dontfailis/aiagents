#!/usr/bin/env python3
import argparse
import asyncio
import os
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_WEB_DIR = ROOT_DIR / "frontend-web"
if str(FRONTEND_WEB_DIR) not in sys.path:
    sys.path.insert(0, str(FRONTEND_WEB_DIR))

import main as frontend_main  # noqa: E402
from media_service import (  # noqa: E402
    GENERATED_MEDIA_DIR,
    build_scene_video_prompt,
    ensure_scene_audio,
    ensure_scene_image,
    generate_scene_video,
)


def build_video_relative_path(session_id: str, scene_number: int, narrative: str) -> Path:
    video_hash = uuid.uuid5(uuid.NAMESPACE_URL, f"{session_id}:{scene_number}:{narrative}").hex[:16]
    return Path("videos") / "sessions" / session_id / f"scene_{scene_number}_{video_hash}.mp4"


async def ensure_scene_assets(
    *,
    session_id: str,
    scene_number: int,
    narrative: str,
    world: dict[str, Any],
    character: dict[str, Any],
    include_video: bool,
) -> dict[str, Any]:
    image_url = ensure_scene_image(
        session_id,
        scene_number,
        narrative,
        world,
        frontend_main.PUBLIC_API_BASE_URL,
    )
    audio_url = ensure_scene_audio(
        session_id,
        scene_number,
        narrative,
        frontend_main.PUBLIC_API_BASE_URL,
    )

    video_url = None
    if include_video:
        relative_path = build_video_relative_path(session_id, scene_number, narrative)
        absolute_path = GENERATED_MEDIA_DIR / relative_path
        prompt = build_scene_video_prompt(narrative, world, character)
        ok = await asyncio.to_thread(
            generate_scene_video,
            path=absolute_path,
            prompt=prompt,
        )
        if ok:
            video_url = f"{frontend_main.PUBLIC_API_BASE_URL.rstrip('/')}/generated/{relative_path.as_posix()}"

    return {
        "image_url": image_url,
        "audio_url": audio_url,
        "video_url": video_url,
    }


async def build_branch_tree(
    *,
    session_id: str,
    world: dict[str, Any],
    character: dict[str, Any],
    history: list[dict[str, Any]],
    selected_choice: dict[str, Any] | None,
    scene_number: int,
    depth: int,
    include_video: bool,
) -> dict[str, Any]:
    scene = await frontend_main.generate_story_scene_with_gemini(
        world,
        character,
        history,
        selected_choice,
        scene_number,
    )
    assets = await ensure_scene_assets(
        session_id=session_id,
        scene_number=scene_number,
        narrative=scene["narrative"],
        world=world,
        character=character,
        include_video=include_video,
    )

    node = {
        "scene_number": scene_number,
        "narrative": scene["narrative"],
        "choices": scene["choices"],
        **assets,
        "branches": {},
    }

    if depth <= 0:
        return node

    next_history_base = history + [{
        "scene_number": scene_number,
        "narrative": scene["narrative"],
        "choice": "",
    }]

    for choice in scene["choices"]:
        next_history = next_history_base[:-1] + [{
            "scene_number": scene_number,
            "narrative": scene["narrative"],
            "choice": choice["text"],
        }]
        node["branches"][str(choice["id"])] = await build_branch_tree(
            session_id=session_id,
            world=world,
            character=character,
            history=next_history,
            selected_choice=choice,
            scene_number=scene_number + 1,
            depth=depth - 1,
            include_video=include_video,
        )

    return node


async def preload_session(
    session: dict[str, Any],
    *,
    branch_depth: int,
    include_video: bool,
) -> dict[str, Any]:
    session_id = session["id"]
    world = frontend_main.get_world_from_local_db(session.get("world_id", ""))
    character = frontend_main.get_character_from_local_db(session.get("character_id", ""))
    if not world or not character:
        raise RuntimeError(f"Session {session_id} is missing world or character data")

    session = frontend_main.enrich_session_media(session)
    current_scene = session.get("current_scene", {}) or {}
    scene_number = int(current_scene.get("scene_number") or 1)
    narrative = current_scene.get("narrative", "")
    if not narrative:
        raise RuntimeError(f"Session {session_id} has no current scene narrative")

    current_assets = await ensure_scene_assets(
        session_id=session_id,
        scene_number=scene_number,
        narrative=narrative,
        world=world,
        character=character,
        include_video=include_video,
    )

    prefetched_choices: dict[str, Any] = {}
    precomputed_branches: dict[str, Any] = {}
    if branch_depth > 0:
        history = session.get("history", []) or []
        for choice in current_scene.get("choices", []) or []:
            branch_node = await build_branch_tree(
                session_id=session_id,
                world=world,
                character=character,
                history=history + [{
                    "scene_number": scene_number,
                    "narrative": narrative,
                    "choice": choice["text"],
                }],
                selected_choice=choice,
                scene_number=scene_number + 1,
                depth=branch_depth - 1,
                include_video=include_video,
            )
            prefetched_choices[str(choice["id"])] = {
                "scene_number": branch_node["scene_number"],
                "narrative": branch_node["narrative"],
                "choices": branch_node["choices"],
                "selected_choice_id": choice["id"],
                "selected_choice_text": choice["text"],
                "image_url": branch_node.get("image_url"),
                "audio_url": branch_node.get("audio_url"),
                "video_url": branch_node.get("video_url"),
            }
            precomputed_branches[str(choice["id"])] = branch_node

    updates = {
        "current_scene": {
            **current_scene,
            **{k: v for k, v in current_assets.items() if v},
        },
        "prefetched_choices": prefetched_choices,
        "prefetched_choice_ids": [int(choice_id) for choice_id in prefetched_choices.keys()],
        "prefetch_status": "ready",
        "precomputed_branches": precomputed_branches,
        "updated_at": frontend_main.now_iso(),
    }
    updated = frontend_main.update_local_document("sessions", session_id, updates)
    if not updated:
        raise RuntimeError(f"Failed to update session {session_id}")
    return updated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preload story assets for existing sessions.")
    parser.add_argument("--session-id", help="Only preload one session by id.")
    parser.add_argument(
        "--branch-depth",
        type=int,
        default=1,
        help="How many branch levels to precompute from the current scene. 1 means immediate next scenes.",
    )
    parser.add_argument(
        "--include-video",
        action="store_true",
        help="Also generate scene videos with Veo for the current scene and precomputed branches.",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    if args.branch_depth < 0:
        raise SystemExit("--branch-depth must be >= 0")

    db = frontend_main.load_local_db()
    sessions = list((db.get("sessions", {}) or {}).values())
    if args.session_id:
        sessions = [session for session in sessions if session.get("id") == args.session_id]

    if not sessions:
        print("No matching sessions found.")
        return 1

    print(
        f"Preloading {len(sessions)} session(s) with branch depth {args.branch_depth}. "
        f"Video generation is {'on' if args.include_video else 'off'}."
    )

    failures = 0
    for session in sessions:
        session_id = session["id"]
        try:
            print(f"[session {session_id}] starting")
            updated = await preload_session(
                session,
                branch_depth=args.branch_depth,
                include_video=args.include_video,
            )
            prefetched = len(updated.get("prefetched_choice_ids", []) or [])
            print(f"[session {session_id}] ready | prefetched_choices={prefetched}")
        except Exception as exc:
            failures += 1
            print(f"[session {session_id}] failed | {exc}")

    if failures:
        print(f"Completed with {failures} failure(s).")
        return 1

    print("All requested sessions were preloaded successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
