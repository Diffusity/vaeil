import { useState } from 'react';
import type { FormEvent } from 'react';

type Principal = { role: 'applicant' | 'member' | 'admin'; admission: 'NeedsReview' | 'Approved' | 'Rejected' };

export function AdmissionPanel() {
  const [mode, setMode] = useState<'apply' | 'login' | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [principal, setPrincipal] = useState<Principal | null>(null);

  function select(next: 'apply' | 'login') {
    setMode(next); setError(''); setMessage('');
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const body = Object.fromEntries(new FormData(form));
    setBusy(true); setError(''); setMessage('');
    try {
      const response = await fetch(mode === 'apply' ? '/api/applications' : '/api/sessions', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin',
        body: JSON.stringify(mode === 'apply' ? { ...body, phone: body.phone || null } : body),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.reason === 'invalid_note' ? 'Remove contact details or rephrase your application note.'
          : data.reason === 'invalid_credentials' ? 'Could not sign in. Check your details and try again.'
          : 'Could not save. Review your details and try again.');
        return;
      }
      if (mode === 'apply') {
        if (!['NeedsReview', 'Approved'].includes(data.admission)) throw new Error('Invalid response');
        setMessage(data.admission === 'NeedsReview' ? 'Application received. Your application is under review.' : 'Your membership is approved.');
      } else {
        if (!['applicant', 'member', 'admin'].includes(data.role)
            || !['NeedsReview', 'Approved', 'Rejected'].includes(data.admission)) throw new Error('Invalid response');
        setPrincipal({ role: data.role, admission: data.admission });
      }
      form.reset(); setMode(null);
    } catch {
      setError('The service is unavailable. Please try again.');
    } finally { setBusy(false); }
  }

  async function signOut() {
    setBusy(true); setError('');
    try {
      const response = await fetch('/api/session', { method: 'DELETE', credentials: 'same-origin' });
      if (!response.ok) throw new Error('Unavailable');
      setPrincipal(null); setMessage('You are signed out.');
    } catch { setError('Could not sign out. Please try again.'); }
    finally { setBusy(false); }
  }

  return <section aria-labelledby="membership-heading">
    <h2 id="membership-heading">Membership</h2>
    {principal ? <>
      <p>{principal.admission === 'NeedsReview' ? 'Your application is under review.'
        : principal.admission === 'Rejected' ? 'An Admin has declined your application.' : 'Your membership is approved.'}</p>
      <button onClick={signOut} disabled={busy}>Sign out</button>
    </> : <nav aria-label="Membership actions">
      <button onClick={() => select('apply')} disabled={busy}>Apply with an Invite</button>
      <button onClick={() => select('login')} disabled={busy}>Sign in</button>
    </nav>}
    {mode && <form onSubmit={submit}>
      {mode === 'apply' && <>
        <p>Demo only — use fictional details.</p>
        <label>Legal name<input name="legal_name" autoComplete="off" required /></label>
        <label>Date of birth<input name="date_of_birth" type="date" required /></label>
        <label>Phone (optional)<input name="phone" type="tel" autoComplete="off" /></label>
        <label>Invite code<input name="invite_code" autoComplete="off" required /></label>
      </>}
      <label>Email<input name="email" type="email" autoComplete={mode === 'login' ? 'username' : 'off'} required /></label>
      <label>Password<input name="password" type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required /></label>
      {mode === 'apply' && <>
        <p>Use a password of 12–128 characters. Why would you like to join, and what are you looking for?</p>
        <label>Application note<textarea name="application_note" required /></label>
        <p>20–500 characters after normalization. Leave out contact details and your name.</p>
      </>}
      <button type="submit" disabled={busy}>{mode === 'apply' ? 'Submit application' : 'Continue'}</button>
    </form>}
    {busy && <p role="status">Checking your request…</p>}
    {message && <p>{message}</p>}
    {error && <p role="alert">{error}</p>}
  </section>;
}
