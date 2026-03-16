import asyncio
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import SendMessageRequest, MessageSendParams
import httpx
import uuid
from typing import Any

AGENT_URL = "http://localhost:10001"

async def run():
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=AGENT_URL)
        agent_card = await resolver.get_agent_card()
        client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

        payload = {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": "Create a new medieval fantasy world with adventure tone called 'Shadow Keep'"}],
                "messageId": uuid.uuid4().hex,
            },
        }

        request = SendMessageRequest(id=str(uuid.uuid4()), params=MessageSendParams(**payload))
        response = await client.send_message(request)
        print(response.root.model_dump_json(exclude_none=True))

if __name__ == "__main__":
    asyncio.run(run())
