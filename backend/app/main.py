from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid
import secrets
import string
from .database import db, firestore
from .ai import generate_world_intro, validate_character_fit, generate_character_portrait

app = FastAPI()

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

# Helper Functions
def generate_share_code(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

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

@app.get("/api/worlds/{world_id}")
async def get_world(world_id: str):
    doc = db.collection("worlds").document(world_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="World not found")
    data = doc.to_dict()
    if "created_at" in data and not isinstance(data["created_at"], str):
        data["created_at"] = data["created_at"].isoformat() if hasattr(data["created_at"], "isoformat") else str(data["created_at"])
    return data

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
    # Validate character and world
    char_doc = db.collection("characters").document(session_data.character_id).get()
    if not char_doc.exists:
        raise HTTPException(status_code=404, detail="Character not found")
    
    world_doc = db.collection("worlds").document(session_data.world_id).get()
    if not world_doc.exists:
        raise HTTPException(status_code=404, detail="World not found")

    session_id = str(uuid.uuid4())
    
    # Placeholder for the first scene until the AI Scene Generation Service is implemented
    first_scene = {
        "scene_number": 1,
        "narrative": "The adventure begins...",
        "choices": [
            {"id": 1, "text": "Explore the surroundings"},
            {"id": 2, "text": "Wait and see what happens"}
        ]
    }
    
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
    
    # Response
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
