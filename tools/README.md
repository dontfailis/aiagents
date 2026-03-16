# Image Generation Tools

Tools for generating all graphical assets in the AI Storytelling RPG using **Google Gemini Imagen 3**.

---

## Setup

### 1. Install dependency

```bash
pip install -r tools/requirements.txt
```

### 2. Configure API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

All tools load this file automatically. You can also pass `--api-key <key>` directly to any tool, or set `GEMINI_API_KEY` as an environment variable.

---

## Tools Overview

| Tool | Purpose | Used On | Output |
|------|---------|---------|--------|
| `generate_portrait.py` | Character portrait options | Portrait Selection screen | 3:4 PNG × 3–4 |
| `generate_world_banner.py` | World hero/banner art | Landing, Join World, Chronicle, "While You Were Away" | 16:9 PNG |
| `generate_scene_art.py` | Story scene illustration | Story Play, End-of-Session Summary | 16:9 PNG |
| `generate_location_art.py` | World location thumbnails | World Map / Region Model | 4:3 PNG |
| `text_to_speech.py` | Generates character speech audio | Story Play, Dialogue scenes | WAV Audio |
| `_gemini.py` | Shared Imagen client | (internal, not called directly) | — |

---

## Tool Reference

### `text_to_speech.py` — Character Speech Generation

Generates natural-sounding voice dialogue for the characters using the Gemini text-to-speech API models. Designed to provide distinct voice variations for different roles in the RPG.

**Arguments**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--text` | Yes | — | The dialogue text to synthesize |
| `--voice`| No | `Puck` | AI Voice profile. Options: `Puck` (Male), `Aoede` (Female), `Charon` (Old Man), `Kore` (Confident), `Fenrir` |
| `--output` | No | `./assets/audio/speech_output.wav` | Output filename/directory |
| `--api-key` | No | — | Overrides the env key |

**Example**

```bash
uv run python tools/text_to_speech.py \
  --text "Hello traveler, I am Puck, waiting for you." \
  --voice "Puck" \
  --output ./assets/audio/sample_puck_male.wav
```

**Output:** `./assets/audio/sample_puck_male.wav`

---

## Tool Reference

### `generate_portrait.py` — Character Portraits

Generates 3–4 portrait options for a character. Players pick one as their canonical identity.

**Arguments**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--name` | Yes | — | Character name |
| `--archetype` | Yes | — | Role: Rogue, Scholar, Warrior, Survivor, Merchant, Wanderer |
| `--description` | Yes | — | Visual cues (appearance, clothing, mood) |
| `--world` | No | `Medieval Fantasy` | World type |
| `--tone` | No | `Adventure` | Story tone |
| `--count` | No | `4` | Number of portraits (1–4) |
| `--output` | No | `./portraits` | Output directory |
| `--api-key` | No | — | Overrides env key |

**Example**

```bash
python tools/generate_portrait.py \
  --name "Kira" \
  --archetype "Rogue" \
  --description "A nimble woman in her 30s, dark hair, leather armor, scar on left cheek" \
  --world "Medieval Fantasy" \
  --tone "Adventure" \
  --count 4 \
  --output ./assets/portraits
```

**Output:** `./assets/portraits/kira_20260316_143022_1.png` … `_4.png`

---

### `generate_world_banner.py` — World Banner / Hero Art

Generates a wide cinematic banner for a world. Also supports generating the three preset **world type preview cards** shown on the Create World screen.

**Arguments**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--name` | No | `Unnamed World` | World name |
| `--setting` | No | `Medieval Fantasy` | `Medieval Fantasy`, `Post-Apocalyptic`, `Modern Mystery` |
| `--environment` | No | `kingdom` | e.g. city, wilderness, wasteland, space colony |
| `--era` | No | `medieval` | Timeline description |
| `--tone` | No | `Adventure` | `Adventure`, `Exploration`, `Intrigue`, `Survival` |
| `--preset` | No | `false` | Generate one preview card for all 3 world types |
| `--output` | No | `./banners` | Output directory |
| `--api-key` | No | — | Overrides env key |

**Example — custom world banner**

```bash
python tools/generate_world_banner.py \
  --name "The Shattered Realm" \
  --setting "Medieval Fantasy" \
  --environment "kingdom" \
  --era "medieval" \
  --tone "Adventure" \
  --output ./assets/banners
