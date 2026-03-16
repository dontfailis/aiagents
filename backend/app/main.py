from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
import secrets
import string
from .database import db, firestore
from .ai import generate_world_intro, validate_character_fit, generate_character_portrait, generate_next_scene, generate_session_summary, generate_world_state_update, generate_while_away_summary

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Helper Functions
def generate_share_code(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def list_collection_documents(collection_name: str):
    collection = db.collection(collection_name)

    if hasattr(collection, "_load_db"):
        db_data = collection._load_db()
        return list(db_data.get(collection_name, {}).values())

    return [doc.to_dict() for doc in collection.stream()]

def find_world_by_share_code(share_code: str):
    normalized_code = share_code.strip().upper()

    for world in list_collection_documents("worlds"):
        if world.get("share_code", "").upper() == normalized_code:
            return world

    return None

def get_character_name(character_id: str):
    char_doc = db.collection("characters").document(character_id).get()
    if not char_doc.exists:
        return "Unknown Character"
    return char_doc.to_dict().get("name", "Unknown Character")

def build_chronicle_entry(session_data: dict, world_data: dict):
    history_count = len(session_data.get("history", []))
    impact = "local"
    if history_count >= 4:
        impact = "global"
    elif history_count >= 2:
        impact = "regional"

    excerpt = session_data.get("summary")
    if not excerpt:
        excerpt = session_data.get("current_scene", {}).get("narrative", "")

    created_at = session_data.get("updated_at") or session_data.get("created_at") or "Earlier"
    when_label = "Today"
    if isinstance(created_at, str) and created_at:
        when_label = created_at.split("T")[0]

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

# Endpoints
@app.get("/")
async def root():
    return {"message": "Shared AI Storytelling RPG API"}

# Worlds API
@app.post("/api/worlds", status_code=201)
async def create_world(world_data: WorldCreate):
    world_id = str(uuid.uuid4())
    share_code = generate_share_code()
    intro = await generate_world_intro(world_data.model_dump())
    
    world_dict = world_data.model_dump()
    world_dict.update({
        "id": world_id,
        "share_code": share_code,
        "intro": intro,
        "created_at": firestore.SERVER_TIMESTAMP
    })
    
    db.collection("worlds").document(world_id).set(world_dict)
    
    response_dict = world_data.model_dump()
    response_dict.update({
        "id": world_id,
        "share_code": share_code,
        "intro": intro,
        "created_at": "2026-03-16T20:55:00Z"
    })
    return response_dict

@app.post("/api/worlds/{share_code}/join")
async def join_world(share_code: str):
    world = find_world_by_share_code(share_code)
    if not world:
        raise HTTPException(status_code=404, detail="World not found for that share code")

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
    world_doc = db.collection("worlds").document(world_id).get()
    if not world_doc.exists:
        raise HTTPException(status_code=404, detail="World not found")

    world_data = world_doc.to_dict()
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
        "world": world_data,
        "entries": [build_chronicle_entry(session, world_data) for session in sessions],
    }

@app.get("/api/worlds/{world_id}")
async def get_world(world_id: str):
    doc = db.collection("worlds").document(world_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="World not found")
    data = doc.to_dict()
    if "created_at" in data and not isinstance(data["created_at"], str):
        data["created_at"] = data["created_at"].isoformat() if hasattr(data["created_at"], "isoformat") else str(data["created_at"])
    return data

@app.get("/api/worlds/{world_id}/events")
async def get_world_events(world_id: str):
    events_ref = db.collection("world_events").where("world_id", "==", world_id).stream()
    events = [doc.to_dict() for doc in events_ref]
    return {"events": events}

@app.get("/api/worlds/{world_id}/updates")
async def get_world_updates(world_id: str, character_id: str):
    world_doc = db.collection("worlds").document(world_id).get()
    if not world_doc.exists:
        raise HTTPException(status_code=404, detail="World not found")
        
    char_doc = db.collection("characters").document(character_id).get()
    if not char_doc.exists:
        raise HTTPException(status_code=404, detail="Character not found")
        
    # In a real app, this would filter by timestamp since the character's last session
    events_ref = db.collection("world_events").where("world_id", "==", world_id).limit(10).stream()
    recent_events = [doc.to_dict() for doc in events_ref]
    
    summary = await generate_while_away_summary(
        world_doc.to_dict(),
        char_doc.to_dict(),
        recent_events
    )
    
    return {"summary": summary, "events_count": len(recent_events)}

# Characters API
@app.post("/api/characters", status_code=201)
async def create_character(char_data: CharacterCreate):
    world_doc = db.collection("worlds").document(char_data.world_id).get()
    if not world_doc.exists:
        raise HTTPException(status_code=404, detail="World not found")
    
    world_data = world_doc.to_dict()
    is_valid, reasoning = await validate_character_fit(world_data, char_data.model_dump())
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Character does not fit the world: {reasoning}")
    
    portrait_url = await generate_character_portrait(world_data, char_data.model_dump())
    char_id = str(uuid.uuid4())
    char_dict = char_data.model_dump()
    char_dict.update({
        "id": char_id,
        "created_at": firestore.SERVER_TIMESTAMP,
        "portrait_url": portrait_url,
        "fit_reasoning": reasoning
    })
    db.collection("characters").document(char_id).set(char_dict)
    
    response_dict = char_data.model_dump()
    response_dict.update({
        "id": char_id,
        "created_at": "2026-03-16T21:10:00Z",
        "portrait_url": portrait_url,
        "fit_reasoning": reasoning
    })
    return response_dict

