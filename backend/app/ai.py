import os
import json
import uuid
import logging
from dotenv import load_dotenv

# Ensure we use ADK instead of generic generativeai
from google.adk.agents import LlmAgent
from google.genai import types

load_dotenv()

# We can configure ADK's LlmAgent directly
MODEL_NAME = 'gemini-1.5-flash'

async def generate_world_intro(world_data: dict):
    """
    Generates a rich narrative introduction for a world based on its metadata.
    """
    prompt = f"""
    You are an expert game master and storyteller. 
    Create a rich, immersive narrative introduction (approx 2-3 paragraphs) for a new storytelling world with the following details:
    
    Name: {world_data['name']}
    Era: {world_data['era']}
    Environment: {world_data['environment']}
    Tone: {world_data['tone']}
    Description: {world_data.get('description', 'N/A')}
    
    Focus on setting the scene and establishing the mood.
    """
    
    agent = LlmAgent(
        model=MODEL_NAME,
        name="WorldIntroAgent",
        description="Generates a narrative intro for a world.",
        instruction="You are an expert game master and storyteller."
    )
    
    try:
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        runner = Runner(agent=agent, session_service=InMemorySessionService(), app_name="rpg-app")
        from google.adk.events import UserMessage, UserMessageContent

        # Run agent
        events = runner.run(user_id="system", session_id=str(uuid.uuid4()), new_message=UserMessage(content=UserMessageContent(parts=[prompt])))
        final_text = ""
        for event in events:
            if hasattr(event, 'content') and hasattr(event.content, 'text'):
                 final_text += event.content.text
            elif hasattr(event, 'message') and hasattr(event.message, 'content') and event.message.content.parts:
                 for part in event.message.content.parts:
                     final_text += part.text
            elif event.type == "model_response":
                 if hasattr(event, 'data') and event.data:
                     # Usually model responses come in event.data.content.parts
                     try:
                         final_text += event.data.content.parts[0].text
                     except:
                         pass
        
        return final_text.strip() if final_text else f"Welcome to {world_data['name']}, a land of {world_data['tone']} set in the {world_data['era']}."
    except Exception as e:
        logging.error(f"Failed to generate intro: {e}")
        return f"Welcome to {world_data['name']}, a land of {world_data['tone']} set in the {world_data['era']}."

async def validate_character_fit(world_data: dict, char_data: dict):
    """
    Validates if a character fits the established world lore and rules.
    Returns (is_valid, reasoning).
    """
    prompt = f"""
    You are a lore expert and game moderator. 
    Validate if the following character fits the storytelling world described.
    
    WORLD DETAILS:
    Name: {world_data['name']}
    Era: {world_data['era']}
    Environment: {world_data['environment']}
    Tone: {world_data['tone']}
    World Description: {world_data.get('description', 'N/A')}
    
    CHARACTER DETAILS:
    Name: {char_data['name']}
    Age: {char_data['age']}
    Archetype: {char_data['archetype']}
    Backstory: {char_data['backstory']}
    Visual Description: {char_data['visual_description']}
    
    Output your response in the following JSON format:
    {{
        "is_valid": true,
        "reasoning": "string explaining why the character fits or doesn't fit the world"
    }}
    
    A character should only be rejected if they fundamentally break the setting.
    """
    
    agent = LlmAgent(
        model=MODEL_NAME,
        name="ValidatorAgent",
        description="Validates a character.",
        instruction="You are a lore expert. Output pure JSON without markdown blocks."
    )
    
    try:
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        runner = Runner(agent=agent, session_service=InMemorySessionService(), app_name="rpg-app")
        from google.adk.events import UserMessage, UserMessageContent
        events = runner.run(user_id="system", session_id=str(uuid.uuid4()), new_message=UserMessage(content=UserMessageContent(parts=[prompt])))
        text = ""
        for event in events:
            if event.type == "model_response" and hasattr(event, 'data'):
                try:
                    text += event.data.content.parts[0].text
                except:
                    pass

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        result = json.loads(text)
        return result.get("is_valid", True), result.get("reasoning", "Fits the world.")
    except Exception as e:
        logging.error(f"Failed character validation: {e}")
        return True, "Lore validation skipped due to technical error."

