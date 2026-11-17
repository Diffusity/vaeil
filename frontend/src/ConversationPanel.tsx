import { RevealPanel } from './RevealPanel';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';

type Receipt = { message_id: string; outcome: 'Delivered' | 'Escalated' | 'Withheld';
  reason: string | null; review_state: string; retry_allowed: boolean; can_submit_for_review: boolean };
type Delivered = { message_id: string; text: string; delivered_at: string };
type View = { delivered: Delivered[]; attempts: Receipt[] };

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid response');
  return value as Record<string, unknown>;
}

function receipt(value: unknown, conversationId: string): Receipt {
  const data = object(value);
  const states = ['not_submitted', 'pending', 'released', 'discarded'];
  const failures = ['unavailable', 'timeout', 'unreachable', 'busy', 'queue_full', 'malformed', 'review_required'];
  if (typeof data.message_id !== 'string' || !data.message_id || data.conversation_id !== conversationId
      || !['Delivered', 'Escalated', 'Withheld'].includes(String(data.outcome))
      || !states.includes(String(data.review_state)) || typeof data.retry_allowed !== 'boolean'
      || typeof data.can_submit_for_review !== 'boolean') throw new Error('Invalid response');
  const withheld = data.outcome === 'Withheld';
  if ((withheld ? !failures.includes(String(data.reason)) : data.reason !== null)
      || (!withheld && (data.retry_allowed || data.can_submit_for_review))
      || (data.review_state !== 'not_submitted' && (data.retry_allowed || data.can_submit_for_review))
      || (data.can_submit_for_review && !data.retry_allowed)
      || (data.reason === 'review_required' && data.retry_allowed)) throw new Error('Invalid response');
  return { message_id: data.message_id, outcome: data.outcome as Receipt['outcome'],
    reason: data.reason as string | null, review_state: String(data.review_state),
    retry_allowed: data.retry_allowed, can_submit_for_review: data.can_submit_for_review };
}

function conversation(value: unknown, conversationId: string): View {
  const data = object(value);
  if (data.conversation_id !== conversationId || !Array.isArray(data.delivered) || !Array.isArray(data.attempts)) throw new Error('Invalid response');
  return { delivered: data.delivered.map(value => {
    const item = object(value);
    if (typeof item.message_id !== 'string' || typeof item.text !== 'string'
        || typeof item.delivered_at !== 'string' || !Number.isFinite(Date.parse(item.delivered_at))) throw new Error('Invalid response');
    return { message_id: item.message_id, text: item.text, delivered_at: item.delivered_at };
  }), attempts: data.attempts.map(value => receipt(value, conversationId)) };
}

