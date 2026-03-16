import logging
import os

from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

load_dotenv()

SYSTEM_INSTRUCTION = (
    "You are an expert game master. Your task is to generate the narrative for a storytelling RPG. "
    "You will receive a world description, character description, and optionally story history and a player's latest choice. "
    "Write 2-3 paragraphs of immersive narrative for the current scene, advancing the story based on the player's choice and the world context. "
    "Do NOT generate choices for the player; your ONLY job is to write the story text. "
    "Once generated, output ONLY the narrative text, nothing else."
)

mcp_url = os.getenv("cloud_run_1_SERVICE_ENDPOINT", os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp"))
logger.info(f"--- 🔧 Connecting to MCP Server at {mcp_url} ---")

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="agent-narrative",
    description="Generates the narrative scene for the story based on context and choices.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(url=mcp_url)
        )
    ],
)

a2a_app = to_a2a(root_agent, port=int(os.getenv("PORT", 8080)))
