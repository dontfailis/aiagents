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
    "You are a lore expert and game moderator. Your task is to receive character details and world details. "
    "1. Validate if the character fits the world described. A character should only be rejected if they fundamentally break the setting. "
    "2. Generate a reasoning string and a boolean 'is_valid' flag. "
    "3. Generate a placeholder portrait URL (e.g. using picsum.photos). "
    "4. If valid, use the 'create_character' tool to save the character to the database. "
    "If invalid, do not create them, instead return a message explaining why."
)

mcp_url = os.getenv("cloud_run_1_SERVICE_ENDPOINT", os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp"))
logger.info(f"--- 🔧 Connecting to MCP Server at {mcp_url} ---")

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="agent-createcharacter",
    description="Validates a character against a world and saves it to the database.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(url=mcp_url)
        )
    ],
)

a2a_app = to_a2a(root_agent, port=int(os.getenv("PORT", 8080)))