@app.get("/api/characters/{char_id}")
async def get_character(char_id: str):
    doc = db.collection("characters").document(char_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Character not found")
    data = doc.to_dict()
    if "created_at" in data and not isinstance(data["created_at"], str):
        data["created_at"] = data["created_at"].isoformat() if hasattr(data["created_at"], "isoformat") else str(data["created_at"])
    return data

# Sessions API
@app.post("/api/sessions", status_code=201)
async def create_session(session_data: SessionCreate):
    char_doc = db.collection("characters").document(session_data.character_id).get()
    if not char_doc.exists:
        raise HTTPException(status_code=404, detail="Character not found")
    char_data = char_doc.to_dict()
    
    world_doc = db.collection("worlds").document(session_data.world_id).get()
    if not world_doc.exists:
        raise HTTPException(status_code=404, detail="World not found")
    world_data = world_doc.to_dict()

    session_id = str(uuid.uuid4())
    first_scene = await generate_next_scene(world_data, char_data)
    first_scene["scene_number"] = 1
    
    session_dict = {
        "id": session_id,
        "character_id": session_data.character_id,
        "world_id": session_data.world_id,
        "status": "in_progress",
        "current_scene": first_scene,
        "history": [],
        "created_at": firestore.SERVER_TIMESTAMP
    }
    
    db.collection("sessions").document(session_id).set(session_dict)
    return {**session_dict, "created_at": "2026-03-16T21:35:00Z"}

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    doc = db.collection("sessions").document(session_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Session not found")
    data = doc.to_dict()
    if "created_at" in data and not isinstance(data["created_at"], str):
        data["created_at"] = data["created_at"].isoformat() if hasattr(data["created_at"], "isoformat") else str(data["created_at"])
    return data

@app.post("/api/sessions/{session_id}/choices")
async def submit_choice(session_id: str, submission: ChoiceSubmission):
    doc_ref = db.collection("sessions").document(session_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = doc.to_dict()
    if session_data["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="Session is already finished")
    
    current_scene = session_data["current_scene"]
    selected_choice = next((c for c in current_scene["choices"] if c["id"] == submission.choice_id), None)
    if not selected_choice:
        raise HTTPException(status_code=400, detail="Invalid choice ID")
    
    world_doc = db.collection("worlds").document(session_data["world_id"]).get()
    char_doc = db.collection("characters").document(session_data["character_id"]).get()
    
    next_scene = await generate_next_scene(
        world_doc.to_dict(), 
        char_doc.to_dict(), 
        session_data["history"], 
        selected_choice["text"]
    )
    next_scene["scene_number"] = current_scene["scene_number"] + 1
    
    history_entry = {
        "scene_number": current_scene["scene_number"],
        "narrative": current_scene["narrative"],
        "choice": selected_choice["text"]
    }
    new_history = session_data["history"] + [history_entry]
    
    update_data = {
        "current_scene": next_scene,
        "history": new_history,
        "updated_at": firestore.SERVER_TIMESTAMP
    }
    
    doc_ref.update(update_data)
    return {**session_data, **update_data, "updated_at": "2026-03-16T21:40:00Z"}

@app.post("/api/sessions/{session_id}/conclude")
async def conclude_session(session_id: str):
    doc_ref = db.collection("sessions").document(session_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = doc.to_dict()
    if session_data["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="Session is already finished")
    
    world_id = session_data["world_id"]
    world_doc_ref = db.collection("worlds").document(world_id)
    world_doc = world_doc_ref.get()
    char_doc = db.collection("characters").document(session_data["character_id"]).get()
    
    world_data = world_doc.to_dict()
    char_data = char_doc.to_dict()
    
    summary = await generate_session_summary(
        world_data, 
        char_data, 
        session_data["history"]
    )
    
    state_update = await generate_world_state_update(
        world_data,
        char_data,
        session_data["history"]
    )
    
    # 1. Add world event
    event_id = str(uuid.uuid4())
    event_dict = {
        "id": event_id,
        "world_id": world_id,
        "source_character_id": char_data["id"],
        "location": state_update.get("location", "Unknown"),
        "summary": summary,
        "impact_scope": "global" if state_update.get("global_impact") else "regional",
        "new_hooks": state_update.get("story_hooks_unlocked", []),
        "created_at": firestore.SERVER_TIMESTAMP
    }
    db.collection("world_events").document(event_id).set(event_dict)
    
    # 2. Update world state
    new_structured_state = world_data.get("structured_state", {})
    # Simple merge for MVP
    new_structured_state.update(state_update)
    world_doc_ref.update({
        "structured_state": new_structured_state,
        "updated_at": firestore.SERVER_TIMESTAMP
    })
    
    update_data = {
        "status": "completed",
        "summary": summary,
        "updated_at": firestore.SERVER_TIMESTAMP
    }
    doc_ref.update(update_data)
    
    return {**session_data, **update_data, "updated_at": "2026-03-16T21:45:00Z", "world_update": state_update}

