import { ArrowLeft, Castle, Clapperboard, LoaderCircle, MapPin, UserRound, Volume2, VolumeX } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { concludeSession, createSessionNarration, createSessionVideo, getCharacter, getSession, getSessionVideo, getWorld, submitChoice } from '../lib/api';
import { getThemeClassForWorld, splitSummary } from '../lib/storyContent';
import type { Character, Session, World } from '../lib/types';

const TARGET_SCENE_COUNT = 8;

export default function StorySession() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [world, setWorld] = useState<World | null>(null);
  const [character, setCharacter] = useState<Character | null>(null);
  const [loading, setLoading] = useState(true);
  const [processingChoice, setProcessingChoice] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isReadingAloud, setIsReadingAloud] = useState(false);
  const [narrationLoading, setNarrationLoading] = useState(false);
  const [narrationUrl, setNarrationUrl] = useState<string | null>(null);
  const [narrationSceneNumber, setNarrationSceneNumber] = useState<number | null>(null);
  const [videoStatus, setVideoStatus] = useState<'idle' | 'pending' | 'ready' | 'error'>('idle');
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [sceneIndex, setSceneIndex] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    async function loadSessionContext() {
      if (!sessionId) {
        setError('Missing session ID.');
        setLoading(false);
        return;
      }

      try {
        const sessionResponse = await getSession(sessionId);
        const [worldResponse, characterResponse] = await Promise.all([
          getWorld(sessionResponse.world_id),
          getCharacter(sessionResponse.character_id),
        ]);
        setSession(sessionResponse);
        setSceneIndex(0);
        setWorld(worldResponse);
        setCharacter(characterResponse);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Failed to load story session.');
      } finally {
        setLoading(false);
      }
    }

    void loadSessionContext();
  }, [sessionId]);

  useEffect(() => {
    if (session?.prefetch_status !== 'pending' || !sessionId) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void getSession(sessionId)
        .then((nextSession) => {
          setSession(nextSession);
        })
        .catch(() => {
          window.clearInterval(intervalId);
        });
    }, 1200);

    return () => window.clearInterval(intervalId);
  }, [session?.prefetch_status, sessionId]);

  useEffect(() => {
    return () => {
      audioRef.current?.pause();
      audioRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!sessionId || !session?.current_scene?.scene_number) {
      return;
    }

    const currentSceneNumber = session.current_scene.scene_number;
    if (narrationSceneNumber === currentSceneNumber && narrationUrl) {
      return;
    }

    let cancelled = false;
    setNarrationLoading(true);

    void createSessionNarration(sessionId)
      .then((narration) => {
        if (cancelled) {
          return;
        }
        setNarrationUrl(narration.audio_url);
        setNarrationSceneNumber(narration.scene_number);
      })
      .catch(() => {
        if (!cancelled) {
          setNarrationUrl(null);
          setNarrationSceneNumber(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setNarrationLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [sessionId, session?.current_scene?.scene_number, narrationSceneNumber, narrationUrl]);

  useEffect(() => {
    if (!sessionId || !session?.current_scene?.scene_number || videoStatus !== 'pending') {
      return;
    }

    const currentSceneNumber = session.current_scene.scene_number;
    const intervalId = window.setInterval(() => {
      void getSessionVideo(sessionId, currentSceneNumber)
        .then((result) => {
          if (result.status === 'ready' && result.video_url) {
            setVideoStatus('ready');
            setVideoUrl(result.video_url);
            window.clearInterval(intervalId);
          }
          if (result.status === 'error') {
            setVideoStatus('error');
            window.clearInterval(intervalId);
          }
        })
        .catch(() => {
          setVideoStatus('error');
          window.clearInterval(intervalId);
        });
    }, 5000);

    return () => window.clearInterval(intervalId);
  }, [sessionId, session?.current_scene?.scene_number, videoStatus]);

  useEffect(() => {
    setVideoStatus('idle');
    setVideoUrl(null);
  }, [session?.current_scene?.scene_number]);

  async function handleChoice(choiceId: number) {
    if (!sessionId) {
      return;
    }

    setProcessingChoice(true);
    setError(null);

    try {
      const response = await submitChoice(sessionId, choiceId);
      setSession(response);
      const nextSceneLogLength = response.scene_log?.length ?? 0;
      setSceneIndex(Math.max(nextSceneLogLength - 1, 0));
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Failed to process choice.');
    } finally {
      setProcessingChoice(false);
    }
  }

  async function handleConclude() {
    if (!sessionId) {
      return;
    }

    setProcessingChoice(true);
    setError(null);

    try {
      const response = await concludeSession(sessionId);
      setSession(response);
      const nextSceneLogLength = response.scene_log?.length ?? 0;
      setSceneIndex(Math.max(nextSceneLogLength - 1, 0));
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Failed to conclude session.');
    } finally {
      setProcessingChoice(false);
    }
  }

  async function handleCreateSceneVideo() {
    if (!sessionId || !session?.current_scene?.scene_number) {
      return;
    }

    setError(null);
    setVideoStatus('pending');

    try {
      const result = await createSessionVideo(sessionId);
      if (result.status === 'ready' && result.video_url) {
        setVideoStatus('ready');
        setVideoUrl(result.video_url);
        return;
      }
      setVideoStatus('pending');
    } catch (videoError) {
      setVideoStatus('error');
      setError(videoError instanceof Error ? videoError.message : 'Failed to generate scene video.');
    }
  }

  async function handleToggleReadAloud() {
    if (!session || !sessionId) {
      return;
    }

    if (audioRef.current && !audioRef.current.paused) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsReadingAloud(false);
      return;
    }

    setError(null);

    try {
      let audioUrl = narrationUrl;
      if (!audioUrl || narrationSceneNumber !== session.current_scene.scene_number) {
        setNarrationLoading(true);
        const narration = await createSessionNarration(sessionId);
        audioUrl = narration.audio_url;
        setNarrationUrl(narration.audio_url);
        setNarrationSceneNumber(narration.scene_number);
      }
      const audio = audioRef.current ?? new Audio();
      audioRef.current = audio;
      audio.src = audioUrl;
      audio.onended = () => setIsReadingAloud(false);
      audio.onerror = () => {
        setIsReadingAloud(false);
        setError('Narration playback failed.');
      };
      setIsReadingAloud(true);
      await audio.play();
    } catch (playbackError) {
      setIsReadingAloud(false);
      setError(playbackError instanceof Error ? playbackError.message : 'Failed to generate narration.');
    } finally {
      setNarrationLoading(false);
    }
  }

  if (loading) {
    return (
      <main className="session-shell theme-medieval">
        <p className="loading-copy">Entering the story...</p>
      </main>
    );
  }

  if (!session || !world || !character) {
    return (
      <main className="session-shell theme-medieval">
        <p className="error-banner">{error ?? 'Session not found.'}</p>
      </main>
    );
  }

  const summaryHighlights = splitSummary(session.summary);
  const warmingChoices = session.prefetch_status === 'pending';
  const sceneLog = session.scene_log && session.scene_log.length > 0 ? session.scene_log : [session.current_scene];
  const activeScene = sceneLog[Math.min(sceneIndex, sceneLog.length - 1)] ?? session.current_scene;
  const isViewingLatestScene = sceneIndex >= sceneLog.length - 1;

  if (session.status === 'completed') {
    return (
      <main className={`session-shell ${getThemeClassForWorld(world)}`}>
        <section className="session-complete-card">
          <p className="section-eyebrow">Session Complete</p>
          <h1>Adventure Concluded</h1>
          <p className="session-summary-copy">{session.summary}</p>

          {summaryHighlights.length > 0 && (
            <div className="session-world-changes">
              <h2>World changes</h2>
              <ul>
                {summaryHighlights.map((sentence) => (
                  <li key={sentence}>{sentence}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="session-complete-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={() => navigate(`/chronicle/${world.id}`)}
            >
              View Chronicle
            </button>
            <Link to="/" className="primary-button">
              Return to World
            </Link>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className={`session-shell ${getThemeClassForWorld(world)}`}>
      <header className="session-header">
        <div className="session-header-group">
          <Castle size={16} />
          <span>{world.name}</span>
          <span className="summary-dot" />
          <MapPin size={16} />
          <span>{world.environment}</span>
        </div>
        <div className="session-header-group">
          <span>{character.name}</span>
          <span className="summary-dot" />
          <span>{character.archetype}</span>
          <span className="session-avatar">
            <UserRound size={15} />
          </span>
        </div>
      </header>

      <section className="session-stage">
        {error && <p className="error-banner">{error}</p>}

        <div className="session-scene-count">
          Scene {activeScene.scene_number} of {TARGET_SCENE_COUNT}
        </div>

        <div className="session-scene-nav">
          <button
            type="button"
            className="secondary-button"
            onClick={() => setSceneIndex(0)}
            disabled={sceneIndex === 0}
          >
            Start
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => setSceneIndex((current) => Math.max(current - 1, 0))}
            disabled={sceneIndex === 0}
          >
            Previous
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => setSceneIndex((current) => Math.min(current + 1, sceneLog.length - 1))}
            disabled={sceneIndex >= sceneLog.length - 1}
          >
            Next
          </button>
          <button
            type="button"
            className="secondary-button"
            onClick={() => setSceneIndex(sceneLog.length - 1)}
            disabled={isViewingLatestScene}
          >
            Live
          </button>
        </div>

        <article className="session-story-text">
          <div className="session-story-toolbar">
            <button
              type="button"
              className="session-audio-button"
              onClick={handleToggleReadAloud}
              disabled={!isViewingLatestScene}
            >
              {narrationLoading ? <LoaderCircle size={16} className="spin" /> : isReadingAloud ? <VolumeX size={16} /> : <Volume2 size={16} />}
              <span>
                {!isViewingLatestScene
                  ? 'Narration available on live scene'
                  : narrationLoading
                    ? 'Generating narration'
                    : isReadingAloud
                      ? 'Stop narration'
                      : 'Play narration'}
              </span>
            </button>
            <button
              type="button"
              className="session-audio-button"
              onClick={() => void handleCreateSceneVideo()}
              disabled={!isViewingLatestScene}
            >
              {videoStatus === 'pending' ? <LoaderCircle size={16} className="spin" /> : <Clapperboard size={16} />}
              <span>
                {!isViewingLatestScene
                  ? 'Video available on live scene'
                  : videoStatus === 'ready'
                    ? 'Scene video ready'
                    : videoStatus === 'pending'
                      ? 'Creating scene video'
                      : 'Create scene video'}
              </span>
            </button>
          </div>
          {activeScene.image_url && (
            <div className="session-scene-image">
              <img src={activeScene.image_url} alt={`Scene ${activeScene.scene_number}`} />
            </div>
          )}
          {activeScene.narrative.split('\n').map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
          {!isViewingLatestScene && activeScene.choice_made && (
            <p className="session-history-note">Chosen path: {activeScene.choice_made}</p>
          )}
          {isViewingLatestScene && videoUrl && (
            <div className="session-scene-video">
              <video controls preload="metadata" src={videoUrl} />
            </div>
          )}
          <p className="session-story-prompt">
            {isViewingLatestScene ? 'What do you do?' : 'Viewing a recorded scene. Return to Live to continue playing.'}
          </p>
        </article>

        <div className="session-choices">
          {isViewingLatestScene && warmingChoices && (
            <div className="session-choice-loading">
              <LoaderCircle size={16} className="spin" />
              <span>Preparing the next three branches while you read...</span>
            </div>
          )}
          {activeScene.choices.map((choice, index) => (
            <button
              type="button"
              key={choice.id}
              className="session-choice-button"
              onClick={() => void handleChoice(choice.id)}
              disabled={processingChoice || !isViewingLatestScene}
            >
              <span className="session-choice-letter">
                {String.fromCharCode(65 + index)}
              </span>
              <span>
                {choice.text}
                {isViewingLatestScene && warmingChoices && !(session.prefetched_choice_ids ?? []).includes(choice.id) && (
                  <small className="session-choice-substatus">branch warming up</small>
                )}
              </span>
            </button>
          ))}
        </div>

        {isViewingLatestScene && session.current_scene.scene_number >= 5 && (
          <div className="session-conclude-panel">
            <p>The narrative is reaching a natural conclusion.</p>
            <button
              type="button"
              className="secondary-button"
              onClick={() => void handleConclude()}
              disabled={processingChoice}
            >
              {processingChoice ? 'Concluding...' : 'Bring Adventure to a Close'}
            </button>
          </div>
        )}

        <button type="button" className="session-escape-link" onClick={() => navigate(-1)}>
          <ArrowLeft size={16} />
          Leave session
        </button>
      </section>
    </main>
  );
}
