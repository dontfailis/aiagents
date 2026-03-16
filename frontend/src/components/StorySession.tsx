import { ArrowLeft, Castle, MapPin, UserRound } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { concludeSession, getCharacter, getSession, getWorld, submitChoice } from '../lib/api';
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

  async function handleChoice(choiceId: number) {
    if (!sessionId) {
      return;
    }

    setProcessingChoice(true);
    setError(null);

    try {
      const response = await submitChoice(sessionId, choiceId);
      setSession(response);
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
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Failed to conclude session.');
    } finally {
      setProcessingChoice(false);
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
          Scene {session.current_scene.scene_number} of {TARGET_SCENE_COUNT}
        </div>

        <article className="session-story-text">
          {session.current_scene.image_url && (
            <div className="session-scene-image">
              <img src={session.current_scene.image_url} alt={`Scene ${session.current_scene.scene_number}`} />
            </div>
          )}
          {session.current_scene.narrative.split('\n').map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
          <p className="session-story-prompt">What do you do?</p>
        </article>

        <div className="session-choices">
          {session.current_scene.choices.map((choice, index) => (
            <button
              type="button"
              key={choice.id}
              className="session-choice-button"
              onClick={() => void handleChoice(choice.id)}
              disabled={processingChoice}
            >
              <span className="session-choice-letter">
                {String.fromCharCode(65 + index)}
              </span>
              <span>{choice.text}</span>
            </button>
          ))}
        </div>

        {session.current_scene.scene_number >= 5 && (
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
