import { useCallback, useEffect, useRef, useState } from 'react';

type Application = { applicant_id: string; application_note: string };
type Message = { message_id: string; text: string; outcome: 'Withheld' | 'Escalated' };
type Queue<T> = { items: T[]; status: 'loading' | 'ready' | 'error' };

function record(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function applications(value: unknown): Application[] {
  if (!record(value) || !Array.isArray(value.applications)) throw new Error('Invalid queue');
  return value.applications.map((row: unknown) => {
    if (!record(row) || typeof row.applicant_id !== 'string' || typeof row.application_note !== 'string') throw new Error('Invalid application');
    return { applicant_id: row.applicant_id, application_note: row.application_note };
  });
}

function messages(value: unknown): Message[] {
  if (!record(value) || !Array.isArray(value.messages)) throw new Error('Invalid queue');
  return value.messages.map((row: unknown) => {
    if (!record(row) || typeof row.message_id !== 'string' || typeof row.text !== 'string'
        || (row.outcome !== 'Withheld' && row.outcome !== 'Escalated')) throw new Error('Invalid Message');
    return { message_id: row.message_id, text: row.text, outcome: row.outcome };
  });
}

function queueStatus<T>(queue: Queue<T>, empty: string) {
  if (queue.status === 'loading') return <p role="status">Loading queue…</p>;
  if (queue.status === 'error') return <p role="alert">Could not load this queue. Refresh to try again.</p>;
  if (!queue.items.length) return <p>{empty}</p>;
  return null;
}

export function AdminConsole({ onSessionExpired }: { onSessionExpired: () => void }) {
  const [pending, setPending] = useState<Queue<Application>>({ items: [], status: 'loading' });
  const [moderation, setModeration] = useState<Queue<Message>>({ items: [], status: 'loading' });
  const [code, setCode] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [working, setWorking] = useState(false);
  const scope = useRef<AbortController | null>(null);
  const locked = useRef(false);

  const request = useCallback(async (path: string, signal: AbortSignal, body?: object) => {
    const response = await fetch(path, {
      signal, credentials: 'same-origin',
      ...(body === undefined ? {} : {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      }),
    });
    if (signal.aborted) throw new Error('Request cancelled');
    if (response.status === 401 || response.status === 403) onSessionExpired();
    if (!response.ok) throw new Error('Request refused');
    return response;
  }, [onSessionExpired]);

  const refresh = useCallback(async (signal: AbortSignal) => {
    async function load<T>(path: string, decode: (value: unknown) => T[], update: (value: Queue<T>) => void) {
      update({ items: [], status: 'loading' });
      try {
        const response = await request(path, signal);
        const items = decode(await response.json());
        if (!signal.aborted) update({ items, status: 'ready' });
      } catch {
        if (!signal.aborted) update({ items: [], status: 'error' });
      }
    }
    await Promise.all([
      load('/api/admin/applications', applications, setPending),
      load('/api/admin/messages', messages, setModeration),
    ]);
  }, [request]);

  useEffect(() => {
    const controller = new AbortController();
    scope.current = controller;
    void refresh(controller.signal);
    return () => { controller.abort(); scope.current = null; };
  }, [refresh]);

  async function run(action: (signal: AbortSignal) => Promise<void>) {
    const signal = scope.current?.signal;
    if (!signal || signal.aborted || locked.current) return;
    locked.current = true;
    setWorking(true); setStatus(''); setError('');
    try {
      await action(signal);
    } catch {
      if (!signal.aborted) setError('Could not confirm the Admin action. Refresh the queues before retrying.');
    } finally {
      locked.current = false;
      if (!signal.aborted) setWorking(false);
    }
  }

  function issueInvite() {
    return run(async signal => {
      setCode('');
      const response = await request('/api/admin/invites', signal, {});
      const value: unknown = await response.json();
      if (!record(value) || typeof value.invite_code !== 'string' || !value.invite_code) throw new Error('Invalid Invite');
      if (!signal.aborted) setCode(value.invite_code);
    });
  }

  const queuesLoading = pending.status === 'loading' || moderation.status === 'loading';

  function recordDecision(path: string, decision: string) {
    if (queuesLoading) return;
    return run(async signal => {
      await request(path, signal, { decision });
      if (signal.aborted) return;
      setStatus('Decision recorded.');
      await refresh(signal);
    });
  }

  function proposeMatches() {
    return run(async signal => {
      const response = await request('/api/admin/matches', signal, {});
      const value: unknown = await response.json();
      if (!record(value) || typeof value.created !== 'number' || !Number.isSafeInteger(value.created) || value.created < 0)
        throw new Error('Invalid Match count');
      if (!signal.aborted) setStatus(value.created === 1 ? '1 Match proposed.' : value.created + ' Matches proposed.');
    });
  }

  function copyInvite() {
    return run(async signal => {
      try {
        await navigator.clipboard.writeText(code);
        if (!signal.aborted) setStatus('Invite copied.');
      } catch {
        if (!signal.aborted) setError('Could not copy automatically. Select and copy the Invite code.');
      }
    });
  }

  function messageQueue(outcome: Message['outcome'], title: string) {
    const queue = { ...moderation, items: moderation.items.filter(item => item.outcome === outcome) };
    const options = outcome === 'Withheld' ? ['release', 'discard'] : ['approve', 'reject'];
    const endpoint = outcome === 'Withheld' ? 'decision' : 'escalation-decision';
    return <section>
      <h4>{title}</h4>
      {queueStatus(queue, 'No items in this queue.')}
      {!!queue.items.length && <ul>{queue.items.map(item => <li key={item.message_id}>
        <p>{item.text}</p>
        {options.map(decision => <button key={decision} disabled={working || queuesLoading}
          onClick={() => void recordDecision('/api/admin/messages/' + encodeURIComponent(item.message_id) + '/' + endpoint, decision)}>
          {decision[0].toUpperCase() + decision.slice(1)}
        </button>)}
      </li>)}</ul>}
    </section>;
  }

  return <section aria-labelledby="admin-console-heading">
    <h3 id="admin-console-heading">Admin console</h3>
    <button onClick={() => void issueInvite()} disabled={working}>Issue Invite</button>
    {code && <>
      <label>Issued Invite code<input readOnly value={code} /></label>
      <button onClick={() => void copyInvite()} disabled={working}>Copy Invite</button>
    </>}
    <button onClick={() => void run(refresh)} disabled={working || queuesLoading}>Refresh queues</button>
    <button onClick={() => void proposeMatches()} disabled={working}>Propose Matches</button>
    {status && <p role="status">{status}</p>}
    {error && <p role="alert">{error}</p>}
    <section>
      <h4>Applications in NeedsReview</h4>
      {queueStatus(pending, 'No applications awaiting review.')}
      {!!pending.items.length && <ul>{pending.items.map(item => <li key={item.applicant_id}>
        <p>{item.application_note}</p>
        {['approve', 'reject'].map(decision => <button key={decision} disabled={working || queuesLoading}
          onClick={() => void recordDecision('/api/admin/applications/' + encodeURIComponent(item.applicant_id) + '/decision', decision)}>
          {decision === 'approve' ? 'Approve' : 'Reject'}
        </button>)}
      </li>)}</ul>}
    </section>
    {messageQueue('Withheld', 'Messages under review')}
    {messageQueue('Escalated', 'Escalated deliveries')}
    <section><h4>Reports</h4><p>Report queue is unavailable.</p></section>
  </section>;
}
