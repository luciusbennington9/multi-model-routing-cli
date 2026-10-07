# Multi-model image routing CLI

This Python standard-library CLI chooses an image model from a supplied catalog by size, quality preference, and a USD budget. **ArgoLink is used only when its catalog URL is supplied; the chooser is provider-neutral.** The important behavior is dry-run selection, not a hidden network call. Last checked: 2026-10-07.

## Why a catalog input

Model names and effective prices are data, not constants. The CLI reads catalog JSON and ignores a model when it has no numeric effective image price. That makes a stale price visible instead of silently choosing a model. The sample selection recognises Nano Banana and gpt-image IDs, but this is a conservative filter, not a claim that every alias is interchangeable. Extend it only after reading a live catalog.

## Run

python3 -m router.choose --catalog catalog.json --width 1024 --height 1024 --quality high --budget 0.05 --dry-run

A catalog row uses models, pricing.effective, and an image tier such as 2k. If the service publishes a different field, add an explicit adapter and test it. The CLI does not fetch catalog data and does not submit an image request; that separation keeps dry-run safe. An execution layer can use the selected ID after the operator reviews the result.

## Decision rule

The filter first requires a known image-like ID and a numeric tier under budget. High quality prefers a Pro-named candidate if it remains within budget; otherwise the lowest numeric rate wins. Width and height are retained in the output for the downstream validator. The tool does not infer that a 2k price means a specific pixel dimension or that quality names match across providers.

## Operational checklist

Refresh the catalog before a batch. Record the catalog revision, selected model, dimensions, quality, and estimate in the job manifest. Check the model page for accepted size, reference count, output encoding, and content policy. Apply a concurrency limit in the executor. Failed jobs and ambiguous POST outcomes need explicit provider handling; do not wrap this safe selector in an automatic retry that submits again.

## Tests and limitations

python3 -m unittest discover -s tests runs without network access. The test proves a budgeted selection from a local fixture. This repository deliberately does not implement API-key loading, image upload, or billing. Add those in a separate, reviewed executor using a neutral API key and a User-Agent on every request.

## FAQ

**Does dry-run call a model?** No. It only reads the provided JSON. **Why was a model skipped?** It had no numeric effective image rate or did not match the conservative filter. **Can I route video?** No; video has a different async lifecycle and billing formula. **Are cheapest images always best?** No; quality, references, and output requirements matter. **Can I use an old catalog?** Only if you label its date and accept that the result is historical.
