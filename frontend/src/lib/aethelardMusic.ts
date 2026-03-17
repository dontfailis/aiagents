// Ambient fantasy RPG intro music — composed by Gemini (Web Audio API)

export function createAethelardMusic(ctx: AudioContext): void {
  // --- CONSTANTS AND HELPERS ---
  const now = ctx.currentTime;
  const LOOP_DURATION = 24; // A 24-second loop for a slow, evolving piece

  // Helper to convert MIDI note number to frequency
  const mtof = (midi: number): number => Math.pow(2, (midi - 69) / 12) * 440;

  // A mysterious C Minor Pentatonic Scale
  const scale = [
    mtof(48), // C3
    mtof(51), // Eb3
    mtof(53), // F3
    mtof(55), // G3
    mtof(58), // Bb3
    mtof(60), // C4
    mtof(63), // Eb4
    mtof(65), // F4
  ];

  // --- MASTER OUTPUT ---
  const masterGain = ctx.createGain();
  masterGain.gain.setValueAtTime(0.4, now);
  masterGain.connect(ctx.destination);

  // --- REVERB EFFECT (feedback delay loop) ---
  const reverbInput = ctx.createGain();
  const reverbOutput = ctx.createGain();
  const delay1 = ctx.createDelay(2.0);
  const delay2 = ctx.createDelay(1.5);
  const feedback = ctx.createGain();
  const filter = ctx.createBiquadFilter();

  filter.type = 'lowpass';
  filter.frequency.value = 1500;
  feedback.gain.value = 0.6;
  reverbOutput.gain.value = 0.3;

  reverbInput.connect(delay1);
  reverbInput.connect(delay2);
  delay1.connect(filter);
  delay2.connect(filter);
  filter.connect(feedback);
  feedback.connect(delay1);
  filter.connect(reverbOutput);
  reverbOutput.connect(masterGain);

  // --- LOW RUMBLE / BASS DRONE ---
  const bassDroneGain = ctx.createGain();
  bassDroneGain.gain.setValueAtTime(0, now);
  bassDroneGain.gain.linearRampToValueAtTime(0.5, now + 10);

  const bassOsc = ctx.createOscillator();
  bassOsc.type = 'sine';
  bassOsc.frequency.value = mtof(24); // C1
  const bassFilter = ctx.createBiquadFilter();
  bassFilter.type = 'lowpass';
  bassFilter.frequency.value = 120;

  bassOsc.connect(bassFilter);
  bassFilter.connect(bassDroneGain);
  bassDroneGain.connect(masterGain);
  bassOsc.start(now);

  // --- PAD DRONES ---
  const createPad = (baseFrequency: number, detuneCents: number, startTime: number) => {
    const padGain = ctx.createGain();
    padGain.gain.setValueAtTime(0, startTime);
    padGain.gain.linearRampToValueAtTime(0.2, startTime + 8);

    const padFilter = ctx.createBiquadFilter();
    padFilter.type = 'lowpass';
    padFilter.frequency.setValueAtTime(300, startTime);
    padFilter.frequency.linearRampToValueAtTime(800, startTime + LOOP_DURATION);
    padFilter.Q.value = 5;

    padGain.connect(padFilter);
    padFilter.connect(masterGain);

    const reverbSend = ctx.createGain();
    reverbSend.gain.value = 0.4;
    padFilter.connect(reverbSend);
    reverbSend.connect(reverbInput);

    [-detuneCents, 0, detuneCents].forEach(detune => {
      const osc = ctx.createOscillator();
      osc.type = 'sawtooth';
      osc.frequency.value = baseFrequency;
      osc.detune.value = detune;
      osc.connect(padGain);
      osc.start(startTime);
    });
  };

  createPad(mtof(36), 7, now);  // C2
  createPad(mtof(43), -5, now); // G2

  // --- MELODY ---
  const melodySequence = [
    { note: 0, time: 2,  duration: 4 }, // C3
    { note: 3, time: 8,  duration: 4 }, // G3
    { note: 2, time: 14, duration: 3 }, // F3
    { note: 4, time: 18, duration: 5 }, // Bb3
  ];

  const playMelodyNote = (noteIndex: number, startTime: number, duration: number) => {
    const freq = scale[noteIndex];
    if (!freq) return;

    const osc = ctx.createOscillator();
    osc.type = 'triangle';
    osc.frequency.value = freq;

    const noteGain = ctx.createGain();
    noteGain.gain.setValueAtTime(0, startTime);
    noteGain.gain.linearRampToValueAtTime(0.3, startTime + 0.1);
    noteGain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);

    const noteFilter = ctx.createBiquadFilter();
    noteFilter.type = 'lowpass';
    noteFilter.frequency.value = 1200;

    osc.connect(noteFilter);
    noteFilter.connect(noteGain);
    noteGain.connect(masterGain);

    const reverbSend = ctx.createGain();
    reverbSend.gain.value = 0.6;
    noteGain.connect(reverbSend);
    reverbSend.connect(reverbInput);

    osc.start(startTime);
    osc.stop(startTime + duration + 0.5);
  };

  // --- SCHEDULER ---
  let nextLoopTime = now;

  const scheduleNextLoop = () => {
    melodySequence.forEach(note => {
      playMelodyNote(note.note, nextLoopTime + note.time, note.duration);
    });
  };

  const scheduler = () => {
    while (nextLoopTime < ctx.currentTime + LOOP_DURATION / 2) {
      scheduleNextLoop();
      nextLoopTime += LOOP_DURATION;
    }
    setTimeout(scheduler, 500);
  };

  scheduler();
}
