import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini API
api_key = os.getenv("GOOGLE_API_KEY") # You might need to set this or use ADC
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
    
    # In a real async environment, we'd use the async version of the SDK if available or run in thread
    # For MVP simplicity, we'll use a mock for testing or handle the sync call
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Fallback for testing/unconfigured environments
        return f"Welcome to {world_data['name']}, a land of {world_data['tone']} set in the {world_data['era']}."
