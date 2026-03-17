import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Volume2, VolumeX } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createAethelardMusic } from '../lib/aethelardMusic';

const SLIDES = [
  { type: 'image' as const, src: '/hero-bg.jpg',               label: 'The Ancient Realm'   },
  { type: 'image' as const, src: '/slide-ember-wastes.jpg',    label: 'The Ember Wastes'    },
  { type: 'image' as const, src: '/slide-sunken-citadel.jpg',  label: 'The Sunken Citadel'  },
  { type: 'image' as const, src: '/slide-gilded-throne.jpg',   label: 'The Gilded Throne'   },
  { type: 'image' as const, src: '/slide-verdant-expanse.jpg', label: 'The Verdant Expanse' },
];

const SLIDE_MS = 5000;

export default function LandingPage() {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const [playing,  setPlaying]  = useState(false);
  const [current,  setCurrent]  = useState(0);
  const [choosing, setChoosing] = useState(false);

  // Auto-advance slides
  useEffect(() => {
    const id = setInterval(() => setCurrent(c => (c + 1) % SLIDES.length), SLIDE_MS);
    return () => clearInterval(id);
  }, []);

  function toggleAudio() {
    if (playing) {
      audioCtxRef.current?.suspend();
      setPlaying(false);
    } else {
      if (!audioCtxRef.current) {
        const ctx = new AudioContext();
        audioCtxRef.current = ctx;
        createAethelardMusic(ctx);
      } else {
        audioCtxRef.current.resume();
      }
      setPlaying(true);
    }
  }

  return (
    <main className="landing-shell">
      {/* ── Slide layers — always rendered, opacity drives crossfade ── */}
      {SLIDES.map((slide, i) => (
        <div key={i} className={`landing-slide ${i === current ? 'slide-active' : ''}`}>
          <div className="landing-slide-bg" style={{ backgroundImage: `url(${slide.src})` }} />
        </div>
      ))}

      <div className="landing-overlay" />

      {/* ── Particles ── */}
      <div className="landing-particles" aria-hidden="true">
        {Array.from({ length: 18 }).map((_, i) => (
          <span key={i} className="landing-particle" style={{ '--pi': i } as React.CSSProperties} />
        ))}
      </div>

      {/* ── Hero content ── */}
      <div className={`landing-content ${choosing ? 'content-hidden' : ''}`}>
        <p className="landing-kicker">Shared AI Storytelling RPG</p>
        <h1 className="landing-title">AETHELARD</h1>
        <p className="landing-sub">Forge your legend in a living world shaped by every choice.</p>

        <button className="landing-cta" onClick={() => setChoosing(true)}>
          Start Now <ArrowRight size={18} />
        </button>

        <p className="landing-slide-label">{SLIDES[current].label}</p>

        <div className="landing-dots" role="tablist">
          {SLIDES.map((_, i) => (
            <button
              key={i}
              role="tab"
              aria-selected={i === current}
              className={`landing-dot ${i === current ? 'dot-active' : ''}`}
              onClick={() => setCurrent(i)}
            />
          ))}
        </div>
      </div>

      {/* ── Choice panels ── */}
      <div className={`landing-choice ${choosing ? 'choice-visible' : ''}`}>
        <button className="landing-choice-back" onClick={() => setChoosing(false)}>
          ← Back
        </button>

        <Link to="/create-world" className="choice-panel choice-create">
          <div className="choice-panel-photo" style={{ backgroundImage: `url(/panel-create.jpg)` }} />
          <div className="choice-panel-overlay" />
          <div className="choice-panel-body">
            <h2>Create World</h2>
            <p>Shape a new universe from nothing.</p>
            <span className="choice-cta">Begin <ArrowRight size={15} /></span>
          </div>
        </Link>

        <Link to="/join" className="choice-panel choice-join">
          <div className="choice-panel-photo" style={{ backgroundImage: `url(/panel-join.jpg)` }} />
          <div className="choice-panel-overlay" />
          <div className="choice-panel-body">
            <h2>Join Existing</h2>
            <p>Enter an invite code and step into an unfolding story.</p>
            <span className="choice-cta">Enter <ArrowRight size={15} /></span>
          </div>
        </Link>
      </div>

      <button className="landing-audio-btn" onClick={toggleAudio} aria-label="Toggle intro music">
        {playing ? <VolumeX size={16} /> : <Volume2 size={16} />}
        {playing ? 'Mute' : 'Play Music'}
      </button>
    </main>
  );
}