async def generate_character_portrait(world_data: dict, char_data: dict):
    """
    Generates an AI character portrait URL. 
    """
    return f"https://picsum.photos/seed/{char_data['name']}/512/512"

async def generate_next_scene(world_data: dict, char_data: dict, history: list = None, last_choice: str = None):
    """
    Generates the next narrative scene and a set of choices.
    """
    history_str = ""
    if history:
        history_str = "PREVIOUS STORY EVENTS:\n" + "\n".join([f"Scene: {h['narrative']}\nChoice: {h['choice']}" for h in history])
        
    world_state_str = ""
    if world_data.get("structured_state"):
        state = world_data["structured_state"]
        world_state_str = f"""
        CURRENT WORLD STATE CONTEXT:
        - Major Active Region: {state.get('location', 'Unknown')}
        - Global Tension Delta: {state.get('tension_delta', 0)}
        - Factions: {state.get('faction_changes', [])}
        - Current Rumors: {state.get('rumors_added', [])}
        - Open Plot Hooks: {state.get('story_hooks_unlocked', [])}
        """
    
    last_choice_str = f"The player chose: {last_choice}" if last_choice else "This is the start of the adventure."
    
    prompt = f"""
    You are an expert game master. Generate the next scene in an asynchronous storytelling RPG.
    
    WORLD: {world_data['name']} ({world_data['era']}, {world_data['tone']})
    CHARACTER: {char_data['name']}, a {char_data['age']} year old {char_data['archetype']}. Backstory: {char_data['backstory']}
    
    {world_state_str}
    
    {history_str}
    
    {last_choice_str}
    
    TASK:
    1. Write 2-3 paragraphs of immersive narrative for the current scene.
    2. Provide 2-4 distinct, numbered choices for the player.
    
    Output in JSON format:
    {{
        "narrative": "the story text",
        "choices": [
            {{"id": 1, "text": "choice one description"}},
            {{"id": 2, "text": "choice two description"}}
        ]
    }}
    """
    
    agent = LlmAgent(
        model=MODEL_NAME,
        name="NarrativeAgent",
        description="Generates next scene.",
        instruction="You are an expert game master. Output pure JSON."
    )
    
    try:
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        runner = Runner(agent=agent, session_service=InMemorySessionService(), app_name="rpg-app")
        from google.adk.events import UserMessage, UserMessageContent
        events = runner.run(user_id="system", session_id=str(uuid.uuid4()), new_message=UserMessage(content=UserMessageContent(parts=[prompt])))
        text = ""
        for event in events:
            if event.type == "model_response" and hasattr(event, 'data'):
                try:
                    text += event.data.content.parts[0].text
                except:
                    pass

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        logging.error(f"Failed next scene: {e}")
        return {
            "narrative": f"The journey continues for {char_data['name']} in the {world_data['name']}.",
            "choices": [{"id": 1, "text": "Press onward"}, {"id": 2, "text": "Look for shelter"}]
        }

async def generate_session_summary(world_data: dict, char_data: dict, history: list):
    """
    Generates a narrative summary of the session's events and the character's impact.
    """
    history_str = "STORY EVENTS:\n" + "\n".join([f"Scene: {h['narrative']}\nChoice: {h['choice']}" for h in history])
    
    prompt = f"""
    You are an expert game master. The story session has concluded. 
    Summarize the character's journey and the impact they had on the world.
    
    WORLD: {world_data['name']}
    CHARACTER: {char_data['name']}
    
    {history_str}
    
    Provide a 1-2 paragraph conclusion that wraps up this specific adventure.
    """
    
    agent = LlmAgent(
        model=MODEL_NAME,
        name="SummaryAgent",
        description="Summarizes the session.",
        instruction="You are an expert game master."
    )
    
    try:
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        runner = Runner(agent=agent, session_service=InMemorySessionService(), app_name="rpg-app")
        from google.adk.events import UserMessage, UserMessageContent
        events = runner.run(user_id="system", session_id=str(uuid.uuid4()), new_message=UserMessage(content=UserMessageContent(parts=[prompt])))
        text = ""
        for event in events:
            if event.type == "model_response" and hasattr(event, 'data'):
                try:
                    text += event.data.content.parts[0].text
                except:
                    pass
        return text.strip() if text else f"{char_data['name']}'s journey in {world_data['name']} has come to an end for now."
    except Exception as e:
        logging.error(f"Failed summary: {e}")
        return f"{char_data['name']}'s journey in {world_data['name']} has come to an end for now."

