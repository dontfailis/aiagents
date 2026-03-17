from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Any
import uuid
import httpx
import os
import json
import secrets
import string
import asyncio
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import SendMessageRequest, MessageSendParams
from google import genai
from google.genai import types
from media_service import (
    GENERATED_MEDIA_DIR,
    build_scene_video_prompt,
    ensure_character_portraits,
    ensure_media_dirs,
    ensure_scene_audio,
    ensure_scene_image,
    ensure_world_banner,
    ensure_world_setting_preset,
    generate_scene_video,
    generate_character_preview,
    generate_world_preview,
)

app = FastAPI()

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DB_PATH = os.path.join(ROOT_DIR, "mcp-server", "test_db.json")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
FRONTEND_ORIGIN_ALT = os.getenv("FRONTEND_ORIGIN_ALT", "http://127.0.0.1:5173")
PUBLIC_API_BASE_URL = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000")

ensure_media_dirs()
app.mount("/generated", StaticFiles(directory=str(GENERATED_MEDIA_DIR)), name="generated")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, FRONTEND_ORIGIN_ALT],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cloud Run injects these via terraform main.tf modifications
AGENT_CREATEWORLD_URL = os.getenv("AGENT_CREATEWORLD_URL", "http://localhost:10001")
AGENT_CREATECHARACTER_URL = os.getenv("AGENT_CREATECHARACTER_URL", "http://localhost:10002")
AGENT_NARRATIVE_URL = os.getenv("AGENT_NARRATIVE_URL", "http://localhost:10003")
AGENT_OPTIONGEN_URL = os.getenv("AGENT_OPTIONGEN_URL", "http://localhost:10004")
PREFETCH_TASKS: dict[str, asyncio.Task] = {}
VIDEO_TASKS: dict[str, asyncio.Task] = {}
VIDEO_STATUS: dict[str, dict] = {}
GEMINI_STORY_MODEL = os.getenv("GEMINI_STORY_MODEL", "gemini-2.5-pro")
GEMINI_OPTION_MODEL = os.getenv("GEMINI_OPTION_MODEL", GEMINI_STORY_MODEL)
GEMINI_SUMMARY_MODEL = os.getenv("GEMINI_SUMMARY_MODEL", GEMINI_STORY_MODEL)
_GEMINI_CLIENT: genai.Client | None = None

def extract_jsonish_from_a2a_parts(parts: Any) -> str:
    def unwrap_part(part: Any) -> Any:
        if part is None:
            return None

        root = getattr(part, "root", None)
        if root is not None:
            return root

        if hasattr(part, "model_dump"):
            try:
                dumped = part.model_dump()
            except Exception:
                dumped = None
            if isinstance(dumped, dict) and dumped.get("root") is not None:
                return dumped["root"]

        return part

    def serialize_payload(payload: Any) -> str:
        if payload is None:
            return ""

        text = getattr(payload, "text", None)
        if text:
            return text

        data = getattr(payload, "data", None)
        if data is not None:
            return json.dumps(data)

        file_value = getattr(payload, "file", None)
        if file_value is not None:
            if hasattr(file_value, "model_dump"):
                try:
                    return json.dumps(file_value.model_dump())
                except Exception:
                    return str(file_value)
            return str(file_value)

        if isinstance(payload, dict):
            if payload.get("text"):
                return payload["text"]
            if payload.get("data") is not None:
                return json.dumps(payload["data"])
            if payload.get("file") is not None:
                return json.dumps(payload["file"])

        if hasattr(payload, "model_dump"):
            try:
                dumped = payload.model_dump()
            except Exception:
                dumped = None
            if isinstance(dumped, dict):
                if dumped.get("text"):
                    return dumped["text"]
                if dumped.get("data") is not None:
                    return json.dumps(dumped["data"])
                if dumped.get("file") is not None:
                    return json.dumps(dumped["file"])
                return json.dumps(dumped)

        return ""

    serialized_parts = []
    for part in parts or []:
        serialized = serialize_payload(unwrap_part(part))
        if serialized:
            serialized_parts.append(serialized)

    return "\n".join(item.strip() for item in serialized_parts if item).strip()


def extract_jsonish_from_a2a_message(message: Any) -> str:
    if message is None:
        return ""

    direct_text = extract_jsonish_from_a2a_parts(getattr(message, "parts", None) or [])
    if direct_text:
        return direct_text

    content = getattr(message, "content", None)
    return extract_jsonish_from_a2a_parts(getattr(content, "parts", None) or [])


def extract_jsonish_from_a2a_artifacts(artifacts: Any) -> str:
    artifact_payloads = []
    for artifact in artifacts or []:
        artifact_payload = extract_jsonish_from_a2a_parts(getattr(artifact, "parts", None) or [])
        if not artifact_payload:
            artifact_payload = extract_jsonish_from_a2a_message(getattr(artifact, "content", None))
        if artifact_payload:
            artifact_payloads.append(artifact_payload)
    return "\n".join(item.strip() for item in artifact_payloads if item).strip()


def extract_text_from_a2a_result(result: Any) -> str:
    if result is None:
        return ""

    message = getattr(result, "message", None)
    message_text = extract_jsonish_from_a2a_message(message)
    if message_text:
        return message_text

    status = getattr(result, "status", None)
    status_message_text = extract_jsonish_from_a2a_message(getattr(status, "message", None))
    if status_message_text:
        return status_message_text

    artifact_text = extract_jsonish_from_a2a_artifacts(getattr(result, "artifacts", None) or [])
    if artifact_text:
        return artifact_text

    history = getattr(result, "history", None) or []
    history_texts = [extract_jsonish_from_a2a_message(entry) for entry in history]
    history_text = "\n".join(text.strip() for text in history_texts if text).strip()
    if history_text:
        return history_text

    return ""


