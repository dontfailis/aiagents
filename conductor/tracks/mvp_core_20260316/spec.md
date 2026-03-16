# Specification: MVP Core: AI World and Character Engine

## 1. Overview
- **Track ID**: `mvp_core_20260316`
- **Objective**: Implement the foundational AI-driven world and character creation systems.
- **Scope**:
    - Backend API for world creation.
    - AI-generated world introduction.
    - Backend API for character creation and world-fit validation.
    - AI-generated character portrait options.

## 2. Requirements & Acceptance Criteria
- [ ] **R1: World Setup**
    - [ ] Create world with name, era, environment, tone, and description.
    - [ ] Generate unique share code.
    - [ ] Store initial world state (JSON).
- [ ] **R2: World Intro Generation**
    - [ ] Use AI (Gemini) to generate a rich narrative introduction for the world.
- [ ] **R3: Character Creation**
    - [ ] Create character with name, age, archetype, and backstory.
    - [ ] Validate character fit against the world settings (lore/rules).
- [ ] **R4: Portrait Generation**
    - [ ] Generate 3-4 portrait options per character.
    - [ ] Store selected portrait URL.

## 3. Technical Constraints
- **Stack**: FastAPI (Python), React (TypeScript), Firebase Firestore.
- **AI**: Google AI (Gemini).
- **Format**: State updates must use structured JSON.

## 4. User Experience Context
- **Design**: Clean, minimal UI for world/character forms.
- **Flow**: Home -> Create World -> Share Code -> Character Creation -> Ready to Play.
