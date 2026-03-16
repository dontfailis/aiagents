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
    "You are an expert game master and storyteller. "
    "Your purpose is to receive details about a new storytelling world and use the 'create_world' tool to save it. "
    "Before saving, create a rich, immersive narrative introduction (approx 2-3 paragraphs) based on the provided details. "
    "Once the world is created, simply return the response you get from the tool."
)

logger.info("--- 🔧 Loading MCP tools from MCP Server... ---")
logger.info("--- 🤖 Creating ADK World Builder Agent... ---")

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="world_builder",
    description="An agent that creates storytelling worlds.",
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
a2a_app = to_a2a(root_agent, port=10001)
