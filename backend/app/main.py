from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import secrets
import string
from .database import db, firestore
from .ai import generate_world_intro

app = FastAPI()

class WorldCreate(BaseModel):
    name: str
    era: str
    environment: str
    tone: str
    description: Optional[str] = None

def generate_share_code(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

@app.get("/")
async def root():
    return {"message": "Shared AI Storytelling RPG API"}

@app.post("/api/worlds", status_code=201)
async def create_world(world_data: WorldCreate):
    world_id = str(uuid.uuid4())
    share_code = generate_share_code()
    
    # Generate the world introduction narrative
    intro = await generate_world_intro(world_data.model_dump())
    
    world_dict = world_data.model_dump()
    world_dict.update({
        "id": world_id,
        "share_code": share_code,
        "intro": intro,
        "created_at": firestore.SERVER_TIMESTAMP
    })
    
    db.collection("worlds").document(world_id).set(world_dict)
    
    # For the response, we return a serializable version
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
    # Handle non-serializable objects
    if "created_at" in data and not isinstance(data["created_at"], str):
        data["created_at"] = data["created_at"].isoformat() if hasattr(data["created_at"], "isoformat") else str(data["created_at"])
    
    return data
