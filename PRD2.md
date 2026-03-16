# Product Requirements Document (PRD)

## Shared AI Storytelling RPG — MVP

**Document Version:** 1.0
**Date:** March 16, 2026
**Status:** Draft
**Author:** Product Team

---

## 1. Product Overview

### 1.1 Product Statement

A web application where friends co-create and play asynchronous AI-generated story adventures in a shared, evolving world.

### 1.2 Vision

Players create or join collaborative storytelling worlds where every decision matters. An AI narrator drives branching story sessions, generates character portraits, and maintains a persistent world that evolves with every player's actions. The result is a living, shared choose-your-own-adventure novel — authored collectively by players and AI.

### 1.3 Target Users

Friends and communities who enjoy tabletop RPGs, interactive fiction, collaborative storytelling, and AI-assisted creative play. Users who want the depth of a tabletop RPG without the scheduling burden of synchronous sessions.

---

## 2. Problem Statement

Tabletop RPGs and collaborative storytelling games require all players to be online simultaneously, a dedicated Game Master, and significant preparation time. Most groups struggle to maintain consistent sessions. Existing AI chatbot experiences are single-player and lack persistence — each conversation is isolated and disposable.

There is no product today that combines AI-driven narrative generation with persistent shared worlds and asynchronous multiplayer, allowing friends to contribute to the same evolving story on their own schedules.

---

## 3. Goals & Success Criteria

### 3.1 MVP Goals

1. Prove that players can create a shared world and invite others to join it.
2. Prove that AI-generated branching story sessions are engaging and coherent.
3. Prove that persistent world state creates a feeling of shared consequence across players.
4. Prove that asynchronous play feels connected — not like isolated chatbot sessions.

### 3.2 Success Metrics

| Metric | Target |
|--------|--------|
| A host can create a world and invite friends via share code | 100% functional |
| A joining player can create a character that fits the world | 100% functional |
| Each player can complete a short AI-generated story session (10–20 min) | 100% functional |
| World state persists and updates between sessions | 100% functional |
| Returning players see believable consequences from previous sessions | Validated via playtesting with 2–3 players over 5–10 sessions |
| Players report the experience feels like a shared story, not isolated chatbot interactions | Qualitative feedback from playtest cohort |

---

## 4. User Flows

### 4.1 Flow A — Create a New Game

1. Player lands on the homepage.
2. Player selects **Create New Game**.
3. Player defines the world:
   - Game / world name
   - Era or timeline (medieval, post-apocalyptic, futuristic, modern, etc.)
   - Environment / setting (city, wilderness, kingdom, wasteland, space colony, etc.)
   - Story tone / theme (adventure, exploration, mystery, survival, intrigue, horror)
   - Optional short world description (free text)
4. System generates the world and produces a **share code / invite link**.
5. Player proceeds to **Character Creation** (see 4.3).
6. Player begins their first **Story Session** (see 4.4).

### 4.2 Flow B — Join an Existing Game

1. Player lands on the homepage.
2. Player selects **Join Existing Game**.
3. Player enters the **share code** or follows an invite link.
4. Player reads a **World Summary** (setting, tone, recent events).
5. System validates the player's entry and routes them to **Character Creation** (see 4.3).

### 4.3 Character Creation

1. Player provides character details:
   - Name
   - Age
   - Archetype / role (from a curated list: rogue, scholar, warrior, survivor, merchant, wanderer, etc.)
   - Short backstory (free text)
   - Visual description / style cues
2. The system validates that the character fits the established world rules (e.g., no futuristic characters in a medieval setting unless the world permits it).
3. The system generates **3–4 AI character portrait options**.
4. Player selects the portrait that best represents their character.
5. Character is saved and becomes the player's canonical identity in that world.

### 4.4 Story Session

1. Session opens with an **intro summary**: current world context, character location, and any "while you were away" recap.
2. The AI generates **5–10 story scenes** sequentially.
3. Each scene presents **2–4 choices** for the player.
4. Player choices influence the narrative direction, creating branches.
5. Session concludes with an **end-of-session summary**: what happened, what changed, and consequences.
6. Target session duration: **10–20 minutes** of active play.

### 4.5 Returning Player Flow

1. Player logs in and selects their world.
2. System presents a **"While You Were Away"** recap:
   - What changed since their last session
   - Which characters caused the changes
   - New tensions, opportunities, or story hooks
3. Player begins a new Story Session from the updated world state.

---

## 5. Feature Requirements

### 5.1 Landing Page

- Two primary actions: **Create New Game** and **Join Existing Game**.
- Clean, minimal UI that communicates the core concept.

### 5.2 World Creation

- Form-based setup: name, era, environment, tone/theme, optional description.
- AI generates a world introduction narrative from the inputs.
- System creates and stores the initial **World State** document.
- Produces a shareable invite code / link.

