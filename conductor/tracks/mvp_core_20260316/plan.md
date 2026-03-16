# Implementation Plan: MVP Core: AI World and Character Engine

## Phase 1: World Creation Backend
- [ ] **Task: Setup Backend Project Structure (FastAPI)**
    - [ ] Initialize FastAPI project with basic routes.
    - [ ] Configure Firebase Firestore connection.
- [ ] **Task: World Setup API**
    - [ ] Write tests for world creation (POST /api/worlds).
    - [ ] Implement POST /api/worlds with validation and Firestore storage.
    - [ ] Write tests for world retrieval (GET /api/worlds/:id).
    - [ ] Implement GET /api/worlds/:id.
- [ ] **Task: AI World Intro Generation**
    - [ ] Write tests for AI intro generation prompt and service.
    - [ ] Implement Gemini-powered world intro generation.
- [ ] **Task: Conductor - User Manual Verification 'World Creation Backend' (Protocol in workflow.md)**

## Phase 2: Character Engine Backend
- [ ] **Task: Character Creation API**
    - [ ] Write tests for character creation (POST /api/characters).
    - [ ] Implement POST /api/characters with world-fit validation.
- [ ] **Task: AI Portrait Generation Job**
    - [ ] Write tests for portrait generation service.
    - [ ] Implement AI image generation service for character portraits.
- [ ] **Task: Conductor - User Manual Verification 'Character Engine Backend' (Protocol in workflow.md)**

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