def summarize_a2a_result_shape(result: Any) -> dict:
    def part_summary(part: Any) -> dict:
        root = getattr(part, "root", None)
        dumped = None
        if hasattr(part, "model_dump"):
            try:
                dumped = part.model_dump()
            except Exception:
                dumped = None
        return {
            "kind": type(part).__name__,
            "has_text": bool(getattr(part, "text", None)),
            "has_data": getattr(part, "data", None) is not None,
            "root_kind": type(root).__name__ if root is not None else None,
            "root_text": bool(getattr(root, "text", None)) if root is not None else False,
            "root_data": getattr(root, "data", None) is not None if root is not None else False,
            "dump": dumped,
        }

    def message_summary(message: Any) -> dict | None:
        if message is None:
            return None
        parts = getattr(message, "parts", None) or []
        content = getattr(message, "content", None)
        content_parts = getattr(content, "parts", None) or []
        return {
            "kind": type(message).__name__,
            "parts": [part_summary(part) for part in parts[:5]],
            "content_parts": [part_summary(part) for part in content_parts[:5]],
        }

    artifacts = getattr(result, "artifacts", None) or []
    history = getattr(result, "history", None) or []
    status = getattr(result, "status", None)

    return {
        "result_type": type(result).__name__,
        "message": message_summary(getattr(result, "message", None)),
        "status_message": message_summary(getattr(status, "message", None)),
        "artifact_count": len(artifacts),
        "artifacts": [
            {
                "kind": type(artifact).__name__,
                "parts": [part_summary(part) for part in (getattr(artifact, "parts", None) or [])[:5]],
                "content": message_summary(getattr(artifact, "content", None)),
            }
            for artifact in artifacts[:3]
        ],
        "history_count": len(history),
        "history": [message_summary(entry) for entry in history[:3]],
    }

def load_local_db() -> dict:
    if not os.path.exists(LOCAL_DB_PATH):
        return {}

    with open(LOCAL_DB_PATH, "r") as db_file:
        return json.load(db_file)

def save_local_db(db_data: dict) -> None:
    with open(LOCAL_DB_PATH, "w") as db_file:
        json.dump(db_data, db_file)

def now_iso() -> str:
    return "2026-03-17T00:00:00Z"

def create_local_document(collection_name: str, document: dict) -> dict:
    db_data = load_local_db()
    collection = db_data.setdefault(collection_name, {})
    collection[document["id"]] = document
    save_local_db(db_data)
    return document

def list_collection_documents(collection_name: str) -> List[dict]:
    return list(load_local_db().get(collection_name, {}).values())

def update_local_document(collection_name: str, document_id: str, updates: dict) -> dict | None:
    db_data = load_local_db()
    collection = db_data.setdefault(collection_name, {})
    document = collection.get(document_id)
    if not document:
        return None

    document.update(updates)
    collection[document_id] = document
    save_local_db(db_data)
    return document

def find_world_by_share_code(share_code: str) -> Optional[dict]:
    normalized_code = share_code.strip().upper()

    for world in list_collection_documents("worlds"):
        if world.get("share_code", "").upper() == normalized_code:
            return world

    return None

def get_character_name(character_id: str) -> str:
    db_data = load_local_db()
    character = db_data.get("characters", {}).get(character_id)
    return character.get("name", "Unknown Character") if character else "Unknown Character"

def get_world_from_local_db(world_id: str) -> Optional[dict]:
    return load_local_db().get("worlds", {}).get(world_id)

def get_character_from_local_db(char_id: str) -> Optional[dict]:
    return load_local_db().get("characters", {}).get(char_id)

def generate_share_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

def build_world_intro(world_data: dict) -> str:
    description = (world_data.get("description") or "").strip()
    world_name = world_data["name"]
    era = world_data["era"]
    environment = world_data["environment"]
    tone = world_data["tone"]

    opening = (
        f"{world_name} is a {tone.lower()} world set in a {era.lower()} age, centered on {environment.lower()}. "
        f"Every street, rumor, and frontier reflects that mood from the first step into the setting."
    )
    detail = (
        f"The world is built to support immediate play: clear atmosphere, a strong sense of place, "
        f"and enough tension to give new characters something meaningful to do right away."
    )
    if description:
        detail = f"{description} {detail}"

    return f"{opening}\n\n{detail}"

def build_character_fit_reasoning(world: dict, character: dict) -> str:
    return (
        f"{character['name']} fits {world['name']} because the {character['archetype'].lower()} concept, "
        f"backstory, and visual description can operate naturally within a {world['tone'].lower()} "
        f"{world['era'].lower()} setting centered on {world['environment'].lower()}."
    )


def get_gemini_client() -> genai.Client:
    global _GEMINI_CLIENT
    if _GEMINI_CLIENT is not None:
        return _GEMINI_CLIENT

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        _GEMINI_CLIENT = genai.Client(api_key=api_key)
        return _GEMINI_CLIENT

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    if project:
        _GEMINI_CLIENT = genai.Client(vertexai=True, project=project, location=location)
        return _GEMINI_CLIENT

    raise RuntimeError("No Gemini credentials configured. Set GOOGLE_API_KEY, GEMINI_API_KEY, or GOOGLE_CLOUD_PROJECT.")


