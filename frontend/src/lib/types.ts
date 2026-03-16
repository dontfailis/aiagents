export interface World {
  id: string;
  name: string;
  era: string;
  environment: string;
  tone: string;
  description?: string | null;
  intro: string;
  share_code: string;
  banner_url?: string;
  created_at: string;
}

export interface Character {
  id: string;
  world_id: string;
  name: string;
  age: number;
  archetype: string;
  backstory: string;
  visual_description: string;
  portrait_url: string;
  portrait_urls?: string[];
  fit_reasoning: string;
  created_at: string;
}

export interface StoryChoice {
  id: number;
  text: string;
}

export interface StoryScene {
  scene_number: number;
  narrative: string;
  choices: StoryChoice[];
  image_url?: string;
}

export interface SessionHistoryEntry {
  scene_number: number;
  narrative: string;
  choice: string;
}

export interface Session {
  id: string;
  character_id: string;
  world_id: string;
  status: 'in_progress' | 'completed';
  current_scene: StoryScene;
  history: SessionHistoryEntry[];
  summary?: string;
  created_at: string;
  updated_at?: string;
}

export type ChronicleImpact = 'local' | 'regional' | 'global';

export interface ChronicleEntry {
  id: string;
  session_id: string;
  session_label: string;
  when_label: string;
  character_name: string;
  location: string;
  excerpt: string;
  impact: ChronicleImpact;
  footer: string;
}

export interface JoinWorldResponse {
  world: World;
  recent_events: ChronicleEntry[];
}
