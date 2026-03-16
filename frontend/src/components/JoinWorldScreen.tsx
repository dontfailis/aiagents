import { ArrowLeft, ArrowRight, Castle, MapPin, ScrollText } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { joinWorldByCode } from '../lib/api';
import type { FormEvent } from 'react';
import type { JoinWorldResponse } from '../lib/types';

export default function JoinWorldScreen() {
  const navigate = useNavigate();
  const [shareCode, setShareCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<JoinWorldResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await joinWorldByCode(shareCode.trim().toUpperCase());
      setResult(response);
    } catch (submitError) {
      setResult(null);
      setError(submitError instanceof Error ? submitError.message : 'Unable to join this world.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="join-shell">
      <div className="page-topbar">
        <Link to="/" className="inline-back-link">
          <ArrowLeft size={16} />
          Back home
        </Link>
      </div>

      <section className="join-panel">
        <header className="join-header">
          <p className="section-eyebrow">Join World</p>
          <h1>Enter your invite code or paste a link.</h1>
          <p>
            Share codes drop you directly into a living world with its tone, setting, and recent
            events already in motion.
          </p>
        </header>

        <form className="join-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={shareCode}
            onChange={(event) => setShareCode(event.target.value.toUpperCase())}
            placeholder="8-character invite code"
            className="input-shell join-input"
            maxLength={32}
          />
          <button type="submit" className="primary-button" disabled={loading || !shareCode.trim()}>
            {loading ? 'Joining...' : 'Join'}
            {!loading && <ArrowRight size={16} />}
          </button>
        </form>

        {error && <p className="error-banner">{error}</p>}

        {result && (
          <article className="join-summary-card">
            <div className="join-summary-heading">
              <div>
                <div className="join-summary-meta">
                  <Castle size={16} />
                  <span>{result.world.era}</span>
                  <span className="summary-dot" />
                  <span>{result.world.tone}</span>
                </div>
                <h2>{result.world.name}</h2>
                <p>{result.world.description || result.world.intro}</p>
              </div>
              <div className="join-code-chip">Code {result.world.share_code}</div>
            </div>

            <div className="join-summary-region">
              <MapPin size={16} />
              <span>{result.world.environment}</span>
            </div>

            <div className="join-recent-events">
              <h3>
                <ScrollText size={18} />
                Recent events
              </h3>
              {result.recent_events.length > 0 ? (
                <ul>
                  {result.recent_events.map((entry) => (
                    <li key={entry.id}>
                      <strong>{entry.character_name}</strong> {entry.excerpt}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>The chronicle is still quiet. Your choices may be the first to leave a mark.</p>
              )}
            </div>

            <button
              type="button"
              className="primary-button"
              onClick={() => navigate(`/create-character/${result.world.id}`)}
            >
              Continue
              <ArrowRight size={16} />
            </button>
          </article>
        )}
      </section>
    </main>
  );
}