**Supported world types (MVP):**

- Medieval Fantasy
- Post-Apocalyptic
- Modern Mystery

**Supported story tones (MVP):**

- Adventure
- Exploration
- Intrigue
- Survival

### 5.3 Character Creation & Portrait Generation

- Structured input form (name, age, archetype, backstory, visual cues).
- World-fit validation: system constrains character options to match the world's rules.
- AI image generation produces 3–4 portrait options per character.
- Selected portrait becomes the canonical character visual.

**Supported archetypes (MVP):** Rogue, Scholar, Warrior, Survivor, Merchant, Wanderer.

### 5.4 Story Session Engine

- Generates a bounded, self-contained story arc per session.
- 5–10 scenes per session, each with 2–4 branching choices.
- Narrative is consistent with the world state, character identity, and tone.
- Sessions have a clear beginning, middle, and resolution.
- Player choices are recorded and mapped to world-state consequences.

### 5.5 Persistent World State

After each session, the system:

- Extracts structured world changes (JSON format).
- Updates the master World State document.
- Records key events with location, impact scope, and story hooks.
- Saves both human-readable story text and machine-readable state changes.

### 5.6 "While You Were Away" Summaries

- Generated automatically for returning players.
- Summarizes changes caused by other players since the last session.
- Highlights new tensions, opportunities, and unresolved plot threads.

### 5.7 World History / Chronicle

- A timeline or log of all major world events.
- Records which player/character caused each event.
- Serves as a continuity reference for players and the AI system.

### 5.8 World Map / Region Model

- Simple named-location model (5–8 places per world).
- Each event is attached to a specific location.
- Enables geographic context for consequences and interaction.

**Example locations:** North City, Old Forest, Harbor District, Desert Pass, Mountain Keep, River Settlement, Borderlands, Market Square.

---

## 6. Interaction Model

### 6.1 Asynchronous Multiplayer (MVP)

- Players do **not** need to be online simultaneously.
- Each player takes turns / sessions in the same world independently.
- The world state updates between sessions.
- Players influence each other **indirectly** through shared world consequences.

### 6.2 Interaction Scope Levels

| Level | Scope | Example |
|-------|-------|---------|
| **Local** | Affects a single location | A tavern burns down in Harbor District |
| **Regional** | Affects nearby areas | Trade routes near the Harbor become dangerous |
| **Global** | Affects the entire world | A plague spreads; a king dies; war begins |

### 6.3 Deferred Features (Not in MVP)

- Real-time multiplayer / live co-play
- Direct character-to-character scene encounters
- Live chat between players
- Simultaneous scene handling

---

## 7. AI System Design

### 7.1 AI Generation Jobs

The AI workload is split into discrete, specialized jobs:

| Job | Description | Output |
|-----|-------------|--------|
| **World Intro Generation** | Produces the narrative introduction for a newly created world | Rich text narrative |
| **Character Portrait Generation** | Creates visual portraits based on character descriptions | 3–4 image options |
| **Session Narrative Generation** | Drives the story scene-by-scene during a play session | Scenes with choices |
| **Session Summary Generation** | Produces the end-of-session recap | Human-readable summary |
| **World Update Generation** | Extracts and applies structured changes to the world state | JSON state delta |
| **"While You Were Away" Generation** | Summarizes inter-session changes for returning players | Contextual recap |

### 7.2 Prompt Templates Required

- World creation prompt
- Character creation / validation prompt
- Scene generation prompt (with world context injection)
- Choice generation prompt
- End-of-session state update prompt (structured JSON output)
- "While you were away" summary prompt

### 7.3 AI Guardrails

- A **World Bible** summary document is always injected into generation context to prevent lore contradictions.
- State updates require **structured JSON output** from the LLM, not free-form text.
- Character creation is **constrained** to world-compatible options.
- Narrative tone and setting rules are enforced through system prompts.

---

## 8. Data Model

### 8.1 Core Data Objects

**Game / World**

| Field | Type | Description |
|-------|------|-------------|
| world_id | UUID | Unique identifier |
| world_name | String | Display name |
| host_player_id | UUID | Creator's player ID |
| setting_type | Enum | Medieval, Post-Apocalyptic, Modern Mystery |
| era | String | Timeline description |
| tone_themes | Array[String] | Selected story tones |
| regions | Array[Region] | Named locations (5–8) |
| world_rules | Text | Constraints and lore rules |
| current_state_summary | Text | Human-readable world status |
| structured_state | JSON | Machine-readable world state |
| share_code | String | Invite code |
| created_at | Timestamp | Creation date |

**Character**

