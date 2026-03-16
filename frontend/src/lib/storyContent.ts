import type { CSSProperties } from 'react';
import type { ChronicleImpact, World } from './types';

export interface WorldSettingOption {
  id: string;
  era: string;
  label: string;
  description: string;
  accent: string;
  iconTone: string;
  cardArt: string;
  environmentPool: string[];
  namePool: string[];
  descriptionPool: string[];
}

export interface ToneOption {
  id: string;
  label: string;
  shortDescription: string;
  accent: string;
  cardArt: string;
}

export interface ArchetypeOption {
  id: string;
  label: string;
  description: string;
  accent: string;
  cardArt: string;
}

export const WORLD_SETTINGS: WorldSettingOption[] = [
  {
    id: 'medieval-fantasy',
    era: 'Medieval Fantasy',
    label: 'Medieval Fantasy',
    description: 'Swords, magic, ancient kingdoms, and mythical beasts roaming untamed lands.',
    accent: '#d7a438',
    iconTone: '#f7cb6d',
    cardArt:
      'radial-gradient(circle at 50% 12%, rgba(196, 221, 255, 0.48), transparent 26%), linear-gradient(180deg, rgba(122, 156, 190, 0.92) 0%, rgba(42, 56, 82, 0.76) 45%, rgba(30, 39, 58, 0.96) 100%)',
    environmentPool: ['Harbor District', 'Ashen Keep', 'Whispering Vale'],
    namePool: ['Aethelard', 'The Shattered Realm', 'Vesperhold'],
    descriptionPool: [
      'An old kingdom is splintering at the seams while guilds, nobles, and forgotten magic each fight to decide what comes next.',
      'Storms gather over a realm of hidden covenants, where every port and keep carries a secret oath of its own.',
      'The realm balances on the edge of renewal and ruin, with power shifting from courts to dockside knives and temple relics.',
    ],
  },
  {
    id: 'post-apocalyptic',
    era: 'Post-Apocalyptic',
    label: 'Post-Apocalyptic',
    description: 'Ruin, survival, scarcity, and dangerous scavengers in a collapsed society.',
    accent: '#13b57c',
    iconTone: '#57e5ae',
    cardArt:
      'radial-gradient(circle at 50% 18%, rgba(234, 238, 245, 0.24), transparent 20%), linear-gradient(180deg, rgba(126, 132, 145, 0.72) 0%, rgba(56, 62, 76, 0.82) 42%, rgba(31, 36, 47, 0.98) 100%)',
    environmentPool: ['Glasswater Ruins', 'Black Ridge', 'Dustline Market'],
    namePool: ['Afterglass', 'The Hollow Grid', 'Ruinwake'],
    descriptionPool: [
      'Civilization survives in hard fragments, and every convoy, water source, and rumor of power is worth bleeding for.',
      'Years after the fall, scattered enclaves barter memory for safety while scavengers map the bones of the old world.',
      'The world is held together by signal fires and improvised treaties, and each new alliance can collapse by dawn.',
    ],
  },
  {
    id: 'modern-mystery',
    era: 'Modern Mystery',
    label: 'Modern Mystery',
    description: 'Secrets, urban shadows, hidden conspiracies, and investigative tension.',
    accent: '#6051d4',
    iconTone: '#8b7cff',
    cardArt:
      'radial-gradient(circle at 50% 12%, rgba(220, 234, 255, 0.22), transparent 20%), linear-gradient(180deg, rgba(90, 101, 121, 0.64) 0%, rgba(45, 54, 77, 0.82) 40%, rgba(23, 28, 42, 0.98) 100%)',
    environmentPool: ['North City', 'Crown Street', 'The Flood Tunnels'],
    namePool: ['Noctis Vale', 'The Veiled City', 'Greywatch'],
    descriptionPool: [
      'A modern city hums with quiet corruption, where missing persons, sealed archives, and old societies all point to the same hidden hand.',
      'Streetlights, surveillance, and old money conceal a deeper network of secrets that only the reckless ever glimpse.',
      'Each district looks ordinary in daylight, but every alley and office tower conceals one more thread in a widening conspiracy.',
    ],
  },
];

export const WORLD_TONES: ToneOption[] = [
  {
    id: 'Adventure',
    label: 'Adventure',
    shortDescription: 'Heroic momentum, daring choices, and a world inviting action.',
    accent: '#f2d040',
    cardArt:
      'linear-gradient(135deg, rgba(242, 208, 64, 0.25) 0%, rgba(15, 23, 42, 0.25) 100%), rgba(18, 27, 45, 0.9)',
  },
  {
    id: 'Exploration',
    label: 'Exploration',
    shortDescription: 'Unmapped ground, forgotten places, and discovery around every turn.',
    accent: '#4bc0a8',
    cardArt:
      'linear-gradient(135deg, rgba(75, 192, 168, 0.22) 0%, rgba(15, 23, 42, 0.18) 100%), rgba(18, 27, 45, 0.9)',
  },
  {
    id: 'Intrigue',
    label: 'Intrigue',
    shortDescription: 'Power plays, secrets, leverage, and unstable alliances.',
    accent: '#7195ff',
    cardArt:
      'linear-gradient(135deg, rgba(113, 149, 255, 0.24) 0%, rgba(15, 23, 42, 0.15) 100%), rgba(18, 27, 45, 0.9)',
  },
  {
    id: 'Survival',
    label: 'Survival',
    shortDescription: 'Hard choices, scarce resources, and a constant test of resolve.',
    accent: '#ff8c4c',
    cardArt:
      'linear-gradient(135deg, rgba(255, 140, 76, 0.22) 0%, rgba(15, 23, 42, 0.12) 100%), rgba(18, 27, 45, 0.9)',
  },
];

