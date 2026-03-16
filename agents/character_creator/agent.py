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
    "You are a lore expert and game moderator. "
    "Your purpose is to receive details about a world and a new character. "
    "First, validate if the character fits the storytelling world described. A character should only be rejected if they fundamentally break the setting. "
    "Generate a reasoning string and a boolean 'is_valid' flag. "
    "Then, generate a placeholder portrait URL for the character (e.g. using picsum.photos). "
    "Finally, use the 'create_character' tool to save the character to the database, passing all details, including the 'is_valid' check reasoning and portrait URL. "
    "If the character is invalid, do not create them, instead just return a message explaining why."
)

logger.info("--- 🔧 Loading MCP tools from MCP Server... ---")
logger.info("--- 🤖 Creating ADK Character Creator Agent... ---")

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="character_creator",
    description="An agent that validates and creates characters.",
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
a2a_app = to_a2a(root_agent, port=10002)
