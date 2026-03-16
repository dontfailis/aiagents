┌─────────────────────────────────────────────────────────────────────┐
│                           Web Frontend                              │
│  - Create World                                                     │
│  - Join World                                                       │
│  - Character Creation                                               │
│  - Story Play                                                       │
│  - End-of-Session Summary                                           │
│  - World Chronicle                                                  │
│  - "While You Were Away"                                            │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API / Orchestration Layer                   │
│                    (Cloud Run or GKE Autopilot)                     │
│                                                                     │
│  Responsibilities:                                                  │
│  - Auth/session routing                                             │
│  - World/game lifecycle                                             │
│  - Character lifecycle                                              │
│  - Triggering agents                                                │
│  - MCP access control                                               │
│  - Validation + retries                                             │
└─────────────────────────────────────────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│ Vertex AI Agent  │  │ Async Task Layer     │  │ Data / State Layer   │
│ Engine / ADK     │  │ Pub/Sub + Tasks      │  │                      │
│                  │  │                      │  │ - Firestore /        │
│ - World Builder  │  │ - Session update     │  │   AlloyDB           │
│ - Character      │  │ - Chronicle build    │  │ - Cloud Storage     │
│ - Session        │  │ - Portrait gen       │  │ - BigQuery          │
│   Narrator       │  │ - Retry workflows    │  │                      │
│ - State Keeper   │  │                      │  │ Stores:             │
│ - Recap Agent    │  │                      │  │ worlds, sessions,   │
│                  │  │                      │  │ events, versions,   │
│                  │  │                      │  │ portraits           │
└──────────────────┘  └──────────────────────┘  └──────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                             MCP Layer                               │
│                                                                     │
│  1. Custom World-State MCP                                          │
│  2. Lore / Retrieval MCP                                            │
│  3. Cloud Storage MCP                                               │
│  4. BigQuery MCP                                                    │
│  5. Safety / Moderation MCP                                         │
└─────────────────────────────────────────────────────────────────────┘