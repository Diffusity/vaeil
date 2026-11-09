import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const labels = {
  long_term: 'Long-term relationship', undergraduate: 'Undergraduate', reading: 'Reading',
  honesty: 'Honesty', direct: 'Direct', quiet_and_routine: 'Quiet and routine',
};

function App() {
  const [view, setView] = useState(null);
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
      .then(data => { if (!controller.signal.aborted) setView(data); })
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
      {view && <>
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

createRoot(document.getElementById('root')).render(<App />);
