# Native Windows timing evidence

Read the [measured report](../../local-model-runtime-results-2026-10-27.md) first. All inputs are fixed synthetic timing stimuli, not the40-case safety evaluation. No model weights, secrets, provider credentials or real Member payloads are included.

- `cpu-summary.json` / `vulkan-summary.json`: fixed settings, prompt/model digests, metadata, cold and32-attempt warm samples for each concurrency, placement and ten-minute aggregate windows.
- Per-model `*-sustained.jsonl`: every sustained sample, including errors if any; output JSON validity is not a safety label.
- `comparison.json`: derived values, nearest-rank p95 and first/final-minute output-rate changes; raw metrics remain available.
- `*-placement.log`: whitelisted hardware/offload lines only; startup environment/proxy configuration is excluded.
- `storage.json`: only authorized manifests and their unique referenced blobs; unrelated cached files preserved.
- `hardware-cleanup.json`: actual OS/power snapshot and absence of Ollama process/listener/login shortcut after measurement.
- `interrupted-*`: initial CPU attempt excluded because setup had not completely exited; retained rather than overwritten or presented as accepted data.

GitHub collapses generated JSON/JSONL/log diffs by default through .gitattributes. Expand/download them to inspect all samples; this does not omit evidence. The hand-written report, protocol and harness remain visible for review. Cold-load cache and temperature limitations are stated in the report. No accuracy, final model choice or implemented moderation delivery is claimed.
