# Implementation Plan: MVP Core: AI World and Character Engine

## Phase 1: World Creation Backend [checkpoint: 7a843af]
- [x] **Task: Setup Backend Project Structure (FastAPI)** d9d498a
    - [x] Initialize FastAPI project with basic routes.
    - [x] Configure Firebase Firestore connection.
- [x] **Task: World Setup API** b5a9fd6
    - [x] Write tests for world creation (POST /api/worlds).
    - [x] Implement POST /api/worlds with validation and Firestore storage.
    - [x] Write tests for world retrieval (GET /api/worlds/:id).
    - [x] Implement GET /api/worlds/:id.
- [x] **Task: AI World Intro Generation** ff3a906
    - [x] Write tests for AI intro generation prompt and service.
    - [x] Implement Gemini-powered world intro generation.
- [x] **Task: Conductor - User Manual Verification 'World Creation Backend' (Protocol in workflow.md)** 7a843af

## Phase 2: Character Engine Backend
- [x] **Task: Character Creation API** 90a2190
    - [x] Write tests for character creation (POST /api/characters).
    - [x] Implement POST /api/characters with world-fit validation.
- [x] **Task: AI Portrait Generation Job** 75f3dc7
    - [x] Write tests for portrait generation service.
    - [x] Implement AI image generation service for character portraits.
- [~] **Task: Conductor - User Manual Verification 'Character Engine Backend' (Protocol in workflow.md)**

## Phase 3: Initial UI Scaffolding (React)
- [ ] **Task: Setup Frontend Project (React + TypeScript)**
    - [ ] Initialize React project with Tailwind CSS (if desired) or Vanilla CSS.
    - [ ] Configure basic routing.
- [ ] **Task: Create World Form**
    - [ ] Implement UI for world definition (form + validation).
    - [ ] Connect UI to Backend API.
- [ ] **Task: Character Creation UI**
    - [ ] Implement UI for character definition and portrait selection.
    - [ ] Connect UI to Backend API.
- [ ] **Task: Conductor - User Manual Verification 'Initial UI Scaffolding' (Protocol in workflow.md)**