export function ConversationPanel({ conversationId, onUnauthorized }: { conversationId: string; onUnauthorized: () => void }) {
  const [view, setView] = useState<View | null>(null);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState<{ message_id: string; text: string } | null>(null);
  const operation = useRef<AbortController | null>(null);
  const unresolved = useRef<{ text: string; key: string } | null>(null);
  const path = `/api/conversations/${encodeURIComponent(conversationId)}/messages`;

  const begin = () => {
    operation.current?.abort();
    const controller = new AbortController();
    operation.current = controller;
    return controller;
  };
  const load = useCallback(async () => {
    const controller = new AbortController();
    operation.current?.abort(); operation.current = controller;
    setBusy(true); setError('');
    try {
      const response = await fetch(path, { credentials: 'same-origin', signal: controller.signal });
      if (controller.signal.aborted) return;
      if (response.status === 401) { onUnauthorized(); return; }
      if (!response.ok) throw new Error('Unavailable');
      const data = conversation(await response.json(), conversationId);
      if (!controller.signal.aborted) setView(data);
    } catch { if (!controller.signal.aborted) setError('Could not refresh the Conversation. Loaded Messages may be out of date; please retry.'); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }, [conversationId, path, onUnauthorized]);
  useEffect(() => {
    setView(null); setRetry(null); setText(''); unresolved.current = null;
    void load();
    return () => operation.current?.abort();
  }, [load]);

  function remember(item: Receipt) {
    setView(previous => ({ delivered: previous?.delivered || [],
      attempts: [...(previous?.attempts || []).filter(old => old.message_id !== item.message_id), item] }));
  }

  async function send(body: string) {
    const controller = begin();
    setBusy(true); setError('');
    const key = unresolved.current?.text === body ? unresolved.current.key : crypto.randomUUID();
    unresolved.current = { text: body, key };
    try {
      const response = await fetch(path, { method: 'POST', credentials: 'same-origin', signal: controller.signal,
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ request_id: key, text: body }) });
      if (controller.signal.aborted) return;
      if (response.status === 401) { onUnauthorized(); return; }
      if (!response.ok) { setError(response.status === 409 ? 'This request or Message text already has a decision. Refresh or change your Message.'
        : 'Could not send. Your text is still here; review it and retry.'); return; }
      const item = receipt(await response.json(), conversationId);
      if (controller.signal.aborted) return;
      unresolved.current = null; remember(item);
      if (item.retry_allowed) setRetry({ message_id: item.message_id, text: body });
      else { setText(''); setRetry(null); }
      await load();
    } catch { if (!controller.signal.aborted) setError('Could not confirm your Message. Retry to check the same request.'); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }

  async function submit(messageId: string) {
    const controller = begin(); setBusy(true); setError('');
    try {
      const response = await fetch(`/api/messages/${encodeURIComponent(messageId)}/review`, {
        method: 'POST', credentials: 'same-origin', signal: controller.signal,
      });
      if (controller.signal.aborted) return;
      if (response.status === 401) { onUnauthorized(); return; }
      if (!response.ok) throw new Error('Unavailable');
      const item = receipt(await response.json(), conversationId);
      if (controller.signal.aborted) return;
      remember(item);
      setText(current => retry?.message_id === messageId && current === retry.text ? '' : current);
      setRetry(current => current?.message_id === messageId ? null : current);
      await load();
    } catch { if (!controller.signal.aborted) setError('Could not submit for review. Refresh and retry.'); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }

  function compose(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); void send(text);
  }

  return <section aria-labelledby="conversation-heading">
    <h2 id="conversation-heading">Conversation</h2>
    <RevealPanel conversationId={conversationId} onUnauthorized={onUnauthorized} />
    <p>Messages are checked before delivery. Demo only — use fictional details.</p>
    <button disabled={busy} onClick={() => void load()}>Refresh Conversation</button>
    {busy && <p role="status">Checking…</p>}
    {error && <p role="alert">{error}</p>}
    {view && <>
      <div role="log" aria-label="Delivered Messages">
        {view.delivered.length === 0 && <p>No delivered Messages yet.</p>}
        {view.delivered.map(item => <p className="message-body" key={item.message_id}>{item.text}</p>)}
      </div>
      <form onSubmit={compose}>
        <label htmlFor="message-text">Message</label>
        <textarea id="message-text" value={text} disabled={busy} onChange={event => setText(event.target.value)} />
        <p>Up to 2,000 characters after normalization. No silent truncation.</p>
        <button disabled={busy} type="submit">Send Message</button>
      </form>
      <ul aria-label="Your Message status">
        {view.attempts.map((item, index) => <li key={item.message_id}>
          <p>Message attempt {index + 1}</p>
          <p>{item.review_state === 'pending' ? 'Under review. Not delivered.'
            : item.review_state === 'discarded' ? 'An Admin discarded this Message. Not delivered.'
            : item.outcome === 'Withheld' ? (item.retry_allowed
              ? item.can_submit_for_review ? 'Withheld — technical failure. Retry or submit for review.' : 'Withheld — technical failure. Retry is available.'
              : 'Withheld. Retry and review submission are unavailable.')
            : item.outcome === 'Escalated' ? 'Delivered and queued for Admin review.' : 'Delivered.'}</p>
          {item.can_submit_for_review && <button disabled={busy} onClick={() => void submit(item.message_id)}>Submit for review</button>}
          {item.retry_allowed && retry?.message_id === item.message_id && <button disabled={busy} onClick={() => void send(retry.text)}>Retry Message</button>}
        </li>)}
      </ul>
    </>}
  </section>;
}
