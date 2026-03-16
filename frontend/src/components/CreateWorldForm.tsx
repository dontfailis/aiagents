import { ArrowLeft, ArrowRight, Castle, Compass, Flame, Search, Sparkles, Sword } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { createWorld } from '../lib/api';
import {
  WORLD_SETTINGS,
  WORLD_TONES,
  cardStyle,
  getSettingById,
  getToneById,
  suggestWorldDetails,
} from '../lib/storyContent';

const WORLD_STEP_LABELS = ['Setting', 'Tone', 'Archetype'];

const TONE_ICONS = {
  Adventure: Sword,
  Exploration: Compass,
  Intrigue: Search,
  Survival: Flame,
};

export default function CreateWorldForm() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [settingId, setSettingId] = useState(WORLD_SETTINGS[0].id);
  const [toneId, setToneId] = useState(WORLD_TONES[0].id);
  const [detailSeed, setDetailSeed] = useState(0);
  const [name, setName] = useState('');
  const [environment, setEnvironment] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdWorld, setCreatedWorld] = useState<{
    id: string;
    name: string;
    intro: string;
    share_code: string;
  } | null>(null);

  useEffect(() => {
    const suggestion = suggestWorldDetails(settingId, toneId, detailSeed);
    setName(suggestion.name);
    setEnvironment(suggestion.environment);
    setDescription(suggestion.description);
  }, [detailSeed, settingId, toneId]);

  async function handleFinalizeWorld() {
    setLoading(true);
    setError(null);

    try {
      const selectedSetting = getSettingById(settingId);
      const selectedTone = getToneById(toneId);
      const world = await createWorld({
        name,
        era: selectedSetting.era,
        environment,
        tone: selectedTone.label,
        description,
      });
      setCreatedWorld(world);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Failed to create world.');
    } finally {
      setLoading(false);
    }
  }

  if (createdWorld) {
    return (
      <main className="world-flow-shell world-flow-shell-olive">
        <section className="world-created-card">
          <p className="section-eyebrow">World Created</p>
          <h1>{createdWorld.name}</h1>
          <p>{createdWorld.intro}</p>

          <div className="world-created-code">
            <span>Invite Code</span>
            <strong>{createdWorld.share_code}</strong>
          </div>

          <div className="world-created-actions">
            <Link to="/" className="secondary-button">
              Back home
            </Link>
            <button
              type="button"
              className="primary-button"
              onClick={() => navigate(`/create-character/${createdWorld.id}`)}
            >
              Create Character
              <ArrowRight size={16} />
            </button>
          </div>
        </section>
      </main>
    );
  }

  const selectedSetting = getSettingById(settingId);

  return (
    <main className={step === 2 ? 'world-flow-shell world-flow-shell-olive' : 'world-flow-shell'}>
      <div className="flow-frame">
        <header className="flow-header center">
          <Link to="/" className="inline-back-link subtle">
            <ArrowLeft size={16} />
            Back
          </Link>
          <h1>Create Your World</h1>
          <div className="flow-progress world-progress">
            {WORLD_STEP_LABELS.map((label, index) => (
              <div key={label} className="flow-progress-step">
                <div className={index <= step ? 'flow-progress-dot active' : 'flow-progress-dot'}>
                  {index + 1}
                </div>
                <span className={index === step ? 'active' : ''}>{label}</span>
              </div>
            ))}
          </div>
        </header>

        {step === 0 && (
          <>
            <section className="flow-intro">
              <h2>Choose a Setting</h2>
              <p>Select the foundation for your world. You can reshape the details at the end.</p>
            </section>

            <div className="world-setting-grid">
              {WORLD_SETTINGS.map((setting) => (
                <button
                  type="button"
                  key={setting.id}
                  className={settingId === setting.id ? 'setting-card selected' : 'setting-card'}
                  style={cardStyle(setting.cardArt, setting.accent)}
                  onClick={() => setSettingId(setting.id)}
                >
                  <div className="setting-card-media" />
                  <div className="setting-card-body">
                    <span className="setting-card-icon">
                      <Castle size={28} color={setting.iconTone} />
                    </span>
                    <h3>{setting.label}</h3>
                    <p>{setting.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </>
        )}

        {step === 1 && (
          <>
            <section className="flow-intro">
              <h2>Choose the Story Tone</h2>
              <p>Pick the energy that should define the chronicle’s first chapters.</p>
            </section>

            <div className="tone-grid">
              {WORLD_TONES.map((tone) => {
                const ToneIcon = TONE_ICONS[tone.label as keyof typeof TONE_ICONS] ?? Sparkles;

                return (
                  <button
                    type="button"
                    key={tone.id}
                    className={toneId === tone.id ? 'tone-card selected' : 'tone-card'}
                    style={cardStyle(tone.cardArt, tone.accent)}
                    onClick={() => setToneId(tone.id)}
                  >
                    <span className="tone-card-icon">
                      <ToneIcon size={24} />
                    </span>
                    <h3>{tone.label}</h3>
                    <p>{tone.shortDescription}</p>
                  </button>
                );
              })}
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <header className="world-archetype-header">
              <div className="brand-chip">
                <Sparkles size={16} />
                NarrativeForge
              </div>
              <p>Step 3 of 3: Archetype</p>
              <div className="world-archetype-bar">
                <div className="world-archetype-bar-fill" />
              </div>
              <h2>Story Archetype Selection</h2>
              <p>
                Select the dominant narrative shape for <strong>{name}</strong>, then refine the
                generated details below before you finalize.
              </p>
            </header>

            <div className="world-archetype-grid">
              {WORLD_TONES.map((tone) => {
                const ToneIcon = TONE_ICONS[tone.label as keyof typeof TONE_ICONS] ?? Sparkles;

                return (
                  <button
                    type="button"
                    key={tone.id}
                    className={toneId === tone.id ? 'archetype-card selected' : 'archetype-card'}
                    style={cardStyle(tone.cardArt, tone.accent)}
                    onClick={() => setToneId(tone.id)}
                  >
                    <div className="archetype-card-overlay" />
                    <div className="archetype-card-content">
                      <ToneIcon size={28} />
                      <h3>{tone.label}</h3>
                      <p>{tone.shortDescription}</p>
                    </div>
                  </button>
                );
              })}
            </div>

            <section className="world-details-panel">
              <div className="world-details-heading">
                <div>
                  <p className="section-eyebrow">Refine Details</p>
                  <h3>Make the world yours</h3>
                </div>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => setDetailSeed((value) => value + 1)}
                >
                  Regenerate suggestions
                </button>
              </div>

              <div className="details-grid">
                <label className="field-group">
                  <span>World Name</span>
                  <input
                    className="input-shell"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                  />
                </label>

                <label className="field-group">
                  <span>Region Focus</span>
                  <input
                    className="input-shell"
                    value={environment}
                    onChange={(event) => setEnvironment(event.target.value)}
                  />
                </label>
              </div>

              <label className="field-group">
                <span>Chronicle Intro</span>
                <textarea
                  className="input-shell textarea-shell"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  rows={4}
                />
              </label>

              <div className="world-preview-banner">
                <div>
                  <strong>{selectedSetting.label}</strong>
                  <span>{getToneById(toneId).label}</span>
                </div>
                <p>{selectedSetting.environmentPool.join(' • ')}</p>
              </div>
            </section>
          </>
        )}

        {error && <p className="error-banner">{error}</p>}

        <footer className="flow-footer">
          <button
            type="button"
            className="inline-back-link muted"
            onClick={() => (step > 0 ? setStep((current) => current - 1) : navigate('/'))}
          >
            <ArrowLeft size={16} />
            Back
          </button>

          {step < 2 ? (
            <button type="button" className="primary-button" onClick={() => setStep((current) => current + 1)}>
              Continue
              <ArrowRight size={16} />
            </button>
          ) : (
            <button
              type="button"
              className="primary-button world-finalize-button"
              onClick={() => void handleFinalizeWorld()}
              disabled={loading || !name.trim() || !environment.trim() || !description.trim()}
            >
              {loading ? 'Finalizing...' : 'Finalize World'}
              {!loading && <ArrowRight size={16} />}
            </button>
          )}
        </footer>
      </div>
    </main>
  );
}
