# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`UBIQUITOUS_LANGUAGE.md`** and **`GLOSSARY.md`** at the repo root — two views of one vocabulary, kept in sync (see **Vocabulary files** below).
- **`GLOSSARY-MAP.md`** at the repo root if it exists: it points at one `GLOSSARY.md` per context. Read each one relevant to the topic.
- **`docs/adr/`**: read ADRs that touch the area you're about to work in. In multi-context repos, also check `src/<context>/docs/adr/` for context-scoped decisions.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## Vocabulary files

One vocabulary, two files — never let them disagree, never invent a third name:

- **`UBIQUITOUS_LANGUAGE.md`** — the IT643-evaluated artifact. Structure, in order: grouped term tables (`Term | Definition | Aliases to avoid | Named in code at`), **Relationships**, **Example dialogue**, **Flagged ambiguities** (one word for two concepts, or two words for one — say which wins), **Code drift**. Citations are `path:line` and must match reality; stale docs are graded as absent. Report drift, never silently rename a term.
- **`GLOSSARY.md`** — the skills'/agents' view, following the domain-modeling format: definitions and `_Avoid_` synonyms only, no implementation details.
- **Sync rule:** when a term is settled, added, or changed, update **both** in the same change. If they disagree, the code wins — fix the file that is stale.

## File structure

Single-context repo (most repos):

```
/
├── GLOSSARY.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

Multi-context repo (presence of `GLOSSARY-MAP.md` at the root):

```
/
├── GLOSSARY-MAP.md
├── docs/adr/                          ← system-wide decisions
└── src/
    ├── ordering/
    │   ├── GLOSSARY.md
    │   └── docs/adr/                  ← context-specific decisions
    └── billing/
        ├── GLOSSARY.md
        └── docs/adr/
```

## Use the vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `UBIQUITOUS_LANGUAGE.md` / `GLOSSARY.md`. Don't drift to synonyms those files explicitly avoid.

If the concept you need isn't in the vocabulary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders), but worth reopening because…_
