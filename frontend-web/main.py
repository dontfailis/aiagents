from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import httpx
import os
import json
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import SendMessageRequest, MessageSendParams
from media_service import GENERATED_MEDIA_DIR, ensure_character_portraits, ensure_media_dirs, ensure_scene_image, ensure_world_banner

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

def extract_text_from_a2a_result(result: Any) -> str:
    if result is None:
        return ""

    message = getattr(result, "message", None)
    if message and getattr(message, "content", None):
        parts = getattr(message.content, "parts", []) or []
        return "".join([part.text for part in parts if getattr(part, "kind", None) == "text"]).strip()

    artifacts = getattr(result, "artifacts", None) or []
    artifact_texts = []
    for artifact in artifacts:
        parts = getattr(getattr(artifact, "content", None), "parts", []) or []
        artifact_texts.extend([part.text for part in parts if getattr(part, "kind", None) == "text"])

    return "\n".join(text.strip() for text in artifact_texts if text).strip()

def load_local_db() -> dict:
    if not os.path.exists(LOCAL_DB_PATH):
        return {}

    with open(LOCAL_DB_PATH, "r") as db_file:
        return json.load(db_file)

def save_local_db(db_data: dict) -> None:
    with open(LOCAL_DB_PATH, "w") as db_file:
        json.dump(db_data, db_file)

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
                     return {"error": f"Agent returned no text payload ({type(response.root.result).__name__})"}
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

class SessionCreate(BaseModel):
    character_id: str
    world_id: str

class ChoiceSubmission(BaseModel):
    choice_id: int

@app.get("/")
async def root():
    return {"message": "Frontend Web API Gateway"}

@app.post("/api/worlds", status_code=201)
async def create_world(world_data: WorldCreate):
    prompt = f"""Create a new world with the following details:
    Name: {world_data.name}
    Era: {world_data.era}
    Environment: {world_data.environment}
    Tone: {world_data.tone}
    Description: {world_data.description}
    """
    res = await send_a2a_message(AGENT_CREATEWORLD_URL, prompt)
    if "error" in res and "raw_text" not in res:
        raise HTTPException(status_code=500, detail=res["error"])
    return enrich_world_media(res)

@app.get("/api/worlds/{world_id}")
async def get_world(world_id: str):
    prompt = f"Use the get_world tool to fetch world_id: {world_id}"
    res = await send_a2a_message(AGENT_CREATEWORLD_URL, prompt)
    if "error" in res:
        raise HTTPException(status_code=404, detail="World not found")
    return enrich_world_media(res)

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
    prompt = f"""Validate and create a character for world_id: {char_data.world_id}.
    Name: {char_data.name}
    Age: {char_data.age}
    Archetype: {char_data.archetype}
    Backstory: {char_data.backstory}
    Visual: {char_data.visual_description}
    """
    res = await send_a2a_message(AGENT_CREATECHARACTER_URL, prompt)
    if "error" in res and "raw_text" not in res:
        raise HTTPException(status_code=500, detail=res["error"])
    return enrich_character_media(res)

@app.get("/api/characters/{char_id}")
async def get_character(char_id: str):
    prompt = f"Use the get_character tool to fetch char_id: {char_id}"
    res = await send_a2a_message(AGENT_CREATECHARACTER_URL, prompt)
    if "error" in res:
        raise HTTPException(status_code=404, detail="Character not found")
    return enrich_character_media(res)

@app.post("/api/sessions", status_code=201)
async def create_session(session_data: SessionCreate):
    # First get choices from option gen (empty scene implies start)
    # Actually, narrative agent can just generate the intro, and we provide empty choices to start.
    prompt = f"""Create a new session using the create_session tool. 
    character_id: {session_data.character_id}
    world_id: {session_data.world_id}
    Generate a 2-3 paragraph introductory scene narrative.
    For the choices parameter, pass an empty list [].
    Return the result of the tool as JSON.
    """
    res = await send_a2a_message(AGENT_NARRATIVE_URL, prompt)
    
    # Now generate choices based on the new narrative
    if "id" in res and "current_scene" in res:
        narrative = res["current_scene"].get("narrative", "")
        choices_prompt = f"Generate JSON choices for this scene:\n{narrative}"
        choices_res = await send_a2a_message(AGENT_OPTIONGEN_URL, choices_prompt)
        
        if isinstance(choices_res, list):
            # Update session with these choices
            update_prompt = f"""Use update_session tool on session_id: {res["id"]}.
            new_narrative: {narrative}
            new_choices: {json.dumps(choices_res)}
            scene_number: 1
            history_entry: {json.dumps({"scene_number": 1, "narrative": narrative, "choice": "started adventure"})}
            """
            final_res = await send_a2a_message(AGENT_NARRATIVE_URL, update_prompt)
            return enrich_session_media(final_res)
            
    return enrich_session_media(res)

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    prompt = f"Use the get_session tool to fetch session_id: {session_id}"
    res = await send_a2a_message(AGENT_NARRATIVE_URL, prompt)
    if "error" in res:
        raise HTTPException(status_code=404, detail="Session not found")
    return enrich_session_media(res)

@app.post("/api/sessions/{session_id}/choices")
async def submit_choice(session_id: str, submission: ChoiceSubmission):
    prompt = f"""The player chose option ID {submission.choice_id} for session_id {session_id}.
    1. Fetch the session.
    2. Generate the next narrative scene (2-3 paragraphs).
    3. Update the session using update_session tool with the new narrative and an empty choices list.
    Return the updated session JSON.
    """
    res = await send_a2a_message(AGENT_NARRATIVE_URL, prompt)
    
    if "id" in res and "current_scene" in res:
        narrative = res["current_scene"].get("narrative", "")
        scene_num = res["current_scene"].get("scene_number", 2)
        
        choices_prompt = f"Generate JSON choices for this scene:\n{narrative}"
        choices_res = await send_a2a_message(AGENT_OPTIONGEN_URL, choices_prompt)
        
        if isinstance(choices_res, list):
            update_prompt = f"""Use update_session tool on session_id: {res["id"]}.
            new_narrative: {narrative}
            new_choices: {json.dumps(choices_res)}
            scene_number: {scene_num}
            history_entry: {json.dumps({"scene_number": scene_num, "narrative": narrative, "choice": "made a choice"})}
            """
            final_res = await send_a2a_message(AGENT_NARRATIVE_URL, update_prompt)
            return enrich_session_media(final_res)
            
    return enrich_session_media(res)

@app.post("/api/sessions/{session_id}/conclude")
async def conclude_session(session_id: str):
    prompt = f"Use conclude_session tool for session_id {session_id}. Write a 1-2 paragraph summary."
    res = await send_a2a_message(AGENT_NARRATIVE_URL, prompt)
    return enrich_session_media(res)
