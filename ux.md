# UX Design Document

## Shared AI Storytelling RPG — MVP

**Companion to:** PRD2.md
**Purpose:** Defines how screens look, feel, and behave. PRD2.md covers *what* to build; this covers *how it should be experienced*.

---

## Core UX Principles

| Principle | How |
|-----------|-----|
| **Always a suggestion** | AI pre-fills names, descriptions, and backstories — never an empty field |
| **Editable everywhere** | Every AI suggestion has an inline edit + regenerate (↻) button |
| **Visual first** | Card pickers for all categorical choices — no dropdowns |
| **Progressive reveal** | Each step unlocks the next — no overwhelming single-page forms |
| **Low commitment** | Players can go back and change any step before confirming |

---

## Image Generation

> **TODO:** Confirm which image generation tools are available and update this section.
> Candidate tools: Vertex AI Imagen, DALL-E, Stability AI, Midjourney API.

Image generation is used in two places:

1. **Character Portrait Generation** — 3–4 portrait options per character, based on archetype, visual cues, and world setting.
2. **World Art / Atmosphere** (optional, post-MVP) — header imagery for each world's landing and session screens.

### Portrait Generation Flow

- Triggered after character details are confirmed.
- System composes a prompt from: archetype + visual description cues + world setting + tone.
- Returns 3–4 options displayed as selectable cards.
- Player picks one; selection is saved as the canonical portrait.
- "Regenerate" button available if no option fits.
- Portrait generation runs **asynchronously** — player sees a loading state while images generate.

---

## Screen-by-Screen UX

---

### 1. Landing Page

Two large, visually distinct CTAs — nothing else.

```
┌─────────────────────────────────────────────┐
│                                             │
│         [World background art / mood]       │
│                                             │
│   ┌─────────────────┐  ┌─────────────────┐  │
│   │  Create New     │  │  Join Existing  │  │
│   │     Game        │  │      Game       │  │
│   └─────────────────┘  └─────────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
```

---

### 2. World Creation — 3-Step Flow

#### Step 1 — Setting (pick one)

Visual cards with icon, name, and one-line description.

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  🏰          │  │  ☢️           │  │  🔍          │
│              │  │              │  │              │
│   Medieval   │  │   Post-Apo   │  │   Modern     │
│   Fantasy    │  │   calyptic   │  │   Mystery    │
│              │  │              │  │              │
│ Swords, magic│  │ Ruin, survival│ │ Secrets, city│
└──────────────┘  └──────────────┘  └──────────────┘
```

#### Step 2 — Story Tone (pick 1–2)

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  ⚔️       │  │  🧭      │  │  🕵️      │  │  🔥      │
│ Adventure │  │Exploration│  │ Intrigue │  │ Survival │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

#### Step 3 — Name & Description

AI generates a world name and 2-sentence intro based on selections. Both are editable inline.

```
World Name:    [ The Shattered Realm              ↻ ]
Description:   [ A kingdom fractured by civil war,   ]
               [ where old loyalties are tested...↻  ]

                              [ Create World → ]
```

On confirm: world is created, share code is generated, player proceeds to Character Creation.

---

### 3. Join World

Simple, focused screen.

```
Enter your invite code or paste a link:

[ ___________________________ ]   [ Join → ]

─────────────────────────────────────────
World Summary (shown after valid code):

  🏰 The Shattered Realm
  Medieval Fantasy · Adventure · Intrigue

  "A kingdom fractured by civil war..."

  Recent events:
  • A merchant caravan was ambushed near North City
  • The Harbor Guild is fracturing

                              [ Continue → ]
```

---

### 4. Character Creation — 3-Step Flow

#### Step 1 — Archetype (pick one)

Cards show icon, archetype name, and a short role description.

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  🗡️           │  │  📚          │  │  🛡️           │
│    Rogue     │  │   Scholar    │  │   Warrior    │
│ Quick, sly,  │  │ Wise, cunning│  │ Bold, loyal, │
│  deceptive   │  │  observant   │  │   fearless   │
└──────────────┘  └──────────────┘  └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  🌿          │  │  💰          │  │  🌍          │
│  Survivor   │  │   Merchant   │  │   Wanderer   │
│ Gritty, wary │  │ Shrewd, con- │  │ Free, rest-  │
│  resourceful │  │  nected, rich│  │  less, wise  │
└──────────────┘  └──────────────┘  └──────────────┘
```

#### Step 2 — Character Details

All fields are AI-suggested from the archetype + world. All are editable.

