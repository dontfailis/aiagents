import { ArrowLeft, Filter, Globe, Link2, MapPin, User } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getChronicle } from '../lib/api';
import { getImpactLabel } from '../lib/storyContent';
import type { ChronicleEntry } from '../lib/types';

const FILTERS = [
  { id: 'all', label: 'All Events' },
  { id: 'local', label: 'Local' },
  { id: 'regional', label: 'Regional' },
  { id: 'global', label: 'Global' },
] as const;

type ChronicleFilter = (typeof FILTERS)[number]['id'];

export default function WorldChronicle() {
  const { worldId } = useParams();
  const [entries, setEntries] = useState<ChronicleEntry[]>([]);
  const [worldName, setWorldName] = useState('');
  const [bannerUrl, setBannerUrl] = useState('');
  const [filter, setFilter] = useState<ChronicleFilter>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadChronicle() {
      if (!worldId) {
        setError('Missing world context.');
        setLoading(false);
        return;
      }

      try {
        const response = await getChronicle(worldId);
        setEntries(response.entries);
        setWorldName(response.world.name);
        setBannerUrl(response.world.banner_url ?? '');
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Unable to load chronicle.');
      } finally {
        setLoading(false);
      }
    }

    void loadChronicle();
  }, [worldId]);

  const visibleEntries =
    filter === 'all' ? entries : entries.filter((entry) => entry.impact === filter);

  return (
    <main className="chronicle-shell">
      <div className="chronicle-header-row">
        <div>
          <h1>World Chronicle</h1>
          <p>
            <Globe size={14} />
            {worldName || 'Unknown world'}
          </p>
        </div>
        <Link to="/" className="chronicle-return-link">
          <ArrowLeft size={16} />
          Return to World
        </Link>
      </div>

      {bannerUrl && (
        <div className="chronicle-banner">
          <img src={bannerUrl} alt={worldName || 'World banner'} />
        </div>
      )}

      <div className="chronicle-toolbar">
        <div className="chronicle-filters">
          {FILTERS.map((option) => (
            <button
              type="button"
              key={option.id}
              className={filter === option.id ? 'chronicle-filter active' : 'chronicle-filter'}
              onClick={() => setFilter(option.id)}
            >
              {option.label}
            </button>
          ))}
        </div>
        <div className="chronicle-sort">
          <Filter size={16} />
          Newest First
        </div>
      </div>

      {loading && <p className="chronicle-empty">Loading the chronicle...</p>}
      {error && <p className="error-banner light">{error}</p>}

      {!loading && !error && (
        <section className="chronicle-timeline">
          {visibleEntries.length > 0 ? (
            visibleEntries.map((entry, index) => (
              <article
                key={entry.id}
                className={index === 0 ? 'chronicle-entry chronicle-entry-active' : 'chronicle-entry'}
              >
                <div className="chronicle-node" />
                <div className="chronicle-card">
                  <div className="chronicle-card-header">
                    <div>
                      <div className="chronicle-session-meta">
                        <span className="chronicle-session-chip">{entry.session_label}</span>
                        <span>{entry.when_label}</span>
                      </div>
                      <h2>
                        <User size={16} />
                        {entry.character_name}
                        <span className="summary-dot" />
                        <MapPin size={16} />
                        {entry.location}
                      </h2>
                    </div>
                    <span className={`impact-chip impact-chip-${entry.impact}`}>
                      {getImpactLabel(entry.impact)}
                    </span>
                  </div>

                  <blockquote>{entry.excerpt}</blockquote>

                  <p className="chronicle-card-footer">
                    <Link2 size={16} />
                    {entry.footer}
                  </p>
                </div>
              </article>
            ))
          ) : (
            <p className="chronicle-empty">
              No events match this filter yet. The chronicle begins here.
            </p>
          )}
        </section>
      )}
    </main>
  );
}
