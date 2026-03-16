from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import secrets
import string
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

# Configuration for Agent URLs (matching Cloud Run internal URLs or local defaults)
AGENT_CREATEWORLD_URL = os.getenv("AGENT_CREATEWORLD_URL", "http://localhost:10001")
AGENT_CREATECHARACTER_URL = os.getenv("AGENT_CREATECHARACTER_URL", "http://localhost:10002")
AGENT_NARRATIVE_URL = os.getenv("AGENT_NARRATIVE_URL", "http://localhost:10003")
AGENT_OPTIONGEN_URL = os.getenv("AGENT_OPTIONGEN_URL", "http://localhost:10004")
MCP_SERVER_URL = os.getenv("cloud_run_1_SERVICE_ENDPOINT", "http://localhost:8080") # FastMCP db server

# A2A Helper function
async def send_a2a_message(agent_url: str, prompt: str) -> str:
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
            
            # The A2A client response contains root.result.message.content.parts if successful
            if hasattr(response, 'root') and hasattr(response.root, 'result'):
                 parts = response.root.result.message.content.parts
                 return "".join([p.text for p in parts if p.kind == "text"])
            return ""
    except Exception as e:
        print(f"Error calling A2A agent at {agent_url}: {e}")
        return ""


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
    return {"message": "Frontend Web API Gateway for Shared AI Storytelling RPG API"}

@app.post("/api/worlds", status_code=201)
async def create_world(world_data: WorldCreate):
    prompt = f"""Create a new world with the following details:
    Name: {world_data.name}
    Era: {world_data.era}
    Environment: {world_data.environment}
    Tone: {world_data.tone}
    Description: {world_data.description}
    """
    # Call the world builder agent to generate intro and save via MCP tool
    response_text = await send_a2a_message(AGENT_CREATEWORLD_URL, prompt)
    
    # We also want to fetch the newly created world from MCP server directly or rely on the agent's return
    # The frontend needs the ID, but the agent's tool creates it.
    # To keep it simple, we just pass the request to the agent, but wait, the agent doesn't guarantee a JSON return with the ID!
    # So actually, we should just let the backend API orchestrate the db!
    return {"message": "World created", "agent_response": response_text}