```
Name:       [ Kira Ashveil                    ↻ ]

Age:        Young ──●─────────── Veteran
            (slider with 3 anchor labels)

Backstory:  [ Once a guild thief cast out for     ]
            [ knowing too much, Kira now trades   ]
            [ secrets for coin in harbor alleys.↻ ]

Looks:      [scarred] [cloaked] [dark-haired] [+add]
            (removable tag chips; player can type custom cues)
```

#### Step 3 — Portrait Selection

Displayed after async generation completes.

```
Choose your portrait:

┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│        │  │        │  │        │  │        │
│  [1]   │  │  [2]   │  │  [3]   │  │  [4]   │
│        │  │        │  │        │  │        │
└────────┘  └────────┘  └────────┘  └────────┘

                                  [ ↻ Regenerate ]

                              [ Confirm Character → ]
```

---

### 5. Story Play Screen

The main session experience. Reads like an interactive novel — minimal UI chrome.

```
┌─────────────────────────────────────────────────────┐
│  🏰 The Shattered Realm  ·  Harbor District          │
│  Kira Ashveil · Rogue                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Scene 3 of 8                                       │
│                                                     │
│  The dockside tavern is thick with smoke and        │
│  whispered arguments. A hooded figure catches       │
│  your eye — the same crest as the Guild vault       │
│  on their ring.                                     │
│                                                     │
│  What do you do?                                    │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  A) Approach and introduce yourself         │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │  B) Follow them when they leave             │   │
│  └─────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────┐   │
│  │  C) Ask the barkeep who they are            │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

- One scene at a time — no scrolling back during play.
- Choices are large tap targets.
- World context (location, character) always visible in the header.
- Scene counter shown to give players a sense of progress.

---

### 6. End-of-Session Summary

```
┌─────────────────────────────────────────────────────┐
│  Session Complete                                   │
│                                                     │
│  What happened:                                     │
│  Kira exposed a conspiracy within the Merchant      │
│  Guild. The Guild is now fractured.                 │
│                                                     │
│  World changes:                                     │
│  📍 Harbor District    Tension ↑ +3                 │
│  🏛️ Merchant Guild     Status → Fractured           │
│  🗺️ Desert Pass        New story hook unlocked      │
│                                                     │
│  New story hook:                                    │
│  "The Guild insider has fled to the Desert Pass."   │
│                                                     │
│  ┌─────────────────────┐  ┌──────────────────────┐  │
│  │   View Chronicle    │  │   Return to World    │  │
│  └─────────────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

### 7. "While You Were Away"

Shown to returning players before starting a new session.

```
┌─────────────────────────────────────────────────────┐
│  Welcome back, Kira.                                │
│  Here's what changed since your last visit:        │
│                                                     │
│  📍 North City                                      │
│     A trade delegation arrived from the capital.   │
│     Caused by: Aldric (Merchant) — 2 days ago      │
│                                                     │
│  📍 Harbor District                                 │
│     The Guild hall was locked and guarded.          │
│     Caused by: World event — ongoing                │
│                                                     │
│  New tensions:                                      │
│  • The Guild wants retribution                      │
│  • A stranger is asking about you by name           │
│                                                     │
│                          [ Begin Your Session → ]   │
└─────────────────────────────────────────────────────┘
```

---

### 8. World Chronicle

A scrollable timeline of all major events, newest first.

```
  [Filter: All · Local · Regional · Global]

  ● Session 7 — Kira Ashveil · Harbor District
    "Guild insider exposed. Merchant Guild fractured."
    Impact: Regional  ·  3 story hooks created

  ● Session 6 — Aldric · North City
    "Trade delegation brokered ceasefire with Borderlands."
    Impact: Global

  ● Session 4 — Mira · Old Forest
    "Ancient shrine discovered. Rumors of old magic spreading."
    Impact: Local
```

---

## Interaction States

| State | Behavior |
|-------|----------|
| **Loading / generating** | Skeleton placeholders; spinner on portrait generation |
| **AI suggestion available** | Field pre-filled, ↻ button visible |
| **User edited** | Field shows edited state; ↻ still available to revert |
| **Step locked** | Greyed out until prior step is completed |
| **Session in progress** | No navigation away; choices are the only interaction |

---

## Typography & Visual Tone

- **Story Play screen:** Large serif or literary font for scene text. Immersive, novel-like.
- **UI chrome:** Clean sans-serif. Minimal. Stays out of the way of the story.
- **Color palette:** Tied to world setting (warm/earthy for Medieval, desaturated/grey for Post-Apo, cool/neon for Modern Mystery) — applied as a theme per world.
- **Card selection:** Clear selected vs. unselected state (border highlight, slight scale, background tint).
