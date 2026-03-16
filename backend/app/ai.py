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
        # Extract JSON from markdown blocks if present
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
    Note: Real implementation would use Imagen or another Image gen API.
    For this MVP/demo, we'll use a high-quality placeholder that matches the description.
    """
    # In a real app, this would be a prompt for an Image Gen model
    prompt = f"A professional character portrait of {char_data['name']}, a {char_data['age']} year old {char_data['archetype']}. " \
             f"Setting: {world_data['era']} world of {world_data['name']}. " \
             f"Visual Details: {char_data['visual_description']}. " \
             f"Style: Consistent with {world_data['tone']} mood."
    
    # Placeholder using a service like Lexica or similar if we wanted real images,
    # or just a high-quality placeholder image for now.
    # Let's use a themed placeholder for the demo.
    return f"https://picsum.photos/seed/{char_data['name']}/512/512"
