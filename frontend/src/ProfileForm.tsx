import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';

type Draft = {
  pseudonym: string | null;
  relationship_intent: string | null;
  life_stage: string | null;
  interests: string[];
  values: string[];
  communication_style: string | null;
  pace_and_lifestyle: string | null;
  about: string;
};

const singleChoices = {
  relationship_intent: { label: 'Relationship intent', options: [['long_term', 'Long-term relationship'], ['open_to_relationship', 'Open to a relationship'], ['still_exploring', 'Still exploring']] },
  life_stage: { label: 'Life stage', options: [['undergraduate', 'Undergraduate'], ['postgraduate', 'Postgraduate'], ['working', 'Working'], ['between_study_and_work', 'Between study and work']] },
  communication_style: { label: 'Communication style', options: [['direct', 'Direct'], ['reflective', 'Reflective'], ['expressive', 'Expressive'], ['balanced', 'Balanced']] },
  pace_and_lifestyle: { label: 'Pace and lifestyle', options: [['quiet_and_routine', 'Quiet and routine'], ['balanced_routine_and_spontaneity', 'Balanced routine and spontaneity'], ['active_and_spontaneous', 'Active and spontaneous']] },
};
const multiChoices = {
  interests: { label: 'Interests', options: ['reading', 'music', 'films', 'gaming', 'cooking', 'art', 'technology', 'sports', 'fitness', 'outdoors', 'travel', 'volunteering'] },
  values: { label: 'Values', options: ['honesty', 'kindness', 'curiosity', 'family', 'independence', 'ambition', 'stability', 'creativity', 'community', 'wellbeing'] },
};
const singles = ['relationship_intent', 'life_stage', 'communication_style', 'pace_and_lifestyle'] as const;
function readProfile(data: unknown): { draft: Draft; complete: boolean } {
  if (!data || typeof data !== 'object') throw new Error('Invalid response');
  const root = data as Record<string, unknown>;
  if (!root.values_profile || typeof root.values_profile !== 'object') throw new Error('Invalid response');
  const profile = root.values_profile as Record<string, unknown>;
  const complete = root.complete !== false;
  const pseudonym = complete ? root.pseudonym : profile.pseudonym;
  if ((pseudonym !== null && typeof pseudonym !== 'string') || (complete && !pseudonym)
      || typeof profile.about !== 'string'
      || singles.some(key => profile[key] !== null && typeof profile[key] !== 'string')
      || !Array.isArray(profile.interests) || !profile.interests.every(item => typeof item === 'string')
      || !Array.isArray(profile.values) || !profile.values.every(item => typeof item === 'string')) throw new Error('Invalid response');
  // Keep only form fields: authorized own-identity payload values are not form state.
  return { complete, draft: { pseudonym, relationship_intent: profile.relationship_intent as string | null,
    life_stage: profile.life_stage as string | null, interests: profile.interests, values: profile.values,
    communication_style: profile.communication_style as string | null,
    pace_and_lifestyle: profile.pace_and_lifestyle as string | null, about: profile.about } };
}

export function ProfileForm({ onSessionExpired }: { onSessionExpired: () => void }) {
  const [draft, setDraft] = useState<Draft | null>(null);
  const [complete, setComplete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const load = useCallback(async () => {
    setBusy(true); setError('');
    try {
      const response = await fetch('/api/me/profile', { credentials: 'same-origin' });
      if (response.status === 401) { onSessionExpired(); return; }
      if (!response.ok) throw new Error('Unavailable');
      const parsed = readProfile(await response.json());
      setDraft(parsed.draft); setComplete(parsed.complete);
    } catch { setError('Could not load your profile. Please retry.'); }
    finally { setBusy(false); }
  }, [onSessionExpired]);
  useEffect(() => { void load(); }, [load]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft) return;
    setBusy(true); setError(''); setMessage('');
    const { pseudonym, ...values } = draft;
    try {
      const response = await fetch('/api/me/profile', { method: 'PUT', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(complete ? values : { ...values, pseudonym: pseudonym || null }) });
      if (response.status === 401) { onSessionExpired(); return; }
      if (!response.ok) {
        const failure = await response.json();
        if (failure.reason === 'invalid_profile' && failure.field === 'about' && failure.can_rephrase === true) {
          setError('About: Rephrase without contact details or your own name.');
        } else if (failure.reason === 'pseudonym_taken') {
          setError('Pseudonym: This name is taken. Choose another and retry.');
        } else if (failure.reason === 'invalid_pseudonym') {
          setError('Pseudonym: Choose an allowed name without your name or contact details.');
        } else if (failure.reason === 'invalid_profile') {
          const label = failure.field === 'interests' ? 'Interests' : failure.field === 'values' ? 'Values'
            : singles.includes(failure.field) ? singleChoices[failure.field as typeof singles[number]].label : 'Profile';
          setError(`${label}: Review your choices and retry.`);
        } else { setError('Could not save your profile. Your changes are still here; please retry.'); }
        return;
      }
      const parsed = readProfile(await response.json());
      setDraft(parsed.draft); setComplete(parsed.complete);
      setMessage(parsed.complete ? 'Profile saved.' : 'Draft saved. Complete all choices and choose a Pseudonym when you are ready.');
    } catch { setError('Could not save your profile. Your changes are still here; please retry.'); }
    finally { setBusy(false); }
  }

  return <section aria-labelledby="own-profile-heading">
    <h2 id="own-profile-heading">Your Values Profile</h2>
    <p>Demo only — use fictional details. Leave identifying details out of About.</p>
    {!draft ? <>
      {busy && <p role="status">Loading your profile…</p>}
      {error && <p role="alert">{error}</p>}
      {!busy && <button onClick={() => void load()}>Retry profile</button>}
    </> : <form aria-labelledby="own-profile-heading" onSubmit={save}>
      <fieldset disabled={busy}>
        {complete ? <p>Pseudonym: {draft.pseudonym} (fixed)</p> : <label>Pseudonym
          <input autoComplete="off" value={draft.pseudonym || ''} onChange={event => setDraft({ ...draft, pseudonym: event.target.value })} />
        </label>}
        {singles.map(key => <div key={key}><label htmlFor={`own-${key}`}>{singleChoices[key].label}</label>
          <select id={`own-${key}`} value={draft[key] || ''} onChange={event => setDraft({ ...draft, [key]: event.target.value || null })}>
            <option value="">Choose when ready</option>
            {singleChoices[key].options.map(([code, label]) => <option key={code} value={code}>{label}</option>)}
          </select>
        </div>)}
        {(['interests', 'values'] as const).map(key => <fieldset key={key}>
          <legend>{multiChoices[key].label} (choose 1–5 for a complete profile)</legend>
          {multiChoices[key].options.map(code => <label key={code} className="profile-choice">
            <input type="checkbox" checked={draft[key].includes(code)} onChange={event => setDraft({ ...draft,
              [key]: event.target.checked ? [...draft[key], code] : draft[key].filter(item => item !== code) })} />
            {code[0].toUpperCase() + code.slice(1)}
          </label>)}
        </fieldset>)}
        <label htmlFor="own-about">About (optional)</label>
        <textarea id="own-about" value={draft.about} onChange={event => setDraft({ ...draft, about: event.target.value })} />
        <p>Up to 280 characters after normalization. The server checks your saved text.</p>
        <button type="submit">Save profile</button>
      </fieldset>
      {busy && <p role="status">Saving your profile…</p>}
      {message && <p role="status">{message}</p>}
      {error && <p role="alert">{error}</p>}
    </form>}
  </section>;
}
