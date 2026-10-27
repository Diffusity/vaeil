# Measured local-model runtime feasibility — 27 October 2026

**Outcome:** all three authorized models completed CPU and Vulkan latency/concurrency/sustained-load measurements on the actual laptop. All six combinations met the short-call latency/failure bars. This is **not a safety-accuracy pass or a final model selection**: no 40-case accuracy run occurred. Parth approved the labels; required independent non-English reviewer coverage has not yet been recorded, and production vetting text remains undefined.

## Machine, runtime and controls

HP15s-eq2xxx, Ryzen5 5500U (6C/12T), 33635885056 bytes RAM; Windows11 Home Single Language10.0.26300; AMD Radeon(TM) Graphics driver31.0.21925.1001. Native user-level **Ollama0.40.11**. No WSL, driver package, tunnel, account or paid service installed. AC/no-sleep/Best Performance checks passed. Balanced is the base scheme; the Best Performance AC overlay is ded574b5-45a0-4f42-8737-46345c09c238, not a standalone High performance scheme. See the [fixed protocol](runtime-benchmark-protocol-2026-10-27.md) for official Microsoft/runtime sources.

CPU placement showed zero GPU allocation. Vulkan discovery identified this iGPU, and process-local OLLAMA_IGPU_ENABLE=1 enabled actual offload; API placement and sanitized logs confirm it. GPU allocation is shared-memory runtime accounting, not proof of extra dedicated VRAM. Qwen3 used explicit think:false; no thinking text was returned in any accepted sample. The same prompt v1 and model digests were used across backends.

## Timings

All times are seconds. Each warm cell is **32 attempts**; concurrency2 had two overlapping client requests and two configured runtime slots. p95 uses nearest rank; every failure is retained. TTFT means first nonempty streamed content. Generation rate is the mean per-call eval_count / eval_duration, excluding prefill. All warm, cold and sustained outputs passed the fixed verdict-shape validator. They were not scored for safety.

| Backend | Model | Cold client / load | C1 total p95 | C1 TTFT p95 | C2 total p95 | C2 TTFT p95 | C1 / C2 output tokens/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cpu | qwen2.5:1.5b | 3.09 / 1.57 | 1.15 | 0.91 | 2.07 | 1.56 | 39.0 / 25.9 |
| cpu | llama3.2:1b | 4.12 / 1.35 | 1.92 | 1.56 | 3.47 | 2.53 | 25.3 / 17.3 |
| cpu | qwen3:1.7b | 4.09 / 1.84 | 1.55 | 1.26 | 2.94 | 2.14 | 30.1 / 19.9 |
| vulkan | qwen2.5:1.5b | 5.08 / 3.52 | 1.18 | 0.89 | 1.98 | 1.45 | 31.2 / 18.2 |
| vulkan | llama3.2:1b | 4.38 / 2.81 | 1.25 | 0.84 | 2.00 | 1.50 | 22.3 / 16.2 |
| vulkan | qwen3:1.7b | 4.91 / 2.78 | 1.70 | 1.31 | 2.69 | 1.92 | 24.5 / 16.2 |

Warm concurrency1 p95 <=8s, cold client/load <=15s and failures <=2% all pass on these fixed short inputs. There were **zero failures in384 warm attempts**, six cold calls and3976 sustained calls. This does not predict arbitrary input lengths or accuracy. Cold means runtime-unloaded model; OS filesystem/shader caches were not purged. The native /api/chat route was measured, not OpenAI-compatible transport conformance. Experimental per-call timeout30s was a measurement guard, not an approved production setting.

## Sustained load

| Backend | Model | Duration / calls | Total p95 | First-minute output tokens/s | Last-minute output tokens/s | Change |
| --- | --- | --- | --- | --- | --- | --- |
| cpu | qwen2.5:1.5b | 600.6s / 804 | 1.24 | 37.8 | 36.3 | -4.0% |
| cpu | llama3.2:1b | 600.5s / 580 | 1.83 | 25.5 | 25.5 | -0.2% |
| cpu | qwen3:1.7b | 600.4s / 633 | 1.60 | 29.6 | 29.9 | +0.8% |
| vulkan | qwen2.5:1.5b | 600.4s / 639 | 1.29 | 25.5 | 24.1 | -5.2% |
| vulkan | llama3.2:1b | 600.5s / 734 | 1.24 | 22.3 | 22.6 | +1.4% |
| vulkan | qwen3:1.7b | 600.5s / 586 | 1.64 | 24.9 | 25.1 | +0.6% |

No supported temperature sensor was collected. These are observed throughput changes, not proof of thermal throttling or its absence. No tests/builds or other heavy work ran during accepted measurements; only lightweight progress monitoring. An initial CPU attempt was interrupted when a lingering setup helper was detected; its samples are preserved separately and excluded for that protocol deviation, with no prompt/label changes.

## Model identity and storage

| Tag | Quantization / reported parameters | Runtime digest |
| --- | --- | --- |
| llama3.2:1b | Q8_0 / 1.2B | `baf6a787fdffd633537aa2eb51cfd54cb93ff08e28040095462bb63daf552878` |
| qwen2.5:1.5b | Q4_K_M / 1.5B | `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b` |
| qwen3:1.7b | Q4_K_M / 2.0B | `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7` |

Actual authorized-file footprint in D:\Ollama_Models: **3,666,459,306 bytes (3.67 GB; 3.41 GiB)**, including manifests and deduplicated referenced blobs. Unrelated cached models/files are excluded and preserved. Win32 reported the same file storage bytes. Models remain installed as authorized. The installer is separate (1662012016 bytes). API model digests and local manifest-file SHA256 values describe different representations; both are retained, not conflated.