async def generate_world_state_update(world_data: dict, char_data: dict, history: list):
    """
    Analyzes the concluded session to extract structured world changes.
    Returns a JSON string of state deltas.
    """
    history_str = "STORY EVENTS:\n" + "\n".join([f"Scene: {h['narrative']}\nChoice: {h['choice']}" for h in history])
    
    prompt = f"""
    You are an expert game master. The story session has concluded.
    Analyze the session events and extract the structured consequences to the world state.
    
    WORLD: {world_data['name']}
    CHARACTER: {char_data['name']}
    
    {history_str}
    
    Output your response in the following JSON format:
    {{
      "location": "The region where most events took place",
      "tension_delta": 0,
      "faction_changes": [
        {{ "faction": "Name of faction", "status": "new status" }}
      ],
      "rumors_added": [
        "A short rumor based on the events"
      ],
      "story_hooks_unlocked": [
        "A future plot hook based on the resolution"
      ],
      "global_impact": false
    }}
    
    Ensure tension_delta is an integer (e.g. +1, -2).
    """
    
    agent = LlmAgent(
        model=MODEL_NAME,
        name="StateUpdateAgent",
        description="Extracts structured world state changes.",
        instruction="You are an expert game master. Output pure JSON."
    )
    
    try:
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        runner = Runner(agent=agent, session_service=InMemorySessionService(), app_name="rpg-app")
        from google.adk.events import UserMessage, UserMessageContent
        events = runner.run(user_id="system", session_id=str(uuid.uuid4()), new_message=UserMessage(content=UserMessageContent(parts=[prompt])))
        text = ""
        for event in events:
            if event.type == "model_response" and hasattr(event, 'data'):
                try:
                    text += event.data.content.parts[0].text
                except:
                    pass

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        logging.error(f"Failed state update generation: {e}")
        return {
            "location": "Unknown",
            "tension_delta": 0,
            "faction_changes": [],
            "rumors_added": [f"{char_data['name']} passed through the area."],
            "story_hooks_unlocked": [],
            "global_impact": False
        }

async def generate_while_away_summary(world_data: dict, char_data: dict, recent_events: list):
    """
    Generates a recap for returning players based on events that happened since their last session.
    """
    if not recent_events:
        return f"Welcome back to {world_data['name']}. The world has been quiet since you last departed."
        
    events_str = "RECENT EVENTS IN THE WORLD:\n" + "\n".join([f"- Location: {e.get('location', 'Unknown')} | Event: {e.get('summary', '')}" for e in recent_events])
    
    prompt = f"""
    You are an expert game master. A player is returning to the storytelling RPG after some time away.
    Other players have been active in the shared world, causing changes.
    
    WORLD: {world_data['name']}
    CHARACTER: {char_data['name']}
    
    {events_str}
    
    Create a brief, atmospheric "While You Were Away" summary (1-2 paragraphs).
    Focus on how the world has shifted, new tensions or opportunities, and what their character might hear as rumors upon returning.
    """
    
    agent = LlmAgent(
        model=MODEL_NAME,
        name="WhileAwayAgent",
        description="Generates a recap of recent world events.",
        instruction="You are an expert game master bringing an asynchronous player back up to speed."
    )
    
    try:
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        runner = Runner(agent=agent, session_service=InMemorySessionService(), app_name="rpg-app")
        from google.adk.events import UserMessage, UserMessageContent
        events = runner.run(user_id="system", session_id=str(uuid.uuid4()), new_message=UserMessage(content=UserMessageContent(parts=[prompt])))
        text = ""
        for event in events:
            if event.type == "model_response" and hasattr(event, 'data'):
                try:
                    text += event.data.content.parts[0].text
                except:
                    pass
        return text.strip() if text else f"The world of {world_data['name']} continues to turn, though rumors are sparse."
    except Exception as e:
        logging.error(f"Failed while-away summary: {e}")
        return f"The world of {world_data['name']} continues to turn, though rumors are sparse."
