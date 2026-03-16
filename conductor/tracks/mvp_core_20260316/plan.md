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

## Phase 2: Character Engine Backend [checkpoint: b95f050]
- [x] **Task: Character Creation API** 90a2190
    - [x] Write tests for character creation (POST /api/characters).
    - [x] Implement POST /api/characters with world-fit validation.
- [x] **Task: AI Portrait Generation Job** 75f3dc7
    - [x] Write tests for portrait generation service.
    - [x] Implement AI image generation service for character portraits.
- [x] **Task: Conductor - User Manual Verification 'Character Engine Backend' (Protocol in workflow.md)** b95f050

## Phase 3: Initial UI Scaffolding (React) [checkpoint: 317652e]
- [x] **Task: Setup Frontend Project (React + TypeScript)** 62db42e
    - [x] Initialize React project with Tailwind CSS (if desired) or Vanilla CSS.
    - [x] Configure basic routing.
- [x] **Task: Create World Form** 938406c
    - [x] Implement UI for world definition (form + validation).
    - [x] Connect UI to Backend API.
- [x] **Task: Character Creation UI** 972b58e
    - [x] Implement UI for character definition and portrait selection.
    - [x] Connect UI to Backend API.
- [x] **Task: Conductor - User Manual Verification 'Initial UI Scaffolding' (Protocol in workflow.md)** 317652e
