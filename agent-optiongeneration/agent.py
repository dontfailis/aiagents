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
    "You are the dungeon master responsible for presenting meaningful player actions in a collaborative fantasy RPG. "
    "You will receive the current narrative scene. "
    "Read it like a game master preparing the table's next turn. "
    "Provide 3-4 distinct, numbered choices that are tightly grounded in the specific scene details. "
    "Each choice must respond to named characters, threats, clues, terrain, or tensions already present in the scene. "
    "Choices must represent different approaches with different likely consequences, such as force, stealth, diplomacy, sacrifice, caution, or investigation. "
    'Do not write generic filler like "press onward" or duplicate the same action with different wording. '
    "Every choice should be actionable, story-specific, and capable of changing the next scene in a meaningful way. "
    "Output MUST be pure JSON in the following format, with NO markdown formatting: "
    "[ {\"id\": 1, \"text\": \"choice description\"}, {\"id\": 2, \"text\": \"choice description\"} ]"
)

# No DB tools strictly needed here, just pure generation, but we can provide them just in case
base_mcp = os.getenv("cloud_run_1_SERVICE_ENDPOINT", os.getenv("MCP_SERVER_URL", "http://localhost:8080")).rstrip("/")
mcp_url = f"{base_mcp}/mcp"
logger.info(f"--- 🔧 Connecting to MCP Server at {mcp_url} ---")

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="agent_optiongeneration",
    description="Generates JSON choices for the player based on the current narrative scene.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(url=mcp_url),
            lazy_init=True,
        )
    ],
)

a2a_app = to_a2a(root_agent, port=int(os.getenv("PORT", 8080)))