def clean_model_json(text: str) -> str:
    payload = (text or "").strip()
    if payload.startswith("```json"):
        return payload.split("```json", 1)[1].split("```", 1)[0].strip()
    if payload.startswith("```"):
        return payload.split("```", 1)[1].split("```", 1)[0].strip()
    return payload


def extract_model_text(response: object) -> str:
    text = getattr(response, "text", None)
    if text:
        return text

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        parts = getattr(getattr(candidate, "content", None), "parts", None) or []
        collected = []
        for part in parts:
            part_text = getattr(part, "text", None)
            if part_text:
                collected.append(part_text)
        if collected:
            return "\n".join(collected).strip()
    return ""


def recent_history_text(history: List[dict], limit: int = 4) -> str:
    recent = history[-limit:]
    if not recent:
        return "No prior scenes yet."
    return "\n".join(
        f"- Scene {entry.get('scene_number', '?')}: choice={entry.get('choice', 'unknown')} | outcome={entry.get('narrative', '').replace(chr(10), ' ')[:260]}"
        for entry in recent
    )


def build_scene_prompt(world: dict, character: dict, history: List[dict], selected_choice: dict | None, scene_number: int) -> str:
    last_choice = (selected_choice or {}).get("text", "The adventure begins at the dungeon threshold.")
    return f"""
You are the dungeon master for a fantasy campaign. Write the next story scene as if you are running a strong Dungeons & Dragons session.

WORLD
- Name: {world['name']}
- Era: {world['era']}
- Environment: {world['environment']}
- Tone: {world['tone']}
- Description: {world.get('description', 'N/A')}

CHARACTER
- Name: {character['name']}
- Archetype: {character['archetype']}
- Backstory: {character.get('backstory', 'Unknown')}
- Visual description: {character.get('visual_description', 'Unknown')}

SESSION CONTEXT
- Scene number: {scene_number}
- Most recent player choice: {last_choice}
- Recent history:
{recent_history_text(history)}

TASK
1. Write 3-5 paragraphs of coherent narrative.
2. Sound like a game master describing a dangerous dungeon, ruin, lair, or fantasy location with sensory detail.
3. Make the new scene a direct consequence of the most recent player choice.
4. Include concrete story elements that options can build on: named threats, NPCs, clues, terrain, obstacles, and stakes.
5. Present an immediate dilemma where different approaches would matter.
6. Avoid generic filler and avoid summarizing the whole campaign. Focus on the live scene.

Return pure JSON:
{{
  "narrative": "scene text only"
}}
""".strip()


def build_option_prompt(world: dict, character: dict, history: List[dict], selected_choice: dict | None, narrative: str) -> str:
    last_choice = (selected_choice or {}).get("text", "No prior choice.")
    return f"""
You are the dungeon master choosing what actions to present to the player next.

WORLD: {world['name']} | {world['era']} | {world['environment']} | {world['tone']}
CHARACTER: {character['name']} the {character['archetype']}
MOST RECENT PLAYER CHOICE: {last_choice}
RECENT HISTORY:
{recent_history_text(history)}

CURRENT SCENE:
{narrative}

TASK
1. Generate 3-4 choices tightly grounded in the current scene.
2. Every option must refer to story details that already exist in the scene.
3. Make the options meaningfully different in approach, such as force, stealth, negotiation, investigation, sacrifice, or risky improvisation.
4. Make the options matter. Each one should plausibly change the next scene.
5. Do not output vague choices like "continue", "look around", or "press onward".

Return pure JSON:
[
  {{"id": 1, "text": "choice text"}},
  {{"id": 2, "text": "choice text"}}
]
""".strip()


def build_summary_prompt(world: dict, character: dict, session: dict) -> str:
    history = session.get("history", []) or []
    current_scene = session.get("current_scene", {}) or {}
    return f"""
You are the dungeon master closing a fantasy adventure chapter.

WORLD: {world['name']}
CHARACTER: {character['name']} the {character['archetype']}

SCENE HISTORY:
{recent_history_text(history, limit=8)}

FINAL LIVE SCENE:
{current_scene.get('narrative', '')}

TASK
Write a 2 paragraph session summary that feels like the end of a tabletop chapter.
Mention what changed, what the character achieved or failed to achieve, and what future hook now remains in the world.

Return pure JSON:
{{
  "summary": "summary text"
}}
""".strip()


def generate_json_with_gemini(model: str, prompt: str, temperature: float = 1.0) -> dict | list:
    client = get_gemini_client()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
        ),
    )
    text = clean_model_json(extract_model_text(response))
    if not text:
        raise ValueError(f"Gemini model {model} returned no text")
    return json.loads(text)