| Field | Type | Description |
|-------|------|-------------|
| character_id | UUID | Unique identifier |
| player_id | UUID | Owning player |
| world_id | UUID | Associated world |
| name | String | Character name |
| age | Integer | Character age |
| archetype | Enum | Role / class |
| backstory | Text | Player-written backstory |
| portrait_url | String | Selected AI portrait |
| current_location | String | Current region |
| status | Enum | Active, Resting, Incapacitated |

**Session**

| Field | Type | Description |
|-------|------|-------------|
| session_id | UUID | Unique identifier |
| character_id | UUID | Playing character |
| world_id | UUID | Associated world |
| start_state_snapshot | JSON | World state at session start |
| scenes | Array[Scene] | Generated scenes |
| player_choices | Array[Choice] | Recorded decisions |
| session_outcome | Text | Narrative summary |
| end_state_changes | JSON | Structured state delta |
| created_at | Timestamp | Session timestamp |

**World Event**

| Field | Type | Description |
|-------|------|-------------|
| event_id | UUID | Unique identifier |
| world_id | UUID | Associated world |
| source_character_id | UUID | Causing character |
| location | String | Affected region |
| summary | Text | What happened |
| impact_scope | Enum | Local, Regional, Global |
| new_hooks | Array[String] | Story threads created |
| order_index | Integer | Chronological position |
| created_at | Timestamp | Event timestamp |

### 8.2 State Update Model

After every completed session, the system:

1. Generates a **structured session summary** via AI.
2. Extracts world changes in **JSON format**.
3. Updates the master **World State** document.
4. Saves a **player-facing narrative summary**.
5. Surfaces updates to future players via the "While You Were Away" system.

**Example state change payload:**

```json
{
  "location": "Harbor District",
  "tension_delta": +2,
  "faction_changes": [
    { "faction": "Merchant Guild", "status": "angered" }
  ],
  "rumors_added": [
    "A masked traveler stole a relic from the Guild vault"
  ],
  "story_hooks_unlocked": [
    "Guild retaliation is imminent"
  ],
  "global_impact": false
}
```

---

## 9. Technical Architecture

### 9.1 Backend APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/worlds` | POST | Create a new world |
| `/api/worlds/:code/join` | POST | Join a world via share code |
| `/api/worlds/:id` | GET | Fetch world state and summary |
| `/api/worlds/:id/events` | GET | Fetch world event history |
| `/api/worlds/:id/updates` | GET | Fetch "while you were away" summary |
| `/api/characters` | POST | Create a new character |
| `/api/characters/:id/portraits` | POST | Generate portrait options |
| `/api/sessions` | POST | Start a new story session |
| `/api/sessions/:id/choices` | POST | Submit a player choice |
| `/api/sessions/:id/complete` | POST | Complete session & trigger world update |

### 9.2 Storage Requirements

- **Worlds**: Full world definitions, state snapshots, and structured state.
- **Players**: Authentication and profile data.
- **Characters**: Character sheets and portrait references.
- **Sessions**: Full session logs with scenes, choices, and outcomes.
- **World Events**: Chronological event log with impact metadata.
- **State Versions**: Snapshots or versioning of world state for traceability.

### 9.3 AI Integration

- **LLM Provider**: Google AI (Gemini) via Agents framework.
- **Image Generation**: AI image generation service for character portraits.
- **Structured Output**: LLM responses for state updates must return valid JSON.
- **Context Management**: World Bible document injected into every generation call.

### 9.4 MVP Technical Priorities

1. **Text-first functionality** before visual polish.
2. **Image generation is optional** if it risks slowing development.
3. **One strong story engine for one genre first**, rather than many weak ones.
4. **Optimize for world consistency** over maximum player freedom.
5. Limit the number of simultaneously moving parts.

---

## 10. Frontend Screens

### 10.1 Screen Inventory

| Screen | Purpose |
|--------|---------|
| **Landing Page** | Entry point: Create or Join a game |
| **Create World** | Form to define world settings |
| **Join World** | Enter share code, view world summary |
| **Character Creation** | Define character attributes |
| **Portrait Selection** | Choose from AI-generated portrait options |
| **Story Play** | Main session screen: read scenes, make choices |
| **End-of-Session Summary** | Recap of session outcomes and world changes |
| **World Chronicle** | Timeline / log of major world events |
| **"While You Were Away"** | Returning player recap screen |

### 10.2 Design Principles

- The **Story Play** screen should read like an interactive novel — clean typography, minimal UI chrome.
- Visual cards for: character identity, world context, recent events, and available choices.
- Current world context displayed at the beginning of each session.
- Consequences shown clearly after each session ends.

---

## 11. Scope Boundaries

### 11.1 In Scope (MVP)

- Create world with structured setup
- Join world with share code
- Character creation with AI portrait generation
- One shared world state per game
- 5–8 named locations per world
- Short branching story sessions (5–10 scenes, 10–20 min)
- Persistent world updates after each session
- Session recap and end-of-session summary
- "While you were away" updates for returning players
- World history / chronicle log
- Indirect player interaction through world consequences

