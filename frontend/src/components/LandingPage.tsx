import { Compass, ArrowRight, UsersRound } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <main className="landing-shell">
      <div className="landing-backdrop" />
      <div className="landing-content">
        <header className="landing-hero">
          <p className="landing-kicker">Shared AI Storytelling RPG</p>
          <h1>AETHELARD</h1>
          <p>
            Forge your legend in a living world shaped by every choice.
            <br />
            Your story awaits.
          </p>
        </header>

        <section className="landing-actions" aria-label="Primary actions">
          <Link to="/create-world" className="landing-card landing-card-primary">
            <span className="landing-card-icon">
              <Compass size={30} />
            </span>
            <h2>Create New World</h2>
            <p>Shape a new universe. Define the era, tone, and lore to begin a fresh saga.</p>
            <span className="landing-card-cta">
              Begin Creation
              <ArrowRight size={16} />
            </span>
          </Link>

          <Link to="/join" className="landing-card landing-card-secondary">
            <span className="landing-card-icon">
              <UsersRound size={30} />
            </span>
            <h2>Join Existing</h2>
            <p>Enter an invite code to step into an unfolding narrative shaped by others.</p>
            <span className="landing-card-cta">
              Enter Code
              <ArrowRight size={16} />
            </span>
          </Link>
        </section>
      </div>
    </main>
  );
}