export const CHARACTER_ARCHETYPES: ArchetypeOption[] = [
  {
    id: 'Rogue',
    label: 'Rogue',
    description: 'Quick, sly, and always one step ahead when a door is locked or a truth is buried.',
    accent: '#d9b24f',
    cardArt:
      'linear-gradient(180deg, rgba(12, 18, 28, 0.18) 0%, rgba(12, 18, 28, 0.9) 100%), radial-gradient(circle at 50% 20%, rgba(217, 178, 79, 0.32), transparent 34%)',
  },
  {
    id: 'Scholar',
    label: 'Scholar',
    description: 'Observant, curious, and driven to decode the lore others overlook.',
    accent: '#8ea5ff',
    cardArt:
      'linear-gradient(180deg, rgba(16, 24, 39, 0.18) 0%, rgba(16, 24, 39, 0.9) 100%), radial-gradient(circle at 40% 20%, rgba(142, 165, 255, 0.3), transparent 36%)',
  },
  {
    id: 'Warrior',
    label: 'Warrior',
    description: 'Bold, disciplined, and built to stand in the path of danger.',
    accent: '#df7b55',
    cardArt:
      'linear-gradient(180deg, rgba(20, 16, 17, 0.18) 0%, rgba(20, 16, 17, 0.9) 100%), radial-gradient(circle at 42% 20%, rgba(223, 123, 85, 0.32), transparent 36%)',
  },
  {
    id: 'Survivor',
    label: 'Survivor',
    description: 'Wary, resourceful, and practiced at making the impossible livable.',
    accent: '#5fb88a',
    cardArt:
      'linear-gradient(180deg, rgba(14, 18, 14, 0.18) 0%, rgba(14, 18, 14, 0.9) 100%), radial-gradient(circle at 42% 20%, rgba(95, 184, 138, 0.3), transparent 36%)',
  },
  {
    id: 'Merchant',
    label: 'Merchant',
    description: 'Connected, persuasive, and never far from a favor, ledger, or debt.',
    accent: '#d2a04c',
    cardArt:
      'linear-gradient(180deg, rgba(19, 16, 9, 0.18) 0%, rgba(19, 16, 9, 0.9) 100%), radial-gradient(circle at 42% 20%, rgba(210, 160, 76, 0.3), transparent 36%)',
  },
  {
    id: 'Wanderer',
    label: 'Wanderer',
    description: 'Restless, experienced, and shaped by roads others are afraid to follow.',
    accent: '#6dbdc6',
    cardArt:
      'linear-gradient(180deg, rgba(10, 18, 20, 0.18) 0%, rgba(10, 18, 20, 0.9) 100%), radial-gradient(circle at 42% 20%, rgba(109, 189, 198, 0.3), transparent 36%)',
  },
];

const LOOKS_BY_ARCHETYPE: Record<string, string[]> = {
  Rogue: ['scarred', 'cloaked', 'dark-haired'],
  Scholar: ['ink-stained', 'watchful', 'well-kept'],
  Warrior: ['broad-shouldered', 'battle-worn', 'steady gaze'],
  Survivor: ['weathered', 'layered leathers', 'quick-eyed'],
  Merchant: ['tailored', 'signet ring', 'measured smile'],
  Wanderer: ['travel-worn', 'windburned', 'dusty cloak'],
};

