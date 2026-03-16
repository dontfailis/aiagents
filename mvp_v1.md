
# 📖 MVP Summary: Shared AI Storytelling RPG

This document provides a structured, detailed summary of the product concept and a concrete action plan for building a Minimum Viable Product (MVP).

---

## I. The Core Concept

### 1. Core Product Idea
The product is a web-based collaborative storytelling RPG where players create or join a shared game world and experience AI-generated narrative adventures inside it. 

**The experience combines:**
*   **LLM-generated** story progression.
*   **AI-generated** character and world imagery.
*   **Branching choices** and consequences.
*   **Persistent** world state.
*   **Multiplayer** (primarily asynchronous play).

> **The Vision:** A shared "choose-your-own-adventure" novel where multiple players contribute to the same evolving world over time.

### 2. Main Player Entry Points
*   **Create a New Game:** A player (host) starts a new shared world and defines its initial setup.
*   **Join an Ongoing Game:** A player enters an existing world using a share code and creates a character that fits that specific setting.

---

## II. Gameplay & Mechanics

### 3. Core Gameplay Loop
1.  **Character Creation:** Users define age, appearance, personality, and backstory. The system generates AI image options for the player to select their "canonical" look.
2.  **World Setup (Host Only):** Defines the era (e.g., Medieval, Sci-Fi), environment (e.g., Wasteland, Kingdom), and the core premise.
3.  **Story Session:** The AI generates a contained narrative arc (5–10 scenes). Players make choices that create branches in the narrative tree.
4.  **World Update:** At the end of a session, the world state is updated. Future players see and react to these changes.

### 4. Asynchronous Multiplayer
To avoid the technical complexity of real-time coordination, the game uses an **asynchronous model**:
*   Players do not need to be online simultaneously.
*   The world state updates between sessions.
*   Returning players receive a **"While You Were Away"** summary of other players' actions.

### 5. World Consistency
The system maintains a "World Bible" (Facts, Factions, Tensions, and History) that is passed to the AI to ensure narrative continuity and prevent contradictions.

---

## III. MVP Definition & Scope

**Goal:** Prove that players can co-create a world and influence each other's experience through persistent, AI-driven storytelling.

### MVP Feature Set
*   **Landing Page:** Create/Join game functionality.
*   **Character Engine:** Form-based creation with AI portrait generation.
*   **Story Engine:** Branching narrative with 2–4 choices per scene.
*   **Persistence:** A JSON-backed world state tracking locations and tensions.
*   **Recap System:** A timeline log of major events and a session summary for returning players.
*   **Map Model:** 5–8 named locations to ground the story.

---

## IV. System Design (Technical)

### 1. Data Objects
*   `World`: Metadata, setting, era, and the "Current State" summary.
*   `Character`: Stats, backstory, portrait URL, and current location.
*   `Session`: A snapshot of the world state at the start, choices made, and the resulting changes.
*   `Event`: A log entry of "Who, What, Where" for the World Chronicle.

### 2. AI Implementation
*   **LLM:** Used for narrative generation, summarization, and extracting structured JSON data for state updates.
*   **Image Gen:** Used primarily for character portraits and key location concept art.

### 3. State Update Logic
After a session, the AI outputs a JSON object:
```json
{
  "location": "Harbor District",
  "tension_change": "+2",
  "faction_impact": "Merchant Guild angered",
  "new_hook": "Guild retaliation imminent"
}
````