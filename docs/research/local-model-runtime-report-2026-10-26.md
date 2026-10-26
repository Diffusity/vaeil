# Local-model runtime attempt — 26 October 2026

## Status

Setup/latency authorization is separate from accuracy approval. No accuracy comparison is permitted before independent label review, dispute resolution and commit-hash freeze. Candidate labels remain unfrozen. Nothing in this report claims an unevaluated model failed or passed the safety bar.

Runtime block began04:45:52 UTC with a two-hour deadline06:45:52. Initial download reset, a ten-minute resume timed out, and a final bounded resume completed. Complete installer verified: **1662012016 bytes**, SHA256 **87309d23b423abeae1d8df2f98df95f94bf35659debfdf3761d65b7b62a75508**, Authenticode **Valid**, signer **Ollama Inc.** The downloaded installer remains in the user's TEMP as Vaeil-OllamaSetup-0.40.11.exe; it was not executed.

The bounded setup helper actually started at06:47:38, after its06:45:22 safety cutoff, and refused before installation. It finished06:47:42. The attempt's wall-clock span was **2h01m50s**, exceeding the outer window by1m50s; do not call it a completed in-time benchmark or equate all clock gaps with active work. No installation, model pull or inference occurred after the deadline (or before it). Stop/report rather than extend the session silently. A new runtime block requires renewed timebox authorization and corrected power prerequisites.

**Cleanup verified:** Ollama not installed; zero pulled models, zero model files and **0 model bytes**; no owned Ollama processes and no listener on11434. Installer size is not model storage. Runtime version, actual model digests, Vulkan discovery and Qwen3 non-thinking behavior are **not measured**. Official documented support is not substituted for a test on this machine.

## Verified preflight

- Actual machine: HP Laptop15s-eq2xxx; Windows11 Home Single Language10.0.26300, 64-bit; 33635885056 bytes RAM. AMD Radeon(TM) Graphics driver31.0.21925.1001. Ryzen5 5500U6C/12T and CPU baseline were verified in the earlier feasibility note.
- Windows GetSystemPowerStatus reports ACLineStatus=0 (battery); battery81%, later73%. Active plan Balanced; only Balanced listed. AC/DC sleep timers are already zero (disabled).
- This does **not** satisfy the required plugged-in/high-performance measurement conditions. Parth was asked to correct/confirm power; no response verified yet. No timing or sustained-load inference is valid until the checks pass. No attempt to manufacture a missing High performance plan or install a GPU driver.
- No tunnels, accounts, paid services or other models/software. Official runtime-control sources and pinned installer digest are in ollama-windows-runtime-controls-2026-10-26.md. CPU placement, Vulkan discovery and Qwen3 non-thinking must be reported as unverified until actual runtime evidence exists.

## Performance/accuracy result table

| Candidate | CPU c1/c2 samples | TTFT / total p95 / tokens per second | Cold load / 10-minute sustained | Safety result |
| --- | --- | --- | --- | --- |
| qwen2.5:1.5b | Not measured | Not measured | Not measured | Not run; label review/freeze pending |
| llama3.2:1b | Not measured | Not measured | Not measured | Not run; label review/freeze pending |
| qwen3:1.7b | Not measured | Not measured | Not measured | Not run; label review/freeze pending |

No CPU/Vulkan speed estimate is substituted for measurements. No timeout/concurrency/queue setting or smallest-passing-model recommendation can be derived from this table. Rules-first fallback is a proposal only if evidence shows no candidate passes, not an automatic response to a missing benchmark.

## Language and composition report status

| Language | Main cases across both tasks (safe/review) | Human review / model-alone / scanner-plus-rules accuracy |
| --- | --- | --- |
| English | 8/8 | Awaiting review; not evaluated |
| Hindi-English | 4/4 | Awaiting two readers; not evaluated |
| roman Gujarati | 4/4 | Awaiting two readers; not evaluated |
| Gujarati script | 4/4 | Awaiting two readers; not evaluated |

No confusion matrix, language-pass claim or comparison is invented before predictions exist. All scored denominators are provisional until exclusions are resolved. The separate eight development and five edge cases are unscored. Proposed supported-language filter is not adopted; counterfactual safe-approval ceilings are in the rubric, not measured model performance. H7 is #16, unassigned. No completed sheets/disagreement decisions received; that is not a finding of zero disagreements.

## Vetting input gate

Spec #7 defines the position of Vetting in the loop but no text/questionnaire. Applicant currently has only wrapped DOB. V fixtures remain provisional intent snippets; no private identity field is selected as model input. Parth must settle the input contract before those scores can claim to evaluate the application we would ship.

## Schedule and estimates — evidence limit

| Ticket | Previous planning estimate | Measured update |
| --- | --- | --- |
| T7 Messages/moderation | 2-3 sessions, before the new Withheld review workflow | Pending runtime evidence and typed-reason/no-resend/Admin-review implementation seam; no fabricated measured estimate |
| T12 Local-model adapter | Unknown; prior hosted-provider estimate superseded | Pending latency, accuracy, approved model and ngrok credit/hourly rate |
| T13 Demo/evaluation | 2-3 sessions | Pending runtime/rehearsal evidence and both Withheld reasons; no fabricated measured estimate |

Freeze remains28 November, five build sessions/week; November29-December4 rehearsal/fixes. Remaining non-T12 lead work is20-32 sessions after T1, plus feasibility/runtime work. Holding the original T1 reservation, original0.5-session research allowance and the full newly authorized benchmark-session reservation leaves only approximately **0.5-1.5 optimistic slots for T12/contingency** (one rehearsal session after freeze). Reservations are not measured active effort. The upper range does not fit and the optimistic plan has inadequate contingency; a full core-fit claim cannot be certified. Do not cut Admin, Reveal, Report handling or any rule to hide this risk. Re-estimate after evidence before starting T2/T3; later T7-T13/H1-H6 remain unpublished.

## Merge and next gates

PR #15 merged06:05:50 UTC using merge commit96a7852 after final-head Windows CI passed on a80db11 (401 tests). Independent review: Standards two wording findings fixed, Spec zero missing amendments. Label review is not a completed freeze. Next: power correction/runtime evidence and human review/input decision -> commit-hash freeze -> accuracy -> actual estimates/forecast -> T2/T3. No service provisioned or teammate assigned.
