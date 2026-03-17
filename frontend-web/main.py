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
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import SendMessageRequest, MessageSendParams
from media_service import (
    GENERATED_MEDIA_DIR,
    ensure_character_portraits,
    ensure_media_dirs,
    ensure_scene_image,
    ensure_world_banner,
    ensure_world_setting_preset,
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

def build_opening_scene(world: dict, character: dict) -> dict:
    character_name = character["name"]
    archetype = character["archetype"]
    environment = world["environment"]
    world_name = world["name"]
    tone = world["tone"]
    backstory = character.get("backstory") or "A past that still pulls at the present."

    narrative = (
        f"{character_name}, a {archetype.lower()} shaped by {backstory.lower()}, arrives in {environment} at the edge of {world_name}. "
        f"The atmosphere is unmistakably {tone.lower()}, and the first signs of trouble are already visible in the people, the streets, and the rumors moving faster than the wind.\n\n"
        f"Nothing about this moment feels accidental. Something is shifting in {environment}, and {character_name} is close enough to intervene, exploit it, or be pulled under by it."
    )
    choices = [
        {"id": 1, "text": f"Survey {environment} carefully before acting"},
        {"id": 2, "text": "Approach the nearest suspicious figure and ask questions"},
        {"id": 3, "text": f"Lean on your {archetype.lower()} instincts and pursue the strongest lead"},
    ]
    return {"narrative": narrative, "choices": choices}


def build_scene_choices(world: dict, character: dict, scene_number: int) -> List[dict]:
    archetype = character["archetype"]
    environment = world["environment"]
    return [
        {"id": 1, "text": f"Investigate the shifting mood in {environment}"},
        {"id": 2, "text": f"Push forward using your {archetype.lower()} instincts"},
        {"id": 3, "text": "Take a risk that could change the balance of the scene"},
    ]


def build_next_scene(world: dict, character: dict, session: dict, selected_choice: dict | None) -> dict:
    current_scene = session.get("current_scene", {}) or {}
    current_scene_number = int(current_scene.get("scene_number") or 1)
    next_scene_number = current_scene_number + 1
    choice_text = (selected_choice or {}).get("text", "Press forward into the unknown")

    narrative = (
        f"Scene {next_scene_number} opens with the consequences of a clear decision: {choice_text}. "
        f"In {world['environment']}, the pressure around {character['name']} changes immediately, and the tone of {world['name']} turns the moment into a test of intent rather than chance.\n\n"
        f"{character['name']} feels the world answer back. Allies, threats, and hidden openings begin to shift around this choice, creating a new angle on the same conflict and a sharper path into the story."
    )

    return {
        "scene_number": next_scene_number,
        "narrative": narrative,
        "choices": build_scene_choices(world, character, next_scene_number),
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
        "created_at": now_iso(),
    }
    session["prefetched_choices"] = build_prefetched_session_branches(world, character, session)
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
    prefetched_choices = session.get("prefetched_choices", {}) or {}
    prefetched = prefetched_choices.get(str(submission.choice_id))

    next_scene = prefetched or build_next_scene(world, character, session, selected_choice)
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
        "updated_at": now_iso(),
    }
    updated_session["prefetched_choices"] = build_prefetched_session_branches(world, character, updated_session)
    updated = update_local_document("sessions", session_id, updated_session)
    return enrich_session_media(updated or updated_session)

@app.post("/api/sessions/{session_id}/conclude")
async def conclude_session(session_id: str):
    prompt = f"Use conclude_session tool for session_id {session_id}. Write a 1-2 paragraph summary."
    res = await send_a2a_message(AGENT_NARRATIVE_URL, prompt)
    return enrich_session_media(res)
