from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import httpx
import os
import json
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import SendMessageRequest, MessageSendParams

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cloud Run injects these via terraform main.tf modifications
AGENT_CREATEWORLD_URL = os.getenv("AGENT_CREATEWORLD_URL", "http://localhost:10001")
AGENT_CREATECHARACTER_URL = os.getenv("AGENT_CREATECHARACTER_URL", "http://localhost:10002")
AGENT_NARRATIVE_URL = os.getenv("AGENT_NARRATIVE_URL", "http://localhost:10003")
AGENT_OPTIONGEN_URL = os.getenv("AGENT_OPTIONGEN_URL", "http://localhost:10004")

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
                 parts = response.root.result.message.content.parts
                 text = "".join([p.text for p in parts if p.kind == "text"]).strip()
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
    return res

@app.get("/api/worlds/{world_id}")
async def get_world(world_id: str):
    prompt = f"Use the get_world tool to fetch world_id: {world_id}"
    res = await send_a2a_message(AGENT_CREATEWORLD_URL, prompt)
    if "error" in res:
        raise HTTPException(status_code=404, detail="World not found")
    return res

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
    return res

@app.get("/api/characters/{char_id}")
async def get_character(char_id: str):
    prompt = f"Use the get_character tool to fetch char_id: {char_id}"
    res = await send_a2a_message(AGENT_CREATECHARACTER_URL, prompt)
    if "error" in res:
        raise HTTPException(status_code=404, detail="Character not found")
    return res

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
            return final_res
            
    return res

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    prompt = f"Use the get_session tool to fetch session_id: {session_id}"
    res = await send_a2a_message(AGENT_NARRATIVE_URL, prompt)
    if "error" in res:
        raise HTTPException(status_code=404, detail="Session not found")
    return res

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
            return final_res
            
    return res

@app.post("/api/sessions/{session_id}/conclude")
async def conclude_session(session_id: str):
    prompt = f"Use conclude_session tool for session_id {session_id}. Write a 1-2 paragraph summary."
    res = await send_a2a_message(AGENT_NARRATIVE_URL, prompt)
    return res