**Scope correction to the earlier attempt:** the old zero-file probe inspected the default C: model directory, while the configured store is D:\Ollama_Models. The26 October attempt performed no pulls, so newly downloaded model bytes then were zero; that probe did not establish that all pre-existing caches on the laptop were empty. Do not repeat the broader zero-total-cache claim.

## Accuracy, languages and recommendation

| Language | Candidate safe / review cases across tasks | Model alone | Scanner + domain-rule composition |
| --- | --- | --- | --- |
| English | 8 / 8 | Not evaluated | Not evaluated |
| Hindi-English | 4 / 4 | Not evaluated | Not evaluated |
| roman Gujarati | 4 / 4 | Not evaluated | Not evaluated |
| Gujarati script | 4 / 4 | Not evaluated | Not evaluated |

No label freeze, accuracy confusion matrix, unsupported-language policy adoption or safety pass is claimed. The exact vetting-input open question is not silently answered by the provisional application-length timing stimuli. Prompt v1 was not revised; the separate development set was not run.

**Runtime recommendation:** retain native Ollama; CPU is a sufficient default for the short-call target and avoids depending on iGPU offload. Vulkan is viable on this machine but benefits are model-dependent: it helped Llama latency, while CPU was slightly faster for Qwen2.5/Qwen3 at concurrency1. **No final model recommendation yet.** Qwen2.5 is the smallest stored Apache-licensed candidate and fastest CPU candidate here; only a candidate that meets the frozen accuracy bar can be selected. Llama3.2 has its separate Community licence/attribution requirements; source links are in the original feasibility note.

**Proposed adapter settings, for T12 review:** concurrency cap1, bounded waiting queue2, end-to-end deadline8s including queue time. These are conservative engineering proposals informed by the measured short-call headroom, not approved product settings. Unknown production input lengths, vetting text and tunnel overhead still need checks. Queue overflow/timeout/unreachable/malformed is technical Withheld with retry or vetting NeedsReview; a model flag is under review/no same-text resend. Model output never clears scanner flags.

## Conditional estimates and freeze forecast

Implementation estimates below use verified runtime capabilities; milliseconds are not converted into developer sessions. Accuracy remediation and unresolved tunnel credit/provisioning are excluded from a false fixed promise.

| Ticket | Earlier sessions | Revised planning proposal | Reason |
| --- | --- | --- | --- |
| T7 Messages/moderation | 2-3 | **3-4** | New typed Withheld reasons, no-resend state, model-review queue and audited Admin release/discard add a cycle; hardware does not remove this policy work. |
| T12 Local-model adapter | Unvalidated | **2-3, conditional** | Stock native Windows runtime/schema/non-thinking/CPU are proven. Still need authenticated proxy, measured-limit wiring, fake failures, tunnel budget, real integration and accuracy. If no model passes, remediation/scope needs approval and this bound does not apply. |
| T13 Demo/evaluation | 2-3 | **2-3, conditional** | Runtime measurement exists, but deployed six-rule/live-model/tunnel/offline/under-review rehearsals and four-person evaluation remain. |

With T7 +1, remaining non-T12 work becomes21-33 sessions after T1. Holding the original T1 reservation (3-4), original0.5-session research allowance and both runtime-attempt reservations (one each), and moving one rehearsal session after freeze, optimistic build demand including conditional T12 is about **27.5-29.5 slots against25**: a **2.5-4.5-slot gap**, before accuracy remediation or other delays. These are conservative reservations/estimates, not certified actual effort; reconcile Parth's ledger before releasing any. Pretracking/clock gaps remain unverified. The plan does not fit on that conservative basis. Plan B already removes the optional scope; do not cut Admin, Reveal, Report handling or any rule. Additional capacity or a revised commitment needs Parth's decision. No later tickets published and no T2/T3 implementation started.

## Cleanup and reproducibility

Renewed runtime window12:53:42-14:53:42 UTC. CPU finished2026-10-27T14:04:07.866290+00:00; Vulkan finished2026-10-27T14:38:02.188822+00:00, before the deadline. Both owned servers were stopped. Final checks found no Ollama process, listener11434 or installer-created login shortcut. No tunnel/account/paid service/other model/software was provisioned. Later analysis, docs and checks are post-measurement bookkeeping; no inference continued.

Raw synthetic samples, summaries, sanitized placement logs, storage and hardware/cleanup evidence are in [the artifact directory](benchmarks/2026-10-27/). CPU harness commit9107385; Vulkan5b37359 (only difference: continue to the next model if offload is absent). The interrupted source/run is retained separately. The shared prompt digest is `04cdf9cafa770c929285aeb2ed8a4517858225af35e4b74b0accd4fd728b2ff2`. Current product tests/Rule5 coverage are separate from these experimental calls.

## Post-measurement client review

Standards review found two failure-path guards to tighten: a failed version probe did not establish port/listener ownership, and idle-read timeouts could be exceeded by a trickling response. Three ownership tests first failed behaviorally, then passed after exclusive-port/liveness/PID checks. Two fake-HTTP tests then failed (a2.5s stream budget took6.87s; an auxiliary timeout was not raised), then passed after absolute socket cancellation and propagation of the remaining block budget. Expected Windows connection-abort cleanup is handled by the fixture; assertions were retained. Five new tooling tests bring the full suite to406, with frozen T1 tests and rule coverage unchanged.

No new Ollama calls occurred during these fixes. Successful measured samples still refer to the original source commits above; they are not silently claimed to come from the later client transport. Current harness changes improve failure-path scope/reproducibility, not the recorded safety accuracy. Spec review found no mismatch; final guard review is recorded in the PR handoff.
