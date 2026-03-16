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
    "You will receive instructions to create a new session or update an existing one. "
    "You MUST use the 'create_session', 'get_session', 'update_session', or 'conclude_session' tools to read or update the database based on the request. "
    "When creating a narrative, write 2-3 paragraphs. "
    "When asked, you must read the database, generate narrative, and then save it using the appropriate tool. "
    "Your final response MUST be a pure JSON representation of the final tool output you received. "
    "DO NOT output markdown blocks or conversational text, ONLY raw JSON."
)

base_mcp = os.getenv("cloud_run_1_SERVICE_ENDPOINT", os.getenv("MCP_SERVER_URL", "http://localhost:8080")).rstrip("/")
mcp_url = f"{base_mcp}/mcp"
logger.info(f"--- 🔧 Connecting to MCP Server at {mcp_url} ---")

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="agent_narrative",
    description="Generates narrative scenes and orchestrates the session database updates.",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(url=mcp_url)
        )
    ],
)

a2a_app = to_a2a(root_agent, port=int(os.getenv("PORT", 8080)))
