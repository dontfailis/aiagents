from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
import os

# --- Google ADK Imports ---
try:
    from adk.agent import Agent
    from adk.models import GeminiModel
except ImportError:
    # Fallback/stub if adk is not fully installed locally during dev
    Agent = object
    GeminiModel = object

app = FastAPI(title="AI RPG API / Orchestration Layer")

# --- ADK Agent Definitions ---
# Initialize the Gemini model to be used by our ADK Agents
gemini_model = GeminiModel(model_name="gemini-3.0-pro")

def load_md_instructions(filename: str) -> str:
    """Helper to load agent instructions directly from markdown files."""
    filepath = os.path.join(os.path.dirname(__file__), "..", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: Could not find instruction file {filename}"

world_builder_agent = Agent(
    name="WorldBuilder",
    model=gemini_model,
    instructions=load_md_instructions("Agent_WorldBuilder.md"),
)

character_agent = Agent(
    name="CharacterValidator",
    model=gemini_model,
    instructions=load_md_instructions("Agent_Character.md"),
)

session_narrator_agent = Agent(
    name="SessionNarrator",
    model=gemini_model,
    instructions=load_md_instructions("Agent_SessionNarrator.md"),
)

state_keeper_agent = Agent(
    name="StateKeeper",
    model=gemini_model,
    instructions=load_md_instructions("Agent_StateKeeper.md"),
)

recap_agent = Agent(
    name="RecapAgent",
    model=gemini_model,
    instructions=load_md_instructions("Agent_Recap.md")
)

# --- Models ---
class WorldCreateRequest(BaseModel):
    name: str
    era: str
    environment: str
    tone: List[str]
    description: Optional[str] = ""

class CharacterCreateRequest(BaseModel):
    world_id: str
    name: str
    age: int
    archetype: str
    backstory: str
    visual_description: str

class ChoiceRequest(BaseModel):
    choice_id: str

# --- Endpoints ---

@app.post("/api/worlds", summary="Create a new world")
async def create_world(request: WorldCreateRequest):
    """Triggers the World Builder Agent."""
    world_id = str(uuid.uuid4())
    share_code = world_id[:8].upper()
    
    # ADK Execution Example
    # response = world_builder_agent.run(f"Create a {request.tone} world in a {request.era} {request.environment} setting.")
    
    return {"world_id": world_id, "share_code": share_code, "status": "initializing", "message": "World Builder ADK Agent started."}

@app.post("/api/worlds/{code}/join", summary="Join a world via share code")
async def join_world(code: str):
    """Validates the share code and allows a player to join."""
    return {"status": "joined", "world_summary": "Welcome to the world..."}

@app.get("/api/worlds/{world_id}", summary="Fetch world state and summary")
async def get_world(world_id: str):
    """Retrieves current world state from Firestore."""
    return {"world_id": world_id, "state": "active", "regions": []}

@app.get("/api/worlds/{world_id}/events", summary="Fetch world event history")
async def get_world_events(world_id: str):
    """Retrieves world chronicle/history from Firestore/BigQuery."""
    return {"events": []}

@app.get("/api/worlds/{world_id}/updates", summary="Fetch 'while you were away' summary")
async def get_world_updates(world_id: str):
    """Triggers Recap Agent if needed or fetches pre-computed recap."""
    # ADK Execution Example
    # response = recap_agent.run("Generate recap based on recent world events...")
    return {"recap": "A lot has happened since you last visited..."}

@app.post("/api/characters", summary="Create a new character")
async def create_character(request: CharacterCreateRequest):
    """Triggers Character Agent for validation."""
    character_id = str(uuid.uuid4())
    # ADK validation
    # response = character_agent.run(f"Validate character: {request.name}, {request.archetype}")
    return {"character_id": character_id, "status": "approved"}

@app.post("/api/characters/{character_id}/portraits", summary="Generate portrait options")
async def generate_portraits(character_id: str):
    """Triggers Character Agent to generate Image Prompts."""
    # response = character_agent.run(f"Generate portrait prompts for character {character_id}")
    return {"portraits": ["url1", "url2", "url3"]}

@app.post("/api/sessions", summary="Start a new story session")
async def start_session(character_id: str):
    """Triggers Session Narrator agent to begin a new scene."""
    session_id = str(uuid.uuid4())
    # response = session_narrator_agent.run("Start a new session for the character...")
    return {"session_id": session_id, "scene": "You arrive at the tavern...", "choices": ["Fight", "Run"]}

@app.post("/api/sessions/{session_id}/choices", summary="Submit a player choice")
async def submit_choice(session_id: str, request: ChoiceRequest):
    """Sends choice to Session Narrator agent for the next scene."""
    # response = session_narrator_agent.run(f"Player chose: {request.choice_id}. Generate next scene.")
    return {"scene": "The enemy attacks!", "choices": ["Dodge", "Block"]}

@app.post("/api/sessions/{session_id}/complete", summary="Complete session & trigger world update")
async def complete_session(session_id: str):
    """Triggers State Keeper Agent to update World State via Async Pub/Sub task."""
    # This would typically be sent to Pub/Sub, then State Keeper runs asynchronously
    # state_keeper_agent.run("Extract JSON updates from the completed session.")
    return {"status": "completed", "summary": "You survived the encounter."}

@app.get("/health", summary="Health check")
async def health_check():
    return {"status": "ok"}

