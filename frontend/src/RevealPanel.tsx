import { useCallback, useEffect, useRef, useState } from 'react';

type State = { conversation_id: string; eligible: boolean; viewer_consented: boolean; revealed: boolean };
type Profile = { relationship_intent: string; life_stage: string; interests: string[]; values: string[];
  communication_style: string; pace_and_lifestyle: string; about: string };
type Partner = { pseudonym: string; values_profile: Profile; legal_name?: string; email?: string; phone?: string | null };
type View = { state: State; partner: Partner };

function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid response');
  return value as Record<string, unknown>;
}
function exact(value: Record<string, unknown>, keys: string[]) {
  if (Object.keys(value).length !== keys.length || keys.some(key => !(key in value))) throw new Error('Invalid response');
}
function stateFrom(value: unknown, id: string): State {
  const data = record(value);
  exact(data, ['conversation_id', 'eligible', 'viewer_consented', 'revealed']);
  if (data.conversation_id !== id || ['eligible', 'viewer_consented', 'revealed'].some(key => typeof data[key] !== 'boolean')
      || (data.revealed && (!data.viewer_consented || data.eligible))) throw new Error('Invalid response');
  return data as State;
}
function partnerFrom(value: unknown, revealed: boolean): Partner {
  const data = record(value);
  exact(data, revealed ? ['pseudonym', 'values_profile', 'legal_name', 'email', 'phone'] : ['pseudonym', 'values_profile']);
  const profile = record(data.values_profile);
  const singles = ['relationship_intent', 'life_stage', 'communication_style', 'pace_and_lifestyle', 'about'];
  exact(profile, [...singles, 'interests', 'values']);
  if (typeof data.pseudonym !== 'string' || singles.some(key => typeof profile[key] !== 'string')
      || ['interests', 'values'].some(key => !Array.isArray(profile[key]) || !(profile[key] as unknown[]).every(item => typeof item === 'string'))
      || (revealed && (typeof data.legal_name !== 'string' || typeof data.email !== 'string'
        || (data.phone !== null && typeof data.phone !== 'string')))) throw new Error('Invalid response');
  return data as Partner;
}
const label = (code: string) => code.replaceAll('_', ' ');

export function RevealPanel({ conversationId, onUnauthorized, onClosed }: {
  conversationId: string; onUnauthorized: () => void; onClosed: () => void;
}) {
  const [view, setView] = useState<View | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const operation = useRef<AbortController | null>(null);
  const path = `/api/conversations/${encodeURIComponent(conversationId)}`;
  const perform = useCallback(async (method?: 'PUT' | 'DELETE') => {
    operation.current?.abort();
    const controller = new AbortController(); operation.current = controller;
    setBusy(true); setError('');
    try {
      const response = await fetch(path + (method ? '/reveal/consent' : '/reveal'), {
        method: method || 'GET', credentials: 'same-origin', signal: controller.signal,
      });
      if (controller.signal.aborted) return;
      if (response.status === 401) { onUnauthorized(); return; }
      if (response.status === 409) {
        const failure = record(await response.json());
        if (controller.signal.aborted) return;
        if (failure.reason === 'conversation_closed') { onClosed(); return; }
      }
      if (!response.ok) throw new Error('Unavailable');
      const state = stateFrom(await response.json(), conversationId);
      if (controller.signal.aborted) return;
      const partnerResponse = await fetch(path + '/partner', { credentials: 'same-origin', signal: controller.signal });
      if (controller.signal.aborted) return;
      if (partnerResponse.status === 401) { onUnauthorized(); return; }
      if (partnerResponse.status === 409) {
        const failure = record(await partnerResponse.json());
        if (controller.signal.aborted) return;
        if (failure.reason === 'conversation_closed') { onClosed(); return; }
      }
      if (!partnerResponse.ok) throw new Error('Unavailable');
      const partner = partnerFrom(await partnerResponse.json(), state.revealed);
      if (!controller.signal.aborted) setView({ state, partner });
    } catch { if (!controller.signal.aborted) setError('Could not confirm Reveal. Refresh to check the current state.'); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }, [path, conversationId, onUnauthorized, onClosed]);
  useEffect(() => {
    setView(null); void perform();
    return () => operation.current?.abort();
  }, [perform]);

  return <section aria-labelledby="reveal-heading">
    <h3 id="reveal-heading">Reveal</h3>
    <button disabled={busy} onClick={() => void perform()}>Refresh Reveal</button>
    {busy && <p role="status">Checking Reveal…</p>}
    {error && <p role="alert">{error}</p>}
    {view && <>
      <p>Pseudonym: {view.partner.pseudonym}</p>
      <dl>
        <dt>Relationship intent</dt><dd>{label(view.partner.values_profile.relationship_intent)}</dd>
        <dt>Life stage</dt><dd>{label(view.partner.values_profile.life_stage)}</dd>
        <dt>Interests</dt><dd>{view.partner.values_profile.interests.map(label).join(', ')}</dd>
        <dt>Values</dt><dd>{view.partner.values_profile.values.map(label).join(', ')}</dd>
        <dt>Communication style</dt><dd>{label(view.partner.values_profile.communication_style)}</dd>
        <dt>Pace and lifestyle</dt><dd>{label(view.partner.values_profile.pace_and_lifestyle)}</dd>
        <dt>About</dt><dd>{view.partner.values_profile.about}</dd>
      </dl>
      {view.state.revealed ? <>
        <p>Reveal complete.</p><p>{view.partner.legal_name}</p><p>{view.partner.email}</p>
        {view.partner.phone && <p>{view.partner.phone}</p>}
      </> : <>
        <p>{view.state.eligible ? 'You can choose to Reveal. Both Members must consent.' : 'Reveal is not yet available.'}</p>
        {view.state.viewer_consented
          ? <button disabled={busy} onClick={() => void perform('DELETE')}>Withdraw consent</button>
          : view.state.eligible && <button disabled={busy} onClick={() => void perform('PUT')}>Consent to Reveal</button>}
      </>}
    </>}
  </section>;
}
