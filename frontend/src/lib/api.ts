import axios from 'axios';
import type {
  Character,
  CharacterPreviewResponse,
  ChronicleEntry,
  JoinWorldResponse,
  Session,
  World,
  WorldPreviewResponse,
  WorldSettingPresetResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

function getErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? fallback;
  }

  return fallback;
}

export async function createWorld(payload: {
  name: string;
  era: string;
  environment: string;
  tone: string;
  description: string;
}) {
  try {
    const response = await api.post<World>('/api/worlds', payload);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to create world.'));
  }
}

export async function getWorld(worldId: string) {
  try {
    const response = await api.get<World>(`/api/worlds/${worldId}`);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to load world.'));
  }
}

export async function joinWorldByCode(shareCode: string) {
  try {
    const response = await api.post<JoinWorldResponse>(
      `/api/worlds/${encodeURIComponent(shareCode)}/join`,
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to find a world for that code.'));
  }
}

export async function getChronicle(worldId: string) {
  try {
    const response = await api.get<{ world: World; entries: ChronicleEntry[] }>(
      `/api/worlds/${worldId}/chronicle`,
    );
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to load the world chronicle.'));
  }
}

export async function createCharacter(payload: {
  world_id: string;
  name: string;
  age: number;
  archetype: string;
  backstory: string;
  visual_description: string;
  portrait_url?: string;
  portrait_urls?: string[];
}) {
  try {
    const response = await api.post<Character>('/api/characters', payload);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to create character.'));
  }
}

export async function getWorldSettingPreviews() {
  try {
    const response = await api.get<WorldSettingPresetResponse>('/api/previews/world-settings');
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to load world setting previews.'));
  }
}

export async function generateWorldPreview(payload: {
  setting_id?: string;
  name: string;
  era: string;
  environment: string;
  tone: string;
  description: string;
}) {
  try {
    const response = await api.post<WorldPreviewResponse>('/api/previews/world', payload);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to generate world preview.'));
  }
}

export async function generateCharacterPreview(payload: {
  world_id: string;
  name: string;
  archetype: string;
  backstory: string;
  visual_description: string;
}) {
  try {
    const response = await api.post<CharacterPreviewResponse>('/api/previews/character', payload);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to generate character portraits.'));
  }
}

export async function getCharacter(characterId: string) {
  try {
    const response = await api.get<Character>(`/api/characters/${characterId}`);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to load character.'));
  }
}

export async function createSession(payload: { character_id: string; world_id: string }) {
  try {
    const response = await api.post<Session>('/api/sessions', payload);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to start a new session.'));
  }
}

export async function getSession(sessionId: string) {
  try {
    const response = await api.get<Session>(`/api/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to load story session.'));
  }
}

export async function submitChoice(sessionId: string, choiceId: number) {
  try {
    const response = await api.post<Session>(`/api/sessions/${sessionId}/choices`, {
      choice_id: choiceId,
    });
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to process choice.'));
  }
}

export async function concludeSession(sessionId: string) {
  try {
    const response = await api.post<Session>(`/api/sessions/${sessionId}/conclude`);
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error, 'Failed to conclude session.'));
  }
}