async def generate_story_scene_with_gemini(
    world: dict,
    character: dict,
    history: List[dict],
    selected_choice: dict | None,
    scene_number: int,
) -> dict:
    scene_prompt = build_scene_prompt(world, character, history, selected_choice, scene_number)
    scene_payload = await asyncio.to_thread(generate_json_with_gemini, GEMINI_STORY_MODEL, scene_prompt, 0.95)
    narrative = (scene_payload.get("narrative", "") if isinstance(scene_payload, dict) else "").strip()
    if not narrative:
        raise ValueError("Gemini scene payload did not include narrative")

    option_prompt = build_option_prompt(world, character, history, selected_choice, narrative)
    option_payload = await asyncio.to_thread(generate_json_with_gemini, GEMINI_OPTION_MODEL, option_prompt, 0.8)
    if not isinstance(option_payload, list):
        raise ValueError("Gemini option payload was not a list")

    choices = []
    for index, item in enumerate(option_payload[:4], start=1):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if text:
            choices.append({"id": index, "text": text})

    if len(choices) < 3:
        raise ValueError("Gemini option payload did not produce enough valid choices")

    return {"scene_number": scene_number, "narrative": narrative, "choices": choices}


async def generate_session_summary_with_gemini(world: dict, character: dict, session: dict) -> str:
    summary_prompt = build_summary_prompt(world, character, session)
    payload = await asyncio.to_thread(generate_json_with_gemini, GEMINI_SUMMARY_MODEL, summary_prompt, 0.85)
    if not isinstance(payload, dict):
        raise ValueError("Gemini summary payload was not an object")
    summary = str(payload.get("summary", "")).strip()
    if not summary:
        raise ValueError("Gemini summary payload did not include summary text")
    return summary

def build_opening_scene(world: dict, character: dict) -> dict:
    character_name = character["name"]
    archetype = character["archetype"]
    environment = world["environment"]
    world_name = world["name"]
    tone = world["tone"]
    backstory = character.get("backstory") or "A past that still pulls at the present."
    hook = f"a sealed passage beneath {environment}"
    threat = "grave-robbers carrying lanterns hooded against the dark"
    clue = "a black-iron key etched with chapel sigils"
    contact = "a shaken acolyte hiding behind a fallen saint's statue"

    narrative = (
        f"{character_name} reaches {environment} with the weight of the past still riding close. "
        f"In {world_name}, even the air feels committed to the story's tone: {tone.lower()}, sharp with omen and opportunity. "
        f"The road ends at a broken threshold where rumors point toward {hook}, and the stone is still warm from recent trespass.\n\n"
        f"Inside, torch smoke clings to the ceiling and the floor bears the fresh scrape of boots, pry-bars, and something heavier being dragged below. "
        f"{threat.capitalize()} are already at work, whispering about a relic they were paid to unearth before dawn. "
        f"Someone else is here as well: {contact}, clutching {clue} and trying not to be seen.\n\n"
        f"This is no generic beginning. It is the kind of dungeon threshold a game master would place in front of an adventurer when every choice can bend the whole descent. "
        f"{character_name}, a {archetype.lower()} shaped by {backstory.lower()}, must decide whether to enter with steel, secrecy, or questions before the chamber below is sealed again."
    )
    choices = [
        {"id": 1, "text": f"Shadow the grave-robbers into {hook} and learn who sent them"},
        {"id": 2, "text": f"Reveal yourself to {contact} and demand the truth about the black-iron key"},
        {"id": 3, "text": f"Trust your {archetype.lower()} instincts, force the pace, and seize the descent before anyone else can"},
        {"id": 4, "text": "Study the threshold, its sigils, and the disturbed dust for traps, wards, or hidden routes"},
    ]
    return {"narrative": narrative, "choices": choices}


def build_scene_choices(world: dict, character: dict, scene_number: int, scene_state: dict) -> List[dict]:
    archetype = character["archetype"].lower()
    objective = scene_state["objective"]
    threat = scene_state["threat"]
    clue = scene_state["clue"]
    location = scene_state["location"]
    contact = scene_state["contact"]
    return [
        {"id": 1, "text": f"Confront {threat} at {location} before they can secure {objective}"},
        {"id": 2, "text": f"Slip past the danger, claim {clue}, and let the enemy realize too late what was taken"},
        {"id": 3, "text": f"Press {contact} for answers and use your {archetype} instincts to expose the real power behind {objective}"},
        {"id": 4, "text": f"Attempt a reckless dungeon gambit that could secure {objective} immediately at the cost of springing the chamber's defenses"},
    ]


def derive_scene_state(world: dict, character: dict, session: dict, selected_choice: dict | None) -> dict:
    scene_number = int((session.get("current_scene", {}) or {}).get("scene_number") or 1) + 1
    environment = world["environment"]
    history = session.get("history", []) or []
    choice_text = (selected_choice or {}).get("text", "advance into the dark")
    lowered_choice = choice_text.lower()

    if any(word in lowered_choice for word in ["shadow", "slip", "study", "trap", "ward"]):
        contact = "a masked scout cut off from their crew"
        threat = "the rear guard stalking the side passages"
        clue = "a hidden route scratched onto the back of a funerary tile"
    elif any(word in lowered_choice for word in ["truth", "demand", "answers", "question"]):
        contact = "an oath-bound caretaker whose fear is finally breaking"
        threat = "mercenaries listening from the gallery above"
        clue = "the true name of the patron bankrolling the expedition"
    elif any(word in lowered_choice for word in ["force", "seize", "pace", "confront"]):
        contact = "a wounded rival willing to bargain for their life"
        threat = "awakened sentinels answering the noise below"
        clue = "a relic chamber map torn in half during the scramble"
    else:
        contact = "a survivor who saw the first seal break"
        threat = "cult lookouts holding the choke point"
        clue = "a prayer-script that opens the inner gate"

    objectives = [
        f"the reliquary hidden under {environment}",
        "the stolen key before it changes hands",
        "the truth behind the employer funding the delve",
        "the inner sanctum before the wards collapse entirely",
    ]
    locations = [
        f"the flooded stair beneath {environment}",
        "the ossuary bridge",
        "the candlelit gallery",
        "the cracked reliquary door",
    ]

    return {
        "scene_number": scene_number,
        "objective": objectives[(scene_number - 1) % len(objectives)],
        "location": locations[(scene_number - 1) % len(locations)],
        "contact": contact,
        "threat": threat,
        "clue": clue,
        "choice_text": choice_text,
        "history_count": len(history),
        "environment": environment,
        "world_name": world["name"],
        "character_name": character["name"],
    }