const BACKSTORIES_BY_ARCHETYPE: Record<string, string[]> = {
  Rogue: [
    'Once a guild thief cast out for knowing too much, this drifter now trades secrets for coin in the tightest corners of the city.',
    'Raised between dockside alleys and noble blind spots, this operator learned that leverage matters more than loyalty.',
    'A former courier for dangerous people, now free only in the sense that no single faction owns the debt outright.',
  ],
  Scholar: [
    'After finding a fragment of forbidden lore, this researcher learned that knowledge draws danger faster than any blade.',
    'An archivist turned field investigator, driven by the certainty that history has been edited by powerful hands.',
    'Once sheltered in study halls, now forced into the world after discovering the one text nobody wanted translated.',
  ],
  Warrior: [
    'Forged by border skirmishes and old oaths, this fighter knows how fragile peace becomes when leaders grow desperate.',
    'A veteran with too many names for too many battlefields, still trying to decide which cause is worth the next scar.',
    'Born to serve a banner that no longer deserves it, now walking a thin line between duty and conscience.',
  ],
  Survivor: [
    'The world taught caution early, and every hard season sharpened an instinct for finding shelter where others see ruin.',
    'A scavenger, tracker, and witness to collapse, moving because staying still has rarely meant safety.',
    'After losing one home too many, this survivor now trusts practical skill more than promises.',
  ],
  Merchant: [
    'Raised in counting houses and contested deals, this negotiator understands that commerce and power are usually the same thing.',
    'Every favor extended has a price, and this merchant has built a life by remembering who owes what when the room goes quiet.',
    'A traveler between courts, caravans, and guildhalls, carrying news faster than most armies.',
  ],
  Wanderer: [
    'No border ever held for long, and each road left behind a lesson, an enemy, or a map nobody else has seen.',
    'This wayfarer learned to read people and weather with equal care, because both can turn lethal without warning.',
    'A restless soul with a knack for appearing where stories break open and vanish again before blame arrives.',
  ],
};

export const AGE_MARKS = [
  { label: 'Young', value: 19 },
  { label: 'Adult', value: 27 },
  { label: 'Veteran', value: 42 },
];

export function getSettingById(settingId: string) {
  return WORLD_SETTINGS.find((setting) => setting.id === settingId) ?? WORLD_SETTINGS[0];
}

export function getToneById(toneId: string) {
  return WORLD_TONES.find((tone) => tone.id === toneId) ?? WORLD_TONES[0];
}

export function getArchetypeById(archetypeId: string) {
  return (
    CHARACTER_ARCHETYPES.find((archetype) => archetype.id === archetypeId) ??
    CHARACTER_ARCHETYPES[0]
  );
}

export function suggestWorldDetails(settingId: string, toneId: string, seed = 0) {
  const setting = getSettingById(settingId);
  const tone = getToneById(toneId);
  const name = setting.namePool[seed % setting.namePool.length];
  const environment = setting.environmentPool[seed % setting.environmentPool.length];
  const baseDescription = setting.descriptionPool[seed % setting.descriptionPool.length];

  return {
    name,
    environment,
    description: `${baseDescription} The dominant pulse of the story is ${tone.label.toLowerCase()}, so every rumor, alliance, and expedition threatens to shift the balance.`,
  };
}

export function suggestCharacterDetails(
  archetypeId: string,
  world: Pick<World, 'era' | 'environment' | 'tone' | 'name'>,
  seed = 0,
) {
  const archetype = getArchetypeById(archetypeId);
  const looks = LOOKS_BY_ARCHETYPE[archetype.id] ?? ['distinctive', 'composed', 'travel-ready'];
  const backstories = BACKSTORIES_BY_ARCHETYPE[archetype.id] ?? BACKSTORIES_BY_ARCHETYPE.Rogue;
  const selectedBackstory = backstories[seed % backstories.length];
  const toneClause = `In ${world.name}, every move around ${world.environment} is colored by ${world.tone.toLowerCase()} tensions.`;
  const fantasyNames = ['Kira Ashveil', 'Aldric Fen', 'Mira Voss'];
  const wastelandNames = ['Nyx Calder', 'Rook Mercer', 'Tamsin Vale'];
  const mysteryNames = ['Iris Vale', 'Jonah Kreel', 'Maren Cross'];
  const pool =
    world.era === 'Post-Apocalyptic'
      ? wastelandNames
      : world.era === 'Modern Mystery'
        ? mysteryNames
        : fantasyNames;

  return {
    name: pool[seed % pool.length],
    ageIndex: 1,
    backstory: `${selectedBackstory} ${toneClause}`,
    looks,
  };
}

export function ageFromIndex(index: number) {
  return AGE_MARKS[index]?.value ?? AGE_MARKS[1].value;
}

export function indexFromAge(age: number) {
  if (age <= AGE_MARKS[0].value) {
    return 0;
  }

  if (age >= AGE_MARKS[2].value) {
    return 2;
  }

  return 1;
}

export function splitSummary(summary?: string) {
  if (!summary) {
    return [];
  }

  return summary
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean)
    .slice(0, 3);
}

export function getImpactLabel(impact: ChronicleImpact) {
  if (impact === 'global') {
    return 'Global Impact';
  }

  if (impact === 'regional') {
    return 'Regional Impact';
  }

  return 'Local Impact';
}

export function getThemeClassForWorld(world?: Pick<World, 'era'> | null) {
  if (!world) {
    return 'theme-medieval';
  }

  if (world.era === 'Post-Apocalyptic') {
    return 'theme-post-apo';
  }

  if (world.era === 'Modern Mystery') {
    return 'theme-modern';
  }

  return 'theme-medieval';
}

export function cardStyle(art: string, accent: string) {
  return {
    '--card-art': art,
    '--card-accent': accent,
  } as CSSProperties;
}
