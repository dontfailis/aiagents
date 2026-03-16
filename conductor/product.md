# Product Definition: Shared AI Storytelling RPG — MVP

## 1. Overview
- **Product Name**: Shared AI Storytelling RPG
- **Target Release**: MVP v1.0
- **Status**: Draft (Initial Scaffolding)
- **Problem Statement**: Tabletop RPGs require synchronous play and significant preparation. Existing AI chatbots lack shared persistence. This product enables asynchronous, collaborative storytelling in a persistent, AI-driven world.

## 2. Objective & Goals
- **Goal**: Create a web application where friends can co-create and play asynchronous AI-generated story adventures in a shared, evolving world.
- **Success Criteria**:
    - Host can create a world and invite friends via share code.
    - Players can create world-compatible characters with AI portraits.
    - AI-generated branching sessions (10-20 min) are engaging and persistent.
    - Returning players see consequences of others' actions.

## 3. Target Audience
- **Primary Audience**: Friends/communities who enjoy tabletop RPGs, interactive fiction, and AI-assisted creative play but struggle with scheduling synchronous sessions.

## 4. Key Use Cases & Requirements
- **Create a New Game**: Host defines world name, era, environment, tone, and description. System generates a share code.
- **Join a Game**: Player enters share code, views world summary, and joins.
- **Character Creation**: Player defines name, age, archetype (Rogue, Scholar, Warrior, Survivor, Merchant, Wanderer), and backstory. AI generates portrait options.
- **Story Session**: AI-driven 5-10 scenes with 2-4 branching choices each.
- **World Persistence**: AI extracts structured changes after each session and updates the master world state.
- **"While You Were Away"**: Returning players get a summary of changes caused by others since their last session.

## 5. Technical Considerations
- **AI Integration**: Google AI (Gemini) for narrative generation, session summaries, and state updates. AI image generation for portraits.
- **Data Model**: Structured JSON for world state and "World Bible" lore consistency.
- **API Endpoints**: RESTful API for world/character management and session execution.

## 6. MVP Scope Boundaries
- **In-Scope**: Structured world/character creation, persistent state updates, asynchronous sessions, world chronicle log.
- **Out-of-Scope**: Real-time multiplayer, direct character-to-character encounters, complex inventory systems, voice narration.
