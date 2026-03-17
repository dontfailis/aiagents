import {
  ArrowLeft,
  ArrowRight,
  Castle,
  Compass,
  Flame,
  LoaderCircle,
  PenSquare,
  Search,
  Sparkles,
  Sword,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { createWorld, generateWorldPreview, getWorldSettingPreviews } from '../lib/api';
import {
  CUSTOM_WORLD_SETTING_ID,
  WORLD_SETTINGS,
  WORLD_TONES,
  cardStyle,
  getSettingById,
  getToneById,
  suggestWorldDetails,
} from '../lib/storyContent';

const WORLD_STEP_LABELS = ['Setting', 'Tone', 'Details'];

const TONE_ICONS = {
  Adventure: Sword,
  Exploration: Compass,
  Intrigue: Search,
  Survival: Flame,
};

const SETTING_ICONS = {
  'medieval-fantasy': Castle,
  'post-apocalyptic': Flame,
  'modern-mystery': Search,
  [CUSTOM_WORLD_SETTING_ID]: PenSquare,
};

export default function CreateWorldForm() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [settingId, setSettingId] = useState(WORLD_SETTINGS[0].id);
  const [toneId, setToneId] = useState(WORLD_TONES[0].id);
  const [detailSeed, setDetailSeed] = useState(0);
  const [era, setEra] = useState(getSettingById(WORLD_SETTINGS[0].id).era);
  const [name, setName] = useState('');
  const [environment, setEnvironment] = useState('');
  const [description, setDescription] = useState('');
  const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null);
  const [presetImageMap, setPresetImageMap] = useState<Record<string, string>>({});
  const [previewLoading, setPreviewLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [craftStage, setCraftStage] = useState(0);
  const [createdWorld, setCreatedWorld] = useState<{
    id: string;
    name: string;
    intro: string;
    share_code: string;
    banner_url?: string;
  } | null>(null);

  useEffect(() => {
    const suggestion = suggestWorldDetails(settingId, toneId, detailSeed);
    const selectedSetting = getSettingById(settingId);

    setEra(selectedSetting.era);
    setName(suggestion.name);
    setEnvironment(suggestion.environment);
    setDescription(suggestion.description);
    setError(null);
  }, [detailSeed, settingId, toneId]);

  useEffect(() => {
    async function loadPresetImages() {
      try {
        const response = await getWorldSettingPreviews();
        const nextImages = response.presets.reduce<Record<string, string>>((accumulator, preset) => {
          if (preset.image_url) {
            accumulator[preset.setting_id] = preset.image_url;
          }
          return accumulator;
        }, {});
        setPresetImageMap(nextImages);
      } catch {
        setPresetImageMap({});
      }
    }

    void loadPresetImages();
  }, []);

  useEffect(() => {
    if (settingId === CUSTOM_WORLD_SETTING_ID) {
      return;
    }

    const presetImage = presetImageMap[settingId];
    if (presetImage && !previewImageUrl) {
      setPreviewImageUrl(presetImage);
    }
  }, [presetImageMap, previewImageUrl, settingId]);

  useEffect(() => {
    if (!loading) {
      setCraftStage(0);
      return;
    }

    const intervalId = window.setInterval(() => {
      setCraftStage((current) => (current + 1) % 3);
    }, 1100);

    return () => window.clearInterval(intervalId);
  }, [loading]);

  async function handleGeneratePreview() {
    setPreviewLoading(true);
    setError(null);

    try {
      const response = await generateWorldPreview({
        setting_id: settingId === CUSTOM_WORLD_SETTING_ID ? undefined : settingId,
        name,
        era,
        environment,
        tone: getToneById(toneId).label,
        description,
      });

      if (response.image_url) {
        setPreviewImageUrl(response.image_url);
      }

      if (!response.image_url && response.error) {
        setError(response.error);
      }
    } catch (previewError) {
      setError(previewError instanceof Error ? previewError.message : 'Failed to generate world preview.');
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleFinalizeWorld() {
    setLoading(true);
    setError(null);

    try {
      const selectedTone = getToneById(toneId);
      const world = await createWorld({
        name,
        era,
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
          {createdWorld.banner_url && (
            <div className="world-created-banner">
              <img src={createdWorld.banner_url} alt={createdWorld.name} />
            </div>
          )}
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
  const selectedTone = getToneById(toneId);
  const craftStages = [
    `Forging the laws of ${name || 'your realm'}`,
    `Layering intrigue into ${environment || 'the frontier'}`,
    `Opening the first chapter of the chronicle`,
  ];

  return (
    <main className={step === 2 ? 'world-flow-shell world-flow-shell-olive' : 'world-flow-shell'}>
      {loading && (
        <div className="creation-ritual">
          <div className="creation-ritual-backdrop" />
          <div className="creation-ritual-panel">
            <p className="section-eyebrow">Forging the Realm</p>
            <h2>{craftStages[craftStage]}</h2>
            <p>
              We are shaping the world, sealing its tone, and preparing the first invitation into{' '}
              <strong>{name || 'your story world'}</strong>.
            </p>
            <div className="creation-ritual-progress">
              <span className={craftStage >= 0 ? 'active' : ''}>Setting</span>
              <span className={craftStage >= 1 ? 'active' : ''}>Conflict</span>
              <span className={craftStage >= 2 ? 'active' : ''}>Welcome</span>
            </div>
            {previewImageUrl && (
              <div className="creation-ritual-portrait">
                <img src={previewImageUrl} alt={name || 'World preview'} />
              </div>
            )}
          </div>
        </div>
      )}
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
              <p>Select a visual starting point, or choose Custom Setting and define the genre yourself.</p>
            </section>

            <div className="world-setting-grid">
              {WORLD_SETTINGS.map((setting) => {
                const SettingIcon =
                  SETTING_ICONS[setting.id as keyof typeof SETTING_ICONS] ?? PenSquare;
                const settingImageUrl = presetImageMap[setting.id];

                return (
                  <button
                    type="button"
                    key={setting.id}
                    className={settingId === setting.id ? 'setting-card selected' : 'setting-card'}
                    style={cardStyle(setting.cardArt, setting.accent)}
                    onClick={() => {
                      setSettingId(setting.id);
                      setPreviewImageUrl(presetImageMap[setting.id] ?? null);
                    }}
                  >
                    <div className="setting-card-media">
                      {settingImageUrl ? (
                        <img src={settingImageUrl} alt={setting.label} />
                      ) : (
                        <div className="setting-card-media-placeholder" />
                      )}
                    </div>
                    <div className="setting-card-body">
                      <span className="setting-card-icon">
                        <SettingIcon size={28} color={setting.iconTone} />
                      </span>
                      <h3>{setting.label}</h3>
                      <p>{setting.description}</p>
                    </div>
                  </button>
                );
              })}
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
              <p>Step 3 of 3: Details</p>
              <div className="world-archetype-bar">
                <div className="world-archetype-bar-fill" />
              </div>
              <h2>Refine the World and Generate a Preview</h2>
              <p>
                Keep the preset as a starting point or rewrite it completely before you finalize the world.
              </p>
            </header>

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
                  <span>World Style</span>
                  <input
                    className="input-shell"
                    value={era}
                    onChange={(event) => setEra(event.target.value)}
                  />
                </label>

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

                <label className="field-group">
                  <span>Story Tone</span>
                  <input className="input-shell" value={selectedTone.label} readOnly />
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

              <section className="generated-preview-card">
                <div className="generated-preview-header">
                  <div>
                    <p className="section-eyebrow">Visual Idea</p>
                    <h3>World preview</h3>
                  </div>
                  <button
                    type="button"
                    className="compact-generate-button"
                    onClick={() => void handleGeneratePreview()}
                    disabled={previewLoading || !name.trim() || !era.trim() || !environment.trim()}
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
                </div>

                <div className="generated-preview-media">
                  {previewImageUrl ? (
                    <img src={previewImageUrl} alt={`${name || 'World'} preview`} />
                  ) : (
                    <div className="generated-preview-empty">
                      <strong>{selectedSetting.label}</strong>
                      <span>Generate a scene image from the world description when you are ready.</span>
                    </div>
                  )}
                </div>

                <div className="world-preview-banner">
                  <div>
                    <strong>{era || selectedSetting.label}</strong>
                    <span>{selectedTone.label}</span>
                  </div>
                  <p>{environment || selectedSetting.environmentPool.join(' • ')}</p>
                </div>
              </section>
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
              disabled={loading || !name.trim() || !era.trim() || !environment.trim() || !description.trim()}
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
