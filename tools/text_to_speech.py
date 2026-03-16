#!/usr/bin/env python3
"""Text-to-Speech Generation Tool.

Generates speech audio from text using Google Gemini 2.5 Flash TTS capabilities.
This script can be run on the command-line to synthesize NPC dialogue.

Examples:
    Run the generation for a specific character voice:
        $ uv run python tools/text_to_speech.py \\
            --text "Hello traveler, I am Puck, waiting for you." \\
            --voice "Puck" \\
            --output ./assets/audio/sample_puck_male.wav

Attributes:
    TTS_MODEL (str): The specific Gemini model variation used for text-to-speech.
"""
import argparse
import os
import sys
import wave
from typing import Optional
from google import genai

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Define the model to use for TTS
TTS_MODEL = "gemini-2.5-flash-preview-tts"

def get_client(api_key: Optional[str] = None) -> genai.Client:
    """Initializes the Gemini internal client using an API key or ADC (Vertex AI).

    Args:
        api_key: An optional string override for the API key.

    Returns:
        A configured `genai.Client` instance ready to make requests.

    SystemExit:
        If neither an explicit GEMINI_API_KEY nor a GOOGLE_CLOUD_PROJECT exist.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if key:
        return genai.Client(api_key=key)
    # Fall back to Application Default Credentials via Vertex AI
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    if not project:
        print("Error: Set GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT for ADC auth.")
        sys.exit(1)
    print(f"Using ADC auth (project={project}, location={location})")
    return genai.Client(vertexai=True, project=project, location=location)


def generate_speech(text: str, voice_name: str, output_path: str, api_key: Optional[str] = None) -> None:
    """Generates audio from text using Gemini TTS.

    This requests the audio generation and natively writes the PCM WAV response
    directly into a `.wav` file at the specified output path.

    Args:
        text: The string content representing the dialogue to synthesize.
        voice_name: The target character voice profile (e.g., 'Puck', 'Aoede').
        output_path: The filesystem path where the `.wav` file should be written.
        api_key: Optional explicitly provided Gemini API key.

    SystemExit:
        On any exception relating to API endpoints or failure to parse audio data.
    """
    print(f"Generating speech with {TTS_MODEL}...")
    print(f"Voice: {voice_name}")
    print(f"Output: {output_path}")

    # Set up output directory
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    try:
        # Get the initialized client
        client = get_client(api_key)

        # Call the API with audio response modality
        print("Waiting for generation...")
        response = client.models.generate_content(
            model=TTS_MODEL,
            contents=text,
            config={
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": voice_name
                        }
                    }
                }
            }
        )

        # Extract audio inline data and save to file
        # Check if the parts exist and contain inline_data
        candidates = response.candidates
        if not candidates:
            print("Error: No candidates returned from the API.")
            sys.exit(1)

        parts = candidates[0].content.parts
        if not parts:
            print("Error: No parts returned in the content.")
            sys.exit(1)

        audio_part = None
        for part in parts:
            if hasattr(part, "inline_data") and part.inline_data:
                audio_part = part.inline_data
                break
                
        if not audio_part:
            print("Error: Generated response did not contain audio data.")
            sys.exit(1)

        # Write raw PCM data with a proper WAV header (24kHz, 16-bit, mono)
        audio_data = audio_part.data
        with wave.open(output_path, "wb") as wf:
            wf.setnchannels(1)       # mono
            wf.setsampwidth(2)       # 16-bit
            wf.setframerate(24000)   # 24 kHz
            wf.writeframes(audio_data)

        print(f"\nOK: Successfully saved text-to-speech audio to:\n{output_path}")

    except Exception as e:
        print(f"\nERROR: Failed to generate speech: {e}")
        sys.exit(1)


def main() -> None:
    """Parses command-line arguments and runs the speech generation process."""
    parser = argparse.ArgumentParser(description="Generate speech from text using Gemini API.")
    parser.add_argument("--text", required=True, help="The text to synthesize into speech.")
    parser.add_argument("--voice", default="Puck", help="Voice name to use (e.g. Puck, Aoede, Charon, Kore, Fenrir).")
    parser.add_argument(
        "--output",
        default="./assets/audio/speech_output.wav",
        help="Path where the generated .wav file should be saved."
    )
    parser.add_argument("--api-key", help="Gemini API key (overrides GEMINI_API_KEY env var).")

    args = parser.parse_args()
    
    # Run Generation
    generate_speech(
        text=args.text,
        voice_name=args.voice,
        output_path=args.output,
        api_key=args.api_key
    )


if __name__ == "__main__":
    main()
