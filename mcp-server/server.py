import asyncio
import logging
import os
import uuid
from fastmcp import FastMCP
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from database import db, firestore

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Story RPG DB MCP Server")

@mcp.tool()
def create_world(
    name: str,
    era: str,
    environment: str,
    tone: str,
    description: str,
    intro: str
) -> dict:
    """Use this to save a new world into the database. Returns the world ID."""
    world_id = str(uuid.uuid4())
    import string
    import secrets
    alphabet = string.ascii_uppercase + string.digits
    share_code = ''.join(secrets.choice(alphabet) for _ in range(8))
    
    world_dict = {
        "id": world_id,
        "name": name,
        "era": era,
        "environment": environment,
        "tone": tone,
        "description": description,
        "intro": intro,
        "share_code": share_code,
        "created_at": firestore.SERVER_TIMESTAMP
    }
    db.collection("worlds").document(world_id).set(world_dict)
    
    # We serialize the response for MCP JSON returns
    result = dict(world_dict)
    result["created_at"] = "2026-03-16T20:55:00Z"
    return result

@mcp.tool()
def get_world(world_id: str) -> dict:
    """Use this to retrieve world details by ID."""
    doc = db.collection("worlds").document(world_id).get()
    if not doc.exists:
        return {"error": "World not found"}
    data = doc.to_dict()
    if "created_at" in data and not isinstance(data["created_at"], str):
        data["created_at"] = str(data["created_at"])
    return data

@mcp.tool()
def create_character(
    world_id: str,
    name: str,
    age: int,
    archetype: str,
    backstory: str,
    visual_description: str,
    portrait_url: str,
    fit_reasoning: str
) -> dict:
    """Use this to save a new character to the database. Returns the character ID."""
    char_id = str(uuid.uuid4())
    char_dict = {
        "id": char_id,
        "world_id": world_id,
        "name": name,
        "age": age,
        "archetype": archetype,
        "backstory": backstory,
        "visual_description": visual_description,
        "portrait_url": portrait_url,
        "fit_reasoning": fit_reasoning,
        "created_at": firestore.SERVER_TIMESTAMP
    }
    db.collection("characters").document(char_id).set(char_dict)
    result = dict(char_dict)
    result["created_at"] = "2026-03-16T21:10:00Z"
    return result

@mcp.tool()
def get_character(char_id: str) -> dict:
    """Use this to retrieve a character by ID."""
    doc = db.collection("characters").document(char_id).get()
    if not doc.exists:
        return {"error": "Character not found"}
    data = doc.to_dict()
    if "created_at" in data and not isinstance(data["created_at"], str):
        data["created_at"] = str(data["created_at"])
    return data

@mcp.tool()
def create_session(
    character_id: str,
    world_id: str,
    first_scene_narrative: str,
    first_scene_choices: List[Dict[str, Any]]
) -> dict:
    """Use this to create a new story session in the database."""
    session_id = str(uuid.uuid4())
    session_dict = {
        "id": session_id,
        "character_id": character_id,
        "world_id": world_id,
        "status": "in_progress",
        "current_scene": {
            "scene_number": 1,
            "narrative": first_scene_narrative,
            "choices": first_scene_choices
        },
        "history": [],
        "created_at": firestore.SERVER_TIMESTAMP
    }
    db.collection("sessions").document(session_id).set(session_dict)
    result = dict(session_dict)
    result["created_at"] = "2026-03-16T21:35:00Z"
    return result

@mcp.tool()
def get_session(session_id: str) -> dict:
    """Use this to retrieve a session by ID."""
    doc = db.collection("sessions").document(session_id).get()
    if not doc.exists:
        return {"error": "Session not found"}
    data = doc.to_dict()
    if "created_at" in data and not isinstance(data["created_at"], str):
        data["created_at"] = str(data["created_at"])
    if "updated_at" in data and not isinstance(data["updated_at"], str):
        data["updated_at"] = str(data["updated_at"])
    return data

@mcp.tool()
def update_session(
    session_id: str,
    new_narrative: str,
    new_choices: List[Dict[str, Any]],
    scene_number: int,
    history_entry: Dict[str, Any]
) -> dict:
    """Use this to update a session with a new scene and choices."""
    doc_ref = db.collection("sessions").document(session_id)
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": "Session not found"}
    session_data = doc.to_dict()
    
    new_history = session_data.get("history", []) + [history_entry]
    
    update_data = {
        "current_scene": {
            "scene_number": scene_number,
            "narrative": new_narrative,
            "choices": new_choices
        },
        "history": new_history,
        "updated_at": firestore.SERVER_TIMESTAMP
    }
    doc_ref.update(update_data)
    result = {**session_data, **update_data}
    result["updated_at"] = "2026-03-16T21:40:00Z"
    return result

@mcp.tool()
def conclude_session(session_id: str, summary: str) -> dict:
    """Use this to conclude a session."""
    doc_ref = db.collection("sessions").document(session_id)
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": "Session not found"}
    session_data = doc.to_dict()
    update_data = {
        "status": "completed",
        "summary": summary,
        "updated_at": firestore.SERVER_TIMESTAMP
    }
    doc_ref.update(update_data)
    result = {**session_data, **update_data}
    result["updated_at"] = "2026-03-16T21:45:00Z"
    return result

if __name__ == "__main__":
    logger.info(f"🚀 MCP server started on port {os.getenv('PORT', '8080')}")
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8080")),
        )
    )