```

**Example — generate all 3 world type preset cards (run once at dev time)**

```bash
python tools/generate_world_banner.py --preset --output ./assets/banners
```

**Output:** `./assets/banners/presets/medieval_fantasy_*.png`, `post_apocalyptic_*.png`, `modern_mystery_*.png`

---

### `generate_scene_art.py` — Story Scene Illustration

Generates an atmospheric background illustration for a story scene. No foreground characters — the art sets the mood without overriding the player's imagination.

**Arguments**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--description` | Yes | — | Narrative description of the scene environment |
| `--location` | Yes | — | Named world location (e.g. Harbor District) |
| `--world` | No | `Medieval Fantasy` | World type |
| `--tone` | No | `Adventure` | Story tone |
| `--session-id` | No | `scene` | Used as filename prefix (e.g. session ID or scene number) |
| `--output` | No | `./scenes` | Output directory |
| `--api-key` | No | — | Overrides env key |

**Example**

```bash
python tools/generate_scene_art.py \
  --description "A rain-soaked dockside tavern at midnight, shadowy figures huddled at tables" \
  --location "Harbor District" \
  --world "Medieval Fantasy" \
  --tone "Intrigue" \
  --session-id "session_001_scene_03" \
  --output ./assets/scenes
```

**Output:** `./assets/scenes/session_001_scene_03_20260316_143022_1.png`

---

### `generate_location_art.py` — Location Thumbnails

Generates a thumbnail for each named location in the world's region model. Each world has 5–8 locations (per PRD §5.8). Supports generating a single location or all defaults for a world type at once.

**Arguments**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--name` | Conditional | — | Location name (required unless `--generate-defaults`) |
| `--description` | Conditional | — | Visual description (required unless `--generate-defaults`) |
| `--world` | No | `Medieval Fantasy` | World type |
| `--tone` | No | `Adventure` | Story tone |
| `--generate-defaults` | No | `false` | Generate thumbnails for all 8 default locations of the selected world type |
| `--output` | No | `./locations` | Output directory |
| `--api-key` | No | — | Overrides env key |

**Default locations per world type**

| Medieval Fantasy | Post-Apocalyptic | Modern Mystery |
|---|---|---|
| North City | Ruins District | Downtown |
| Old Forest | Survivor Camp | Old Quarter |
| Harbor District | Wasteland Highway | Police Precinct |
| Desert Pass | Underground Vault | Harbor Docks |
| Mountain Keep | Scavenger Market | Underground |
| River Settlement | Quarantine Zone | University Campus |
| Borderlands | Power Plant | Industrial Zone |
| Market Square | Outpost Bravo | Luxury District |

**Example — single location**

```bash
python tools/generate_location_art.py \
  --name "Harbor District" \
  --description "A bustling port with crowded docks, fishing boats, and merchant warehouses" \
  --world "Medieval Fantasy" \
  --tone "Adventure" \
  --output ./assets/locations
```

**Example — all default locations for a world type**

```bash
python tools/generate_location_art.py \
  --world "Post-Apocalyptic" \
  --tone "Survival" \
  --generate-defaults \
  --output ./assets/locations
```

**Output:** `./assets/locations/post-apocalyptic/ruins_district_*.png` … (8 files)

---

## Suggested Asset Generation Order

When setting up a new world, generate assets in this order:

```bash
# 1. World type preview cards (one-time, at dev time)
python tools/generate_world_banner.py --preset --output ./assets/banners

# 2. World banner (when a player creates a world)
python tools/generate_world_banner.py --name "The Shattered Realm" --setting "Medieval Fantasy" ...

# 3. Location thumbnails (when a world is created)
python tools/generate_location_art.py --world "Medieval Fantasy" --generate-defaults ...

# 4. Character portraits (during character creation)
python tools/generate_portrait.py --name "Kira" --archetype "Rogue" ...

# 5. Scene art (at the start of each story scene)
python tools/generate_scene_art.py --description "..." --location "Harbor District" ...
```

---

## Output Directory Structure

```
assets/
├── banners/
│   ├── presets/
│   │   ├── medieval_fantasy_*.png
│   │   ├── post_apocalyptic_*.png
│   │   └── modern_mystery_*.png
│   └── the_shattered_realm_*.png
├── portraits/
│   └── kira_*.png  (×4 options)
├── scenes/
│   └── session_001_scene_03_*.png
└── locations/
    ├── medieval_fantasy/
    │   ├── harbor_district_*.png
    │   └── ...
    └── post_apocalyptic/
        └── ...
```

---

## Model & API Notes

- **Model:** `imagen-4.0-generate-001` (Imagen 4)
- **Max images per call:** 4
- **Supported aspect ratios:** `1:1`, `3:4`, `4:3`, `16:9`, `9:16`
- **API key:** Get yours at [aistudio.google.com](https://aistudio.google.com)
- Images are billed per generation — each call to Imagen counts against your quota