### 11.2 Out of Scope (Future Versions)

- Real-time multiplayer / live co-play
- Free movement on a complex interactive map
- Combat systems
- Inventory systems
- Voice interactions
- Direct player-to-player scene encounters
- Deep NPC simulation
- Complex faction AI
- "Cone of interaction" proximity system (deferred to v2)

---

## 12. Risk Register

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| 1 | **World consistency** — AI contradicts earlier established facts | High | Structured World Bible always injected into context; JSON state updates validated before commit |
| 2 | **Character compatibility** — Players create characters that break the world | Medium | World-fit validation during character creation; constrained archetype list |
| 3 | **Cross-player disconnection** — Players don't feel connected without real-time play | High | Strong "While You Were Away" summaries; visible world consequences; shared chronicle |
| 4 | **Scope explosion** — Fully simulated living world is too complex for MVP | High | Strict MVP boundary: bounded sessions, indirect interaction only, limited world types |
| 5 | **Narrative coherence** — Branching stories become incoherent over time | Medium | Sessions are bounded with clear arcs; structured consequences written back to state |
| 6 | **AI generation latency** — Slow response times degrade the play experience | Medium | Optimize prompt sizes; pre-generate where possible; async generation jobs |
| 7 | **Portrait generation quality** — AI images don't match player expectations | Low | Offer 3–4 options; allow re-generation; make portraits optional in MVP |

---

## 13. Design Principles

1. **Keep sessions bounded.** Each session should be short, complete, and satisfying.
2. **Prefer asynchronous multiplayer.** Avoid real-time complexity in version one.
3. **Use structured world state.** Never rely solely on narrative text for persistence.
4. **Make player impact visible.** Every session should visibly change the world.
5. **Constrain creativity inside the chosen world.** Freedom exists within scenario rules.
6. **Focus on indirect interaction first.** Players affect each other through consequences, not live co-play.

---

## 14. Testing & Validation Plan

### 14.1 Testing Phases

| Phase | Description |
|-------|-------------|
| **Phase 1** | Single-player testing within the shared-world framework |
| **Phase 2** | 2–3 players testing asynchronously in the same world |
| **Phase 3** | Validate over 5–10 consecutive sessions for consistency |

### 14.2 Validation Questions

- Can players understand what changed between sessions?
- Can players identify who caused world changes?
- Do players understand their available options in each scene?
- Does the world feel consistent after 5–10 sessions?
- Do players feel connected to each other despite asynchronous play?
- Do sessions feel like chapters of a shared story, not isolated chatbot conversations?

---

## 15. Future Roadmap (Post-MVP)

| Phase | Features |
|-------|----------|
| **v1.1** | Additional world types and tones; improved portrait generation; player profiles |
| **v1.2** | Geographic proximity-based interaction ("cone of influence"); richer map model |
| **v2.0** | Real-time multiplayer scenes; direct character encounters; live co-play |
| **v2.1** | Inventory and item systems; combat mechanics; NPC depth |
| **v3.0** | Voice narration; complex faction AI; community-created world templates |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **World** | A shared game setting created by a host player, defined by era, environment, and tone |
| **Session** | A single bounded play experience (5–10 scenes, 10–20 minutes) |
| **World State** | The structured data document describing the current state of the world |
| **World Bible** | A summary document injected into AI context to maintain lore consistency |
| **Share Code** | A unique code or link used to invite players to join a world |
| **Story Hook** | An unresolved plot thread that future sessions can pick up |
| **Impact Scope** | The geographic reach of a world event: Local, Regional, or Global |

---

## Appendix B: Example Session Flow

**World:** "The Shattered Realm" — Medieval Fantasy, Adventure tone
**Player:** Kira, a Rogue, currently in Harbor District

1. **Session opens** — "While you were away: A merchant caravan was ambushed on the road to North City. Tensions between the Merchant Guild and the Borderlands raiders have escalated."
2. **Scene 1** — Kira hears rumors at the dockside tavern. Choices: investigate the ambush site, seek out the Guild leader, or ignore it and pursue a personal lead.
3. **Scene 2–8** — Story unfolds based on choices, with escalating stakes and branching paths.
4. **Scene 9** — Climactic moment: Kira discovers the raids were orchestrated by a Guild insider.
5. **Session summary** — "Kira exposed a conspiracy within the Merchant Guild. The Guild is now fractured. Harbor District stability has decreased. A new story hook has emerged: the insider has fled to the Desert Pass."
6. **World update** — Harbor District tension +3, Merchant Guild status changed to "fractured", new rumor and story hook committed to world state.
7. **Next player** sees these consequences when they log in.
