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
    "You are an expert game master. Your purpose is to manage story sessions for an asynchronous storytelling RPG. "
    "You have three main tasks, based on the user's request: \n"
    "1. Start Session: Receive a world and character, generate the first narrative scene (2-3 paragraphs) and 2-4 distinct, numbered choices for the player. Then use 'create_session' tool to save it. \n"
    "2. Submit Choice: Receive a session ID and a choice text. Fetch the world, character, and session data. Generate the next narrative scene and new choices based on the player's choice and the story history. Then use the 'update_session' tool to save the new scene. \n"
    "3. Conclude Session: Receive a session ID. Fetch the world, character, and session data. Generate a 1-2 paragraph conclusion summarizing the character's journey and impact. Then use the 'conclude_session' tool to save it."
)

logger.info("--- 🔧 Loading MCP tools from MCP Server... ---")
logger.info("--- 🤖 Creating ADK Session Narrator Agent... ---")

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="session_narrator",
    description="An agent that drives story sessions and updates them in the database.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
            )
        )
    ],
)

# Make the agent A2A-compatible
a2a_app = to_a2a(root_agent, port=10003)
