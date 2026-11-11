# T5 mutation results

CIrun43081827304, reviewed code19ccb9e. Each mutant restored before the next; normal contracts/privacy/purity checks passed afterwards. Exact restoration hashes are in t5-mutations-both-databases.json.

| Mutation | SQLite | PostgreSQL | Shared AST |
| --- | --- | --- | --- |
| remove normalized unique index | Killed | Killed | — |
| remove normalized key | Killed | Killed | — |
| allow second Pseudonym overwrite | Killed | Killed | — |
| commit instead of rollback | Killed | Killed | — |
| commit audit/domain early | Killed | Killed | — |
| allow audit UPDATE | Killed | Killed | — |
| allow audit DELETE | Killed | Killed | — |
| allow replacement of an audit event | Killed | Killed | — |
| omit active Conversation exclusion | Killed | Killed | — |
| omit monotonic Conversation guard | Killed | Killed | — |
| restore a plain private value | Killed | Killed | — |
| leak SQL bound parameters | Killed | Killed | — |
| permit commit after database failure | Killed | Killed | — |
| unwrap outside the approved mapper | — | — | Killed |

Totals:13/13SQLite,13/13PostgreSQL,1/1sharedarchitecture. No production database used. Supplementary unchanged product-test matrices: T2 19/19 and Slice2 12/12 killed; their sources restored.
