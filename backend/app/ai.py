import os
import google.generativeai as genai
import json
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GOOGLE_API_KEY") 
if api_key:
    genai.configure(api_key=api_key)

async def generate_world_intro(world_data: dict):
    """
    Generates a rich narrative introduction for a world based on its metadata.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Welcome to {world_data['name']}, a land of {world_data['tone']} set in the {world_data['era']}."

async def validate_character_fit(world_data: dict, char_data: dict):
    """
    Validates if a character fits the established world lore and rules.
    Returns (is_valid, reasoning).
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
        "is_valid": boolean,
        "reasoning": "string explaining why the character fits or doesn't fit the world"
    }}
    
    A character should only be rejected if they fundamentally break the setting (e.g., a cyborg in a low-fantasy medieval setting).
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        result = json.loads(text)
        return result.get("is_valid", True), result.get("reasoning", "Fits the world.")
    except Exception as e:
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
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    history_str = ""
    if history:
        history_str = "PREVIOUS STORY EVENTS:\n" + "\n".join([f"Scene: {h['narrative']}\nChoice: {h['choice']}" for h in history])
    
    last_choice_str = f"The player chose: {last_choice}" if last_choice else "This is the start of the adventure."
    
    prompt = f"""
    You are an expert game master. Generate the next scene in an asynchronous storytelling RPG.
    
    WORLD: {world_data['name']} ({world_data['era']}, {world_data['tone']})
    CHARACTER: {char_data['name']}, a {char_data['age']} year old {char_data['archetype']}. Backstory: {char_data['backstory']}
    
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
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        return {
            "narrative": f"The journey continues for {char_data['name']} in the {world_data['name']}.",
            "choices": [{"id": 1, "text": "Press onward"}, {"id": 2, "text": "Look for shelter"}]
        }

async def generate_session_summary(world_data: dict, char_data: dict, history: list):
    """
    Generates a narrative summary of the session's events and the character's impact.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    history_str = "STORY EVENTS:\n" + "\n".join([f"Scene: {h['narrative']}\nChoice: {h['choice']}" for h in history])
    
    prompt = f"""
    You are an expert game master. The story session has concluded. 
    Summarize the character's journey and the impact they had on the world.
    
    WORLD: {world_data['name']}
    CHARACTER: {char_data['name']}
    
    {history_str}
    
    Provide a 1-2 paragraph conclusion that wraps up this specific adventure.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"{char_data['name']}'s journey in {world_data['name']} has come to an end for now."
