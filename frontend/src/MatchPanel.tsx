import { useCallback, useEffect, useRef, useState } from 'react';
import { singleChoices } from './ProfileForm';

type Choice = 'accept' | 'decline';
type Match = {
  match_id: string; state: 'pending' | 'accepted' | 'declined'; decision: Choice | null;
  partner: { pseudonym: string; values_profile: Record<string, string | string[]> };
  conversation_id?: string;
};

function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function readMatch(value: unknown): Match {
  if (!object(value) || typeof value.match_id !== 'string'
      || (value.state !== 'pending' && value.state !== 'accepted' && value.state !== 'declined')
      || (value.decision !== null && value.decision !== 'accept' && value.decision !== 'decline')
      || !object(value.partner) || Object.keys(value.partner).length !== 2
      || typeof value.partner.pseudonym !== 'string' || !object(value.partner.values_profile)) throw new Error('Invalid Match');
  if (value.state === 'accepted'
    ? typeof value.conversation_id !== 'string' || !value.conversation_id || value.decision !== 'accept'
    : 'conversation_id' in value) throw new Error('Invalid Conversation link');
  const profile = value.partner.values_profile;
  const clean: Match['partner']['values_profile'] = {};
  for (const [key, field] of Object.entries(singleChoices)) {
    const option = field.options.find(([code]) => code === profile[key]);
    if (!option) throw new Error('Invalid Values Profile');
    clean[field.label] = option[1];
  }
  for (const [key, label] of [['interests', 'Interests'], ['values', 'Values']]) {
    const list = profile[key];
    if (!Array.isArray(list) || !list.length || list.some(item => typeof item !== 'string')) throw new Error('Invalid list');
    clean[label] = list;
  }
  if (typeof profile.about !== 'string') throw new Error('Invalid About');
  clean.About = profile.about;
  return { match_id: value.match_id, state: value.state, decision: value.decision,
    partner: { pseudonym: value.partner.pseudonym, values_profile: clean },
    ...(typeof value.conversation_id === 'string' ? { conversation_id: value.conversation_id } : {}) };
}

export function MatchPanel({ onSessionExpired }: { onSessionExpired: () => void }) {
  const [matches, setMatches] = useState<Match[] | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const scope = useRef<AbortController | null>(null);
  const locked = useRef(false);

  const run = useCallback(async (path: string, decision?: Choice) => {
    const signal = scope.current?.signal;
    if (!signal || signal.aborted || locked.current) return;
    locked.current = true;
    setBusy(true); setError('');
    try {
      const response = await fetch(path, { credentials: 'same-origin', signal,
        ...(decision === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ decision }) }) });
      if (signal.aborted) return;
      if (response.status === 401 || response.status === 403) { onSessionExpired(); return; }
      if (!response.ok) throw new Error('Match request refused');
      const payload: unknown = await response.json();
      if (signal.aborted) return;
      if (decision === undefined) {
        if (!object(payload) || !Array.isArray(payload.matches)) throw new Error('Invalid Matches');
        setMatches(payload.matches.map(readMatch));
      } else {
        const changed = readMatch(payload);
        const expected = path.split('/').at(-2);
        if (encodeURIComponent(changed.match_id) !== expected || changed.decision !== decision) throw new Error('Invalid decision response');
        setMatches(current => current?.map(item => item.match_id === changed.match_id ? changed : item) ?? null);
      }
    } catch {
      if (!signal.aborted) setError('Could not confirm the Match request. Refresh Matches and try again.');
    } finally {
      if (!signal.aborted) { locked.current = false; setBusy(false); }
    }
  }, [onSessionExpired]);

  useEffect(() => {
    const controller = new AbortController();
    scope.current = controller; locked.current = false;
    void run('/api/me/matches');
    return () => { controller.abort(); scope.current = null; };
  }, [run]);

  return <section aria-labelledby="match-heading">
    <h3 id="match-heading">Matches</h3>
    <button disabled={busy} onClick={() => void run('/api/me/matches')}>Refresh Matches</button>
    {busy && <p role="status">Checking Matches…</p>}
    {error && <p role="alert">{error}</p>}
    {matches?.length === 0 && <p>No Matches yet.</p>}
    {!!matches?.length && <ul>{matches.map(item => <li key={item.match_id}>
      <h4>{item.partner.pseudonym}</h4>
      <dl>{Object.entries(item.partner.values_profile).map(([label, value]) => <div key={label}>
        <dt>{label}</dt><dd>{Array.isArray(value) ? value.join(', ') : value}</dd>
      </div>)}</dl>
      {item.state === 'declined' && <p>Match declined.</p>}
      {item.state === 'pending' && (item.decision ? <p>Waiting for the other Member.</p> :
        (['accept', 'decline'] as const).map(decision => <button key={decision} disabled={busy}
          onClick={() => void run('/api/me/matches/' + encodeURIComponent(item.match_id) + '/decision', decision)}>
          {decision === 'accept' ? 'Accept Match' : 'Decline Match'}
        </button>))}
      {item.state === 'accepted' && item.conversation_id &&
        <a href={'/?conversation=' + encodeURIComponent(item.conversation_id)}>Open Conversation</a>}
    </li>)}</ul>}
  </section>;
}
