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
    "You are an expert game master. Your task is to receive parameters for a new world, "
    "generate a 2-3 paragraph rich narrative introduction based on the environment, era, and tone, "
    "and then use the 'create_world' tool to save it to the database. "
    "Return a concise success message once created, along with the generated introduction."
)

mcp_url = os.getenv("cloud_run_1_SERVICE_ENDPOINT", os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp"))
logger.info(f"--- 🔧 Connecting to MCP Server at {mcp_url} ---")

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="agent-createworld",
    description="Generates a narrative introduction for a world and saves it to the database.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(url=mcp_url)
        )
    ],
)

a2a_app = to_a2a(root_agent, port=int(os.getenv("PORT", 8080)))