def build_next_scene(world: dict, character: dict, session: dict, selected_choice: dict | None) -> dict:
    state = derive_scene_state(world, character, session, selected_choice)
    narrative = (
        f"The choice to {state['choice_text'].lower()} reshapes the descent at once. "
        f"In {state['location']}, the dungeon answers with echo, pressure, and consequence rather than waiting politely for the hero to catch up. "
        f"{state['character_name']} reaches the next threshold just in time to see {state['threat']} moving to control {state['objective']}.\n\n"
        f"The scene narrows around a hard dilemma. {state['contact'].capitalize()} is close enough to help, betray, or panic depending on how they are handled, while {state['clue']} promises a cleaner route through the danger if it can be claimed before the opposition locks the chamber down. "
        f"Nothing here is static: boots scrape on old stone, ward-light crawls over cracked icons, and every second gives the enemy more certainty.\n\n"
        f"This is where the story stops being broad setup and turns into a real tabletop beat. "
        f"{character['name']} can force the issue, outmaneuver it, or peel back the truth underneath it, but not without deciding what matters more right now: speed, secrecy, leverage, or survival."
    )

    return {
        "scene_number": state["scene_number"],
        "narrative": narrative,
        "choices": build_scene_choices(world, character, state["scene_number"], state),
    }


def build_prefetched_session_branches(world: dict, character: dict, session: dict) -> dict:
    current_scene = session.get("current_scene", {}) or {}
    choices = current_scene.get("choices", []) or []
    prefetched = {}
    for choice in choices:
        next_scene = build_next_scene(world, character, session, choice)
        prefetched[str(choice["id"])] = {
            "scene_number": next_scene["scene_number"],
            "narrative": next_scene["narrative"],
            "choices": next_scene["choices"],
            "selected_choice_id": choice["id"],
            "selected_choice_text": choice["text"],
        }
    return prefetched


def build_prefetch_metadata(prefetched_choices: dict) -> dict:
    return {
        "prefetched_choice_ids": [int(choice_id) for choice_id in prefetched_choices.keys()],
        "prefetch_status": "ready" if prefetched_choices else "pending",
    }


def schedule_session_prefetch(session_id: str) -> None:
    existing_task = PREFETCH_TASKS.get(session_id)
    if existing_task and not existing_task.done():
        return

    async def _runner() -> None:
        try:
            await asyncio.sleep(0)
            session = load_local_db().get("sessions", {}).get(session_id)
            if not session:
                return

            world = get_world_from_local_db(session.get("world_id", ""))
            character = get_character_from_local_db(session.get("character_id", ""))
            if not world or not character:
                return

            prefetched_choices = build_prefetched_session_branches(world, character, session)
            update_local_document(
                "sessions",
                session_id,
                {
                    "prefetched_choices": prefetched_choices,
                    **build_prefetch_metadata(prefetched_choices),
                    "updated_at": now_iso(),
                },
            )
        finally:
            PREFETCH_TASKS.pop(session_id, None)

    PREFETCH_TASKS[session_id] = asyncio.create_task(_runner())


def build_scene_video_key(session_id: str, scene_number: int) -> str:
    return f"{session_id}:{scene_number}"


def build_scene_video_relative_path(session_id: str, scene_number: int, narrative: str) -> str:
    video_hash = uuid.uuid5(uuid.NAMESPACE_URL, f"{session_id}:{scene_number}:{narrative}").hex[:16]
    return f"videos/sessions/{session_id}/scene_{scene_number}_{video_hash}.mp4"


def start_scene_video_generation(session_id: str, session: dict, world: dict, character: dict) -> dict:
    current_scene = session.get("current_scene", {}) or {}
    scene_number = current_scene.get("scene_number")
    narrative = current_scene.get("narrative", "")
    if not scene_number or not narrative:
        return {"status": "error", "error": "No scene narrative available for video"}

    video_key = build_scene_video_key(session_id, scene_number)
    relative_path = build_scene_video_relative_path(session_id, scene_number, narrative)
    absolute_path = GENERATED_MEDIA_DIR / relative_path
    cached_url = f"{PUBLIC_API_BASE_URL.rstrip('/')}/generated/{relative_path}"

    if absolute_path.exists():
        status = {"status": "ready", "video_url": cached_url, "scene_number": scene_number}
        VIDEO_STATUS[video_key] = status
        return status

    existing_task = VIDEO_TASKS.get(video_key)
    if existing_task and not existing_task.done():
        current_status = VIDEO_STATUS.get(video_key, {"status": "pending", "scene_number": scene_number})
        return current_status

    prompt = build_scene_video_prompt(narrative, world, character)
    VIDEO_STATUS[video_key] = {"status": "pending", "scene_number": scene_number}

    async def _runner() -> None:
        try:
            ok = await asyncio.to_thread(
                generate_scene_video,
                path=absolute_path,
                prompt=prompt,
            )
            if ok:
                VIDEO_STATUS[video_key] = {
                    "status": "ready",
                    "video_url": cached_url,
                    "scene_number": scene_number,
                }
            else:
                VIDEO_STATUS[video_key] = {
                    "status": "error",
                    "error": "Video generation is unavailable",
                    "scene_number": scene_number,
                }
        finally:
            VIDEO_TASKS.pop(video_key, None)

    VIDEO_TASKS[video_key] = asyncio.create_task(_runner())
    return VIDEO_STATUS[video_key]

