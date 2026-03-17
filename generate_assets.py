"""Generate landing page assets (hero image + intro audio) using Gemini/Imagen."""
import base64
import os
import struct
import wave
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("No GEMINI_API_KEY or GOOGLE_API_KEY found in environment.")

client = genai.Client(api_key=API_KEY)
OUT_DIR = Path(__file__).parent / "frontend" / "public"
OUT_DIR.mkdir(parents=True, exist_ok=True)


PANEL_IMAGES = [
    (
        "panel-create.jpg",
        (
            "Epic fantasy world creation: a lone figure standing before a swirling portal of golden "
            "magical energy, ancient stone ruins, dramatic aurora in a dark sky, cinematic wide shot, "
            "dark fantasy art, ultra detailed, no text"
        ),
    ),
    (
        "panel-join.jpg",
        (
            "A group of diverse adventurers gathered around a glowing arcane map inside a candlelit "
            "stone tavern, warm amber light, ready to embark on a great quest, fantasy RPG atmosphere, "
            "cinematic wide shot, ultra detailed, no text"
        ),
    ),
]

SLIDE_IMAGES = [
    (
        "hero-bg.jpg",
        (
            "Epic fantasy landscape: the ancient realm of AETHELARD at golden hour. "
            "A sweeping vista of ruined stone towers draped in ivy rising from a mist-filled valley, "
            "snow-capped mountains in the distance, a crimson and amber sky streaked with clouds, "
            "a lone traveler silhouetted on a winding cobblestone path, "
            "torches glowing along crumbling battlements, atmospheric volumetric fog, "
            "cinematic widescreen, painterly digital art, ultra-detailed, 8K"
        ),
    ),
    (
        "slide-ember-wastes.jpg",
        (
            "Epic fantasy landscape: the Ember Wastes, a vast volcanic wasteland under a blood-red sky. "
            "Glowing rivers of lava cutting through obsidian plains, ash clouds billowing from distant calderas, "
            "ancient ruins half-buried in volcanic rock, embers drifting like fireflies, "
            "a lone armored warrior silhouetted against the hellish glow, "
            "cinematic widescreen, painterly digital art, ultra-detailed, 8K"
        ),
    ),
    (
        "slide-sunken-citadel.jpg",
        (
            "Epic fantasy landscape: the Sunken Citadel, an ancient fortress submerged beneath dark ocean waters. "
            "Massive stone towers encrusted with coral and seaweed rising from a twilight sea, "
            "bioluminescent creatures glowing in the deep, moonlight filtering through dark waves, "
            "ghostly lights flickering in sunken windows, a ship silhouetted above on stormy waters, "
            "cinematic widescreen, painterly digital art, ultra-detailed, 8K"
        ),
    ),
    (
        "slide-gilded-throne.jpg",
        (
            "Epic fantasy interior: the Gilded Throne room of a fallen empire. "
            "Towering golden columns draped in cobwebs, a massive jeweled throne on a cracked marble dais, "
            "rays of dusty amber light cutting through shattered stained glass windows, "
            "treasure scattered across ancient stone floors, a lone figure standing before the throne, "
            "cinematic widescreen, painterly digital art, ultra-detailed, 8K"
        ),
    ),
    (
        "slide-verdant-expanse.jpg",
        (
            "Epic fantasy landscape: the Verdant Expanse, an ancient primordial forest of colossal trees. "
            "Massive root systems forming archways over a mist-filled forest floor, "
            "shafts of emerald light piercing the canopy, strange glowing flowers and ancient stone idols, "
            "a winding path disappearing into deep green shadows, ethereal spirits drifting between the trees, "
            "cinematic widescreen, painterly digital art, ultra-detailed, 8K"
        ),
    ),
]


def generate_images(image_list: list) -> None:
    for filename, prompt in image_list:
        out_path = OUT_DIR / filename
        if out_path.exists():
            print(f"  Skipping {filename} (already exists)")
            continue
        print(f"Generating {filename} with Imagen...")
        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
            ),
        )
        img_bytes = response.generated_images[0].image.image_bytes
        out_path.write_bytes(img_bytes)
        print(f"  Saved -> {out_path}")


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


def generate_intro_audio() -> None:
    print("Generating intro narration with Gemini TTS...")
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=(
            "Speak this as a deep, dramatic, ancient storyteller with a slow, resonant, "
            "cinematic voice full of gravitas and mystery — like the opening of an epic fantasy saga: "
            "\n\n"
            "In ages forgotten by mortal memory... "
            "when the stars were young and the earth still trembled with the breath of creation... "
            "the realm of Aethelard was forged from shadow and starlight. "
            "Heroes rose and fell like tides. "
            "Their legends carved into stone, their sacrifices woven into the very fabric of the world. "
            "Now the age of reckoning stirs once more. "
            "The path before you is unwritten. "
            "The choices are yours alone. "
            "Forge your legend."
        ),
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"
                    )
                )
            ),
        ),
    )

    part = response.candidates[0].content.parts[0]
    raw = base64.b64decode(part.inline_data.data)
    mime = part.inline_data.mime_type  # e.g. "audio/pcm;rate=24000"

    rate = 24000
    if "rate=" in mime:
        try:
            rate = int(mime.split("rate=")[1].split(";")[0])
        except ValueError:
            pass

    wav_bytes = _pcm_to_wav(raw, sample_rate=rate)
    out_path = OUT_DIR / "intro-audio.wav"
    out_path.write_bytes(wav_bytes)
    print(f"  Saved -> {out_path}")


if __name__ == "__main__":
    generate_images(SLIDE_IMAGES)
    generate_images(PANEL_IMAGES)
    generate_intro_audio()
    print("\nAll assets generated successfully.")
