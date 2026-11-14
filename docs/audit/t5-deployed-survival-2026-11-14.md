# T5 deployed storage survival — 14 November 2026

Authorized check on the existing free Render/Neon deployment. No secrets opened/copied, no new accounts/resources, no paid operations and no public diagnostic endpoint.

At approximately12:02 Asia/Calcutta, used the Neon SQL Editor on the existing production branch/database to create the isolated table `vaeil_t5_durability_probe`, with a TEXT primary-key marker and TEXT note. Inserted marker `t5-2026-11-14`, note `fictional durability fixture only`, using ON CONFLICT DO NOTHING. A separate SELECT returned exactly that one fictional row before restart.

At12:03 the existing Render service's Restart service action completed; Events showed Service restarted by you14November12:03. The public smoke then passed HTML/assets, exact anonymous payload, health and real database readiness. Re-ran only SELECT after restart; Neon returned one row with the identical marker/note (627ms query display). No INSERT or CREATE ran after restart, so the post-restart read did not recreate the fixture. The harmless fixture remains for repeatable inspection; no deletion performed.

This proves the isolated Neon record survives the application service restart. It is not a Member API round trip, a disaster-recovery/backup test, a database restart, an idle-spin-down measurement or proof the fictional endpoint uses repositories. Production business API wiring remains T6 and later. Repository mapping/constraints/rollback/audit behavior is separately covered by the same SQLite/PostgreSQL contract suite in disposable CI. The currently deployed runtime remains7fd4ad0; this check does not claim T5 code has been deployed. No real Member data was used.

Reproduction SQL (synthetic, no credentials):

```sql
CREATE TABLE IF NOT EXISTS vaeil_t5_durability_probe (
    marker TEXT PRIMARY KEY, note TEXT NOT NULL
);
INSERT INTO vaeil_t5_durability_probe(marker, note)
VALUES ('t5-2026-11-14', 'fictional durability fixture only')
ON CONFLICT (marker) DO NOTHING;
SELECT marker, note FROM vaeil_t5_durability_probe
WHERE marker = 't5-2026-11-14';
-- After restarting Render: run only the SELECT above.
```