def enrich_world_media(world: dict) -> dict:
    banner_url = world.get("banner_url") or ensure_world_banner(world, PUBLIC_API_BASE_URL)
    if banner_url and world.get("id"):
        updated = update_local_document("worlds", world["id"], {"banner_url": banner_url})
        return updated or {**world, "banner_url": banner_url}
    return world

def enrich_character_media(character: dict) -> dict:
    world = get_world_from_local_db(character.get("world_id", ""))
    if not world:
        return character

    portrait_urls = character.get("portrait_urls") or ensure_character_portraits(
        character,
        world,
        PUBLIC_API_BASE_URL,
    )
    updates = {}
    if portrait_urls:
        updates["portrait_urls"] = portrait_urls
        updates["portrait_url"] = portrait_urls[0]

    if updates and character.get("id"):
        updated = update_local_document("characters", character["id"], updates)
        return updated or {**character, **updates}
    return character

def enrich_session_media(session: dict) -> dict:
    world = get_world_from_local_db(session.get("world_id", ""))
    if not world:
        return session

    current_scene = session.get("current_scene", {}) or {}
    scene_number = current_scene.get("scene_number")
    narrative = current_scene.get("narrative", "")
    if not scene_number or not narrative:
        return session

    image_url = current_scene.get("image_url") or ensure_scene_image(
        session.get("id", ""),
        scene_number,
        narrative,
        world,
        PUBLIC_API_BASE_URL,
    )
    if not image_url:
        return session

    return {
        **session,
        "current_scene": {
            **current_scene,
            "image_url": image_url,
        },
    }

def build_chronicle_entry(session_data: dict, world_data: dict) -> dict:
    history_count = len(session_data.get("history", []))
    impact = "local"
    if history_count >= 4:
        impact = "global"
    elif history_count >= 2:
        impact = "regional"

    excerpt = session_data.get("summary") or session_data.get("current_scene", {}).get("narrative", "")
    created_at = session_data.get("updated_at") or session_data.get("created_at") or "Earlier"
    when_label = created_at.split("T")[0] if isinstance(created_at, str) and created_at else "Today"

    return {
        "id": session_data["id"],
        "session_id": session_data["id"],
        "session_label": f"Session {max(history_count, 1)}",
        "when_label": when_label,
        "character_name": get_character_name(session_data.get("character_id", "")),
        "location": world_data.get("environment", "Unknown Region"),
        "excerpt": excerpt,
        "impact": impact,
        "footer": f"{max(history_count, 1)} story beat{'s' if history_count != 1 else ''} recorded",
    }

async def send_a2a_message(agent_url: str, prompt: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=60.0) as httpx_client:
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=agent_url)
            agent_card = await resolver.get_agent_card()
            client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

            payload = {
                "message": {
                    "role": "user",
                    "parts": [{"kind": "text", "text": prompt}],
                    "messageId": uuid.uuid4().hex,
                },
            }
            request = SendMessageRequest(id=str(uuid.uuid4()), params=MessageSendParams(**payload))
            response = await client.send_message(request)
            
            if hasattr(response, 'root') and hasattr(response.root, 'result'):
                 text = extract_text_from_a2a_result(response.root.result)
                 if not text:
                     result_shape = summarize_a2a_result_shape(response.root.result)
                     print(f"A2A result had no text payload: {json.dumps(result_shape)}")
                     return {
                         "error": f"Agent returned no text payload ({type(response.root.result).__name__})",
                         "result_shape": result_shape,
                     }
                 # Agents are instructed to return pure JSON
                 if text.startswith("```json"):
                     text = text.split("```json")[1].split("```")[0].strip()
                 elif text.startswith("```"):
                     text = text.split("```")[1].split("```")[0].strip()
                 
                 try:
                     return json.loads(text)
                 except json.JSONDecodeError:
                     return {"error": "Failed to parse agent JSON", "raw_text": text}
            return {"error": "Invalid response format from agent"}
    except Exception as e:
        print(f"Error calling A2A agent at {agent_url}: {e}")
        return {"error": str(e)}

# Pydantic Models
class WorldCreate(BaseModel):
    name: str
    era: str
    environment: str
    tone: str
    description: Optional[str] = None

class CharacterCreate(BaseModel):
    world_id: str
    name: str
    age: int
    archetype: str
    backstory: str
    visual_description: str
    portrait_url: Optional[str] = None
    portrait_urls: Optional[List[str]] = None

class SessionCreate(BaseModel):
    character_id: str
    world_id: str

class ChoiceSubmission(BaseModel):
    choice_id: int


class WorldPreviewRequest(BaseModel):
    setting_id: Optional[str] = None
    name: str
    era: str
    environment: str
    tone: str
    description: Optional[str] = None


