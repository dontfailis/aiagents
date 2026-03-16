import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Coins,
  LoaderCircle,
  Map,
  RefreshCw,
  Shield,
  Sparkles,
  UserRound,
  VenetianMask,
  WandSparkles,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { createCharacter, createSession, generateCharacterPreview, getWorld } from '../lib/api';
import {
  AGE_MARKS,
  CHARACTER_ARCHETYPES,
  CUSTOM_ARCHETYPE_ID,
  ageFromIndex,
  cardStyle,
  getArchetypeById,
  suggestCharacterDetails,
} from '../lib/storyContent';
import type { KeyboardEvent } from 'react';
import type { Character, World } from '../lib/types';

const CHARACTER_STEP_LABELS = ['Lineage', 'Details', 'Portrait'];

const ARCHETYPE_ICONS = {
  Rogue: VenetianMask,
  Scholar: BookOpen,
  Warrior: Shield,
  Survivor: Sparkles,
  Merchant: Coins,
  Wanderer: Map,
  [CUSTOM_ARCHETYPE_ID]: WandSparkles,
};

export default function CreateCharacterForm() {
  const { worldId } = useParams();
  const navigate = useNavigate();
  const [world, setWorld] = useState<World | null>(null);
  const [step, setStep] = useState(0);
  const [archetypeId, setArchetypeId] = useState('Rogue');
  const [archetypeLabel, setArchetypeLabel] = useState(getArchetypeById('Rogue').label);
  const [detailSeed, setDetailSeed] = useState(0);
  const [name, setName] = useState('');
  const [ageIndex, setAgeIndex] = useState(1);
  const [backstory, setBackstory] = useState('');
  const [looks, setLooks] = useState<string[]>([]);
  const [lookDraft, setLookDraft] = useState('');
  const [previewPortraitUrls, setPreviewPortraitUrls] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdCharacter, setCreatedCharacter] = useState<Character | null>(null);
  const [selectedPortraitIndex, setSelectedPortraitIndex] = useState(0);

  useEffect(() => {
    async function loadWorld() {
      if (!worldId) {
        setError('Missing world context.');
        setLoading(false);
        return;
      }

      try {
        const response = await getWorld(worldId);
        setWorld(response);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Failed to load world.');
      } finally {
        setLoading(false);
      }
    }

    void loadWorld();
  }, [worldId]);

  useEffect(() => {
    if (!world) {
      return;
    }

    const suggestion = suggestCharacterDetails(archetypeId, world, detailSeed);
    setName(suggestion.name);
    setAgeIndex(suggestion.ageIndex);
    setBackstory(suggestion.backstory);
    setLooks(suggestion.looks);
    setArchetypeLabel(getArchetypeById(archetypeId).label);
    setPreviewPortraitUrls([]);
    setSelectedPortraitIndex(0);
    setCreatedCharacter(null);
    setError(null);
  }, [archetypeId, detailSeed, world]);

  function addLookCue() {
    const nextCue = lookDraft.trim().toLowerCase();

    if (!nextCue || looks.includes(nextCue)) {
      setLookDraft('');
      return;
    }

    setLooks((current) => [...current, nextCue]);
    setLookDraft('');
    setPreviewPortraitUrls([]);
    setCreatedCharacter(null);
  }

  function handleLookKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'Enter') {
      event.preventDefault();
      addLookCue();
    }
  }

  async function handleGeneratePortraits() {
    if (!worldId) {
      return;
    }

    setPreviewLoading(true);
    setError(null);

    try {
      const response = await generateCharacterPreview({
        world_id: worldId,
        name,
        archetype: archetypeLabel.trim() || getArchetypeById(archetypeId).label,
        backstory,
        visual_description: looks.join(', '),
      });

      if (response.image_urls.length) {
        setPreviewPortraitUrls(response.image_urls);
        setSelectedPortraitIndex(0);
        setCreatedCharacter(null);
        setStep(2);
      }

      if (!response.image_urls.length && response.error) {
        setError(response.error);
      }
    } catch (previewError) {
      setError(previewError instanceof Error ? previewError.message : 'Failed to generate character portraits.');
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleConfirmCharacter() {
    if (!worldId) {
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      let persistedCharacter = createdCharacter;

      if (!persistedCharacter) {
        persistedCharacter = await createCharacter({
          world_id: worldId,
          name,
          age: ageFromIndex(ageIndex),
          archetype: archetypeLabel.trim() || getArchetypeById(archetypeId).label,
          backstory,
          visual_description: looks.join(', '),
          portrait_urls: previewPortraitUrls.length ? previewPortraitUrls : undefined,
          portrait_url: previewPortraitUrls[selectedPortraitIndex],
        });
        setCreatedCharacter(persistedCharacter);
      }

      const session = await createSession({
        character_id: persistedCharacter.id,
        world_id: worldId,
      });
      navigate(`/session/${session.id}`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Failed to start session.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <main className="character-flow-shell">
        <p className="loading-copy">Loading world context...</p>
      </main>
    );
  }

  if (!world) {
    return (
      <main className="character-flow-shell">
        <p className="error-banner">{error ?? 'Unable to load this world.'}</p>
      </main>
    );
  }

  const previewPortraitUrl = previewPortraitUrls[selectedPortraitIndex] ?? previewPortraitUrls[0];

  return (
    <main className="character-flow-shell">
      <div className="character-frame">
        <nav className="character-nav">
          <Link to="/" className="brand-chip brand-chip-light">
            <Sparkles size={16} />
            NarrativeForge
          </Link>
          <div className="character-nav-links">
            <span>Dashboard</span>
            <span>Worlds</span>
            <span className="active">Characters</span>
            <span>Settings</span>
            <span className="character-avatar-dot">
              <UserRound size={14} />
            </span>
          </div>
        </nav>

        <section className="character-header">
          <h1>Character Origin Forge</h1>
          <p>
            Shape the narrative foundation of your existence inside <strong>{world.name}</strong>.
          </p>
        </section>

        <section className="character-progress">
          <div className="character-progress-topline">
            <div>
              <Sparkles size={16} />
              <span>Step {step + 1}: {CHARACTER_STEP_LABELS[step]}</span>
            </div>
            <span>{step + 1} of 3</span>
          </div>
          <div className="character-progress-bar">
            <div style={{ width: `${((step + 1) / 3) * 100}%` }} />
          </div>
          <div className="character-progress-labels">
            {CHARACTER_STEP_LABELS.map((label, index) => (
              <span key={label} className={index === step ? 'active' : ''}>
                {label}
              </span>
            ))}
          </div>
        </section>

        {step === 0 && (
          <section className="character-archetype-stage">
            <div className="flow-intro left">
              <h2>Choose an Archetype</h2>
              <p>Use a preset as a base, or pick Custom and define the role yourself in the next step.</p>
            </div>

            <div className="character-archetype-grid">
              {CHARACTER_ARCHETYPES.map((archetype) => {
                const Icon =
                  ARCHETYPE_ICONS[archetype.id as keyof typeof ARCHETYPE_ICONS] ?? WandSparkles;

                return (
                  <button
                    key={archetype.id}
                    type="button"
                    className={archetype.id === archetypeId ? 'character-archetype-card selected' : 'character-archetype-card'}
                    style={cardStyle(archetype.cardArt, archetype.accent)}
                    onClick={() => setArchetypeId(archetype.id)}
                  >
                    <div className="archetype-card-overlay" />
                    <div className="archetype-card-content">
                      <Icon size={28} />
                      <h3>{archetype.label}</h3>
                      <p>{archetype.description}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </section>
        )}

        {step === 1 && (
          <section className="character-details-layout">
            <aside className="character-preview-card">
              <div className="portrait-placeholder">
                {previewPortraitUrl ? (
                  <img src={previewPortraitUrl} alt={name || 'Character preview'} />
                ) : (
                  <span>{name.slice(0, 1) || 'U'}</span>
                )}
              </div>
              <h2>{name || 'Unnamed Character'}</h2>
              <p>{archetypeLabel || 'Custom Role'}</p>
              <div className="preview-divider" />
              <div className="origin-traits">
                <h3>Origin Traits</h3>
                <ul>
                  {looks.slice(0, 3).map((cue) => (
                    <li key={cue}>
                      <span className="origin-dot" />
                      {cue}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="preview-card-actions">
                <button
                  type="button"
                  className="compact-generate-button"
                  onClick={() => void handleGeneratePortraits()}
                  disabled={previewLoading || !name.trim() || !backstory.trim()}
                >
                  {previewLoading ? (
                    <>
                      <LoaderCircle size={14} className="spin" />
                      Generating
                    </>
                  ) : (
                    'Generate'
                  )}
                </button>
                {previewPortraitUrls.length > 0 && (
                  <span className="inline-status">{previewPortraitUrls.length} portraits ready</span>
                )}
              </div>
            </aside>

            <div className="character-details-panel">
              <div className="character-details-heading">
                <div>
                  <h2>Refine Details</h2>
                  <p>Change the role, biography, and look before you generate portraits.</p>
                </div>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => setDetailSeed((value) => value + 1)}
                >
                  Refresh suggestions
                </button>
              </div>

              <div className="details-form">
                <label className="field-group">
                  <span>Role / Archetype</span>
                  <input
                    className="input-shell"
                    value={archetypeLabel}
                    onChange={(event) => {
                      setArchetypeLabel(event.target.value);
                      setPreviewPortraitUrls([]);
                      setCreatedCharacter(null);
                    }}
                  />
                </label>

                <label className="field-group">
                  <span>Name</span>
                  <div className="input-with-action">
                    <input
                      className="input-shell"
                      value={name}
                      onChange={(event) => {
                        setName(event.target.value);
                        setPreviewPortraitUrls([]);
                        setCreatedCharacter(null);
                      }}
                    />
                    <button
                      type="button"
                      className="field-action-button"
                      onClick={() => setDetailSeed((value) => value + 1)}
                    >
                      <RefreshCw size={16} />
                    </button>
                  </div>
                </label>

                <div className="slider-group">
                  <span>Age</span>
                  <input
                    type="range"
                    min={0}
                    max={2}
                    step={1}
                    value={ageIndex}
                    onChange={(event) => {
                      setAgeIndex(Number(event.target.value));
                      setCreatedCharacter(null);
                    }}
                  />
                  <div className="slider-labels">
                    {AGE_MARKS.map((mark, index) => (
                      <span key={mark.label} className={index === ageIndex ? 'active' : ''}>
                        {mark.label}
                      </span>
                    ))}
                  </div>
                </div>

                <label className="field-group">
                  <span>Backstory</span>
                  <div className="textarea-with-action">
                    <textarea
                      className="input-shell textarea-shell"
                      value={backstory}
                      onChange={(event) => {
                        setBackstory(event.target.value);
                        setPreviewPortraitUrls([]);
                        setCreatedCharacter(null);
                      }}
                      rows={5}
                    />
                    <button
                      type="button"
                      className="field-action-button corner"
                      onClick={() => setDetailSeed((value) => value + 1)}
                    >
                      <RefreshCw size={16} />
                    </button>
                  </div>
                </label>

                <div className="field-group">
                  <span>Looks</span>
                  <div className="look-chip-row">
                    {looks.map((cue) => (
                      <button
                        type="button"
                        key={cue}
                        className="look-chip"
                        onClick={() => {
                          setLooks((current) => current.filter((item) => item !== cue));
                          setPreviewPortraitUrls([]);
                          setCreatedCharacter(null);
                        }}
                      >
                        {cue}
                        <span>&times;</span>
                      </button>
                    ))}
                    <label className="look-chip add">
                      + add cue
                      <input
                        value={lookDraft}
                        onChange={(event) => setLookDraft(event.target.value)}
                        onKeyDown={handleLookKeyDown}
                        onBlur={addLookCue}
                      />
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {step === 2 && (
          <section className="portrait-stage">
            <header className="flow-intro left">
              <h2>Choose your portrait</h2>
              <p>
                Select the image that best fits <strong>{name}</strong> before starting the session.
              </p>
            </header>

            <div className="portrait-grid">
              {previewPortraitUrls.map((portraitUrl, index) => (
                <button
                  type="button"
                  key={`${portraitUrl}-${index}`}
                  className={selectedPortraitIndex === index ? 'portrait-card selected' : 'portrait-card'}
                  onClick={() => setSelectedPortraitIndex(index)}
                >
                  <img src={portraitUrl} alt={`${name} portrait ${index + 1}`} />
                  <span>Option {index + 1}</span>
                </button>
              ))}
            </div>

            <div className="portrait-fit-reasoning">
              <p>
                Generated from the current role, backstory, and appearance notes. Go back if you want to refine the prompt and regenerate.
              </p>
            </div>
          </section>
        )}

        {error && <p className="error-banner">{error}</p>}

        <footer className="flow-footer character-footer">
          <button
            type="button"
            className="inline-back-link muted"
            onClick={() => (step > 0 ? setStep((current) => current - 1) : navigate(`/create-world`))}
          >
            <ArrowLeft size={16} />
            Back
          </button>

          {step === 0 && (
            <button type="button" className="primary-button" onClick={() => setStep(1)}>
              Continue
              <ArrowRight size={16} />
            </button>
          )}

          {step === 1 && (
            <button
              type="button"
              className="primary-button"
              onClick={() => setStep(2)}
              disabled={!previewPortraitUrls.length}
            >
              Review Portraits
              <ArrowRight size={16} />
            </button>
          )}

          {step === 2 && (
            <button
              type="button"
              className="primary-button"
              onClick={() => void handleConfirmCharacter()}
              disabled={submitting || !previewPortraitUrls.length}
            >
              {submitting ? 'Starting Session...' : 'Confirm Character'}
              {!submitting && <ArrowRight size={16} />}
            </button>
          )}
        </footer>
      </div>
    </main>
  );
}
