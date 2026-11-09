import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

type DemoView = {
  pseudonym: string;
  values_profile: {
    relationship_intent: string; life_stage: string; interests: string[]; values: string[];
    communication_style: string; pace_and_lifestyle: string; about: string;
  };
};

const labels: Record<string, string> = {
  long_term: 'Long-term relationship', undergraduate: 'Undergraduate', reading: 'Reading',
  honesty: 'Honesty', direct: 'Direct', quiet_and_routine: 'Quiet and routine',
};

function parseView(data: unknown): DemoView {
  const record = (value: unknown): value is Record<string, unknown> =>
    typeof value === 'object' && value !== null && !Array.isArray(value);
  if (!record(data) || Object.keys(data).sort().join() !== 'pseudonym,values_profile'
      || typeof data.pseudonym !== 'string' || !record(data.values_profile)) {
    throw new Error('Invalid demo response');
  }
  const profile = data.values_profile;
  const strings = ['relationship_intent', 'life_stage', 'communication_style', 'pace_and_lifestyle', 'about'];
  if (Object.keys(profile).sort().join() !== [...strings, 'interests', 'values'].sort().join()
      || !strings.every(key => typeof profile[key] === 'string')
      || !['interests', 'values'].every(key => Array.isArray(profile[key])
        && profile[key].every((value: unknown) => typeof value === 'string'))) {
    throw new Error('Invalid demo response');
  }
  return data as DemoView;
}

function App() {
  const [view, setView] = useState<DemoView | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setView(null);
    setError(false);
    fetch('/api/demo/member', { signal: controller.signal, cache: 'no-store' })
      .then(response => {
        if (!response.ok) throw new Error('Demo unavailable');
        return response.json();
      })
      .then(data => { const parsed = parseView(data); if (!controller.signal.aborted) setView(parsed); })
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, [attempt]);
  const profile = view?.values_profile;
  return <main>
    <header><h1>Vaeil</h1><p>Meet through what matters.</p></header>
    <aside>Demo only — don't enter real personal details. This profile is fictional.</aside>
    <section aria-labelledby="profile-heading">
      <p className="eyebrow">Anonymous Values Profile</p>
      {!view && !error && <p role="status">Loading the fictional Values Profile…</p>}
      {error && <div role="alert"><p>Could not load the demo. Please try again.</p>
        <button onClick={() => setAttempt(value => value + 1)}>Try again</button></div>}
      {view && profile && <>
        <h2 id="profile-heading">{view.pseudonym}</h2>
        <p>Identity stays private before a mutual Reveal.</p>
        <dl>
          <dt>Relationship intent</dt><dd>{labels[profile.relationship_intent]}</dd>
          <dt>Life stage</dt><dd>{labels[profile.life_stage]}</dd>
          <dt>Interests</dt><dd>{profile.interests.map(code => labels[code]).join(', ')}</dd>
          <dt>Values</dt><dd>{profile.values.map(code => labels[code]).join(', ')}</dd>
          <dt>Communication style</dt><dd>{labels[profile.communication_style]}</dd>
          <dt>Pace and lifestyle</dt><dd>{labels[profile.pace_and_lifestyle]}</dd>
        </dl>
        {profile.about && <p>{profile.about}</p>}
      </>}
    </section>
    <footer>Local walking skeleton · values-based matching · human safety review planned</footer>
  </main>;
}

createRoot(document.getElementById('root')!).render(<App />);