class CharacterPreviewRequest(BaseModel):
    world_id: str
    name: str
    archetype: str
    backstory: str
    visual_description: str

@app.get("/")
async def root():
    return {"message": "Frontend Web API Gateway"}


@app.get("/api/previews/world-settings")
async def get_world_setting_previews():
    preset_ids = ["medieval-fantasy", "post-apocalyptic", "modern-mystery"]
    return {
        "presets": [
            {
                "setting_id": setting_id,
                "image_url": ensure_world_setting_preset(setting_id, PUBLIC_API_BASE_URL),
            }
            for setting_id in preset_ids
        ]
    }


@app.post("/api/previews/world")
async def preview_world(preview_data: WorldPreviewRequest):
    image_url = generate_world_preview(preview_data.model_dump(), PUBLIC_API_BASE_URL)
    if not image_url:
        return {
            "image_url": None,
            "error": "World preview generation is unavailable. Check Vertex AI authentication and try again.",
        }
    return {"image_url": image_url, "error": None}


@app.post("/api/previews/character")
async def preview_character(preview_data: CharacterPreviewRequest):
    world = get_world_from_local_db(preview_data.world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    image_urls = generate_character_preview(preview_data.model_dump(), world, PUBLIC_API_BASE_URL)
    if not image_urls:
        return {
            "image_urls": [],
            "error": "Character portrait generation is unavailable. Check Vertex AI authentication and try again.",
        }
    return {"image_urls": image_urls, "error": None}

@app.post("/api/worlds", status_code=201)
async def create_world(world_data: WorldCreate):
    world = {
        "id": str(uuid.uuid4()),
        "name": world_data.name,
        "era": world_data.era,
        "environment": world_data.environment,
        "tone": world_data.tone,
        "description": world_data.description,
        "intro": build_world_intro(world_data.model_dump()),
        "share_code": generate_share_code(),
        "created_at": now_iso(),
    }
    create_local_document("worlds", world)
    return enrich_world_media(world)

@app.get("/api/worlds/{world_id}")
async def get_world(world_id: str):
    world = get_world_from_local_db(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return enrich_world_media(world)

@app.post("/api/worlds/{share_code}/join")
async def join_world(share_code: str):
    world = find_world_by_share_code(share_code)
    if not world:
        raise HTTPException(status_code=404, detail="World not found for that share code")
    world = enrich_world_media(world)

    recent_sessions = [
        session
        for session in list_collection_documents("sessions")
        if session.get("world_id") == world["id"] and session.get("status") == "completed"
    ]
    recent_sessions.sort(
        key=lambda session: session.get("updated_at") or session.get("created_at") or "",
        reverse=True,
    )

    return {
        "world": world,
        "recent_events": [build_chronicle_entry(session, world) for session in recent_sessions[:3]],
    }

@app.get("/api/worlds/{world_id}/chronicle")
async def get_world_chronicle(world_id: str):
    db_data = load_local_db()
    world = db_data.get("worlds", {}).get(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    world = enrich_world_media(world)

    sessions = [
        session
        for session in list_collection_documents("sessions")
        if session.get("world_id") == world_id and session.get("status") == "completed"
    ]
    sessions.sort(
        key=lambda session: session.get("updated_at") or session.get("created_at") or "",
        reverse=True,
    )

    return {
        "world": world,
        "entries": [build_chronicle_entry(session, world) for session in sessions],
    }

@app.post("/api/characters", status_code=201)
async def create_character(char_data: CharacterCreate):
    world = get_world_from_local_db(char_data.world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    res = {
        "id": str(uuid.uuid4()),
        "world_id": char_data.world_id,
        "name": char_data.name,
        "age": char_data.age,
        "archetype": char_data.archetype,
        "backstory": char_data.backstory,
        "visual_description": char_data.visual_description,
        "portrait_url": char_data.portrait_url,
        "portrait_urls": char_data.portrait_urls,
        "fit_reasoning": build_character_fit_reasoning(world, char_data.model_dump()),
        "created_at": now_iso(),
    }
    create_local_document("characters", res)

    preview_updates = {}
    if char_data.portrait_urls:
        preview_updates["portrait_urls"] = char_data.portrait_urls
    if char_data.portrait_url:
        preview_updates["portrait_url"] = char_data.portrait_url

    if preview_updates:
        if res.get("id"):
            updated = update_local_document("characters", res["id"], preview_updates)
            res = updated or {**res, **preview_updates}
        else:
            res = {**res, **preview_updates}

    return enrich_character_media(res)

@app.get("/api/characters/{char_id}")
async def get_character(char_id: str):
    character = get_character_from_local_db(char_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return enrich_character_media(character)

@app.post("/api/sessions", status_code=201)
async def create_session(session_data: SessionCreate):
    world = get_world_from_local_db(session_data.world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    character = get_character_from_local_db(session_data.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    try:
        opening_scene = await generate_story_scene_with_gemini(
            world,
            character,
            [],
            None,
            1,
        )
    except Exception as exc:
        print(f"Gemini scene generation failed for create_session: {exc}")
        opening_scene = build_opening_scene(world, character)
    session = {
        "id": str(uuid.uuid4()),
        "character_id": session_data.character_id,
        "world_id": session_data.world_id,
        "status": "in_progress",
        "current_scene": {
            "scene_number": 1,
            "narrative": opening_scene["narrative"],
            "choices": opening_scene["choices"],
        },
        "history": [],
        "prefetched_choices": {},
        "prefetched_choice_ids": [],
        "prefetch_status": "ready",
        "created_at": now_iso(),
    }
    create_local_document("sessions", session)
    return enrich_session_media(session)

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session = load_local_db().get("sessions", {}).get(session_id)
    if session:
        return enrich_session_media(session)

    prompt = f"Use the get_session tool to fetch session_id: {session_id}"
    res = await send_a2a_message(AGENT_NARRATIVE_URL, prompt)
    if "error" in res:
        raise HTTPException(status_code=404, detail="Session not found")
    return enrich_session_media(res)

@app.post("/api/sessions/{session_id}/choices")
async def submit_choice(session_id: str, submission: ChoiceSubmission):
    session = load_local_db().get("sessions", {}).get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    world = get_world_from_local_db(session.get("world_id", ""))
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    character = get_character_from_local_db(session.get("character_id", ""))
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    current_scene = session.get("current_scene", {}) or {}
    current_choices = current_scene.get("choices", []) or []
    selected_choice = next((choice for choice in current_choices if choice.get("id") == submission.choice_id), None)
    try:
        next_scene = await generate_story_scene_with_gemini(
            world,
            character,
            session.get("history", []) + [{
                "scene_number": current_scene.get("scene_number", 1),
                "narrative": current_scene.get("narrative", ""),
                "choice": (selected_choice or {}).get("text", "made a choice"),
            }],
            selected_choice,
            int(current_scene.get("scene_number", 1)) + 1,
        )
    except Exception as exc:
        print(f"Gemini scene generation failed for submit_choice: {exc}")
        next_scene = build_next_scene(world, character, session, selected_choice)
    history_entry = {
        "scene_number": current_scene.get("scene_number", 1),
        "narrative": current_scene.get("narrative", ""),
        "choice": (selected_choice or {}).get("text", "made a choice"),
    }
    updated_session = {
        **session,
        "current_scene": {
            "scene_number": next_scene["scene_number"],
            "narrative": next_scene["narrative"],
            "choices": next_scene["choices"],
        },
        "history": session.get("history", []) + [history_entry],
        "prefetched_choices": {},
        "prefetched_choice_ids": [],
        "prefetch_status": "ready",
        "updated_at": now_iso(),
    }
    updated = update_local_document("sessions", session_id, updated_session)
    return enrich_session_media(updated or updated_session)

@app.post("/api/sessions/{session_id}/conclude")
async def conclude_session(session_id: str):
    session = load_local_db().get("sessions", {}).get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    world = get_world_from_local_db(session.get("world_id", ""))
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    character = get_character_from_local_db(session.get("character_id", ""))
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    try:
        summary = await generate_session_summary_with_gemini(world, character, session)
    except Exception as exc:
        print(f"Gemini summary generation failed for conclude_session: {exc}")
        current_scene = (session.get("current_scene", {}) or {}).get("narrative", "")
        summary = (
            f"{character['name']} closes this chapter in {world['name']} after pushing through the dangers of {world['environment']}. "
            f"The latest scene leaves a clear mark on the world and points toward deeper trouble ahead.\n\n{current_scene}"
        ).strip()

    updated_session = {
        **session,
        "status": "completed",
        "summary": summary,
        "updated_at": now_iso(),
    }
    updated = update_local_document("sessions", session_id, updated_session)
    return enrich_session_media(updated or updated_session)


@app.post("/api/sessions/{session_id}/narration")
async def create_session_narration(session_id: str):
    session = load_local_db().get("sessions", {}).get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    current_scene = session.get("current_scene", {}) or {}
    scene_number = current_scene.get("scene_number")
    narrative = current_scene.get("narrative", "")
    if not scene_number or not narrative:
        raise HTTPException(status_code=400, detail="No scene narrative available for narration")

    audio_url = ensure_scene_audio(
        session_id,
        scene_number,
        narrative,
        PUBLIC_API_BASE_URL,
    )
    if not audio_url:
        raise HTTPException(status_code=503, detail="Narration generation is unavailable")

    return {
        "audio_url": audio_url,
        "scene_number": scene_number,
    }


@app.post("/api/sessions/{session_id}/video")
async def create_session_video(session_id: str):
    session = load_local_db().get("sessions", {}).get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    world = get_world_from_local_db(session.get("world_id", ""))
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    character = get_character_from_local_db(session.get("character_id", ""))
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    status = start_scene_video_generation(session_id, session, world, character)
    if status.get("status") == "error":
        raise HTTPException(status_code=503, detail=status.get("error", "Video generation failed"))
    return status


@app.get("/api/sessions/{session_id}/video")
async def get_session_video(session_id: str, scene_number: int):
    video_key = build_scene_video_key(session_id, scene_number)
    status = VIDEO_STATUS.get(video_key)
    if status:
        return status

    session = load_local_db().get("sessions", {}).get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    current_scene = session.get("current_scene", {}) or {}
    narrative = current_scene.get("narrative", "")
    relative_path = build_scene_video_relative_path(session_id, scene_number, narrative)
    absolute_path = GENERATED_MEDIA_DIR / relative_path
    if absolute_path.exists():
        return {
            "status": "ready",
            "scene_number": scene_number,
            "video_url": f"{PUBLIC_API_BASE_URL.rstrip('/')}/generated/{relative_path}",
        }

    return {"status": "idle", "scene_number": scene_number}
