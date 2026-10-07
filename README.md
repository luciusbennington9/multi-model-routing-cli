# Multi-model image routing CLI

This small Python standard-library CLI makes a **dry-run** image-model decision from a local, dated catalog. It is a selection component, not a gateway and not a request executor: it never reads an API key, uploads an image, or sends a billable request. The two deliberately supported choices are the live catalog IDs `nano-banana-2` and `gpt-image-2`.

## Why a local catalog matters

Prices and capabilities belong to the catalog, not to source-code constants. Refresh the catalog through the public model-list route (`GET https://argolink.io/v1/models`) in a separately reviewed process, save the JSON with its retrieval time, then pass that file to this command. The selector reads `models[].id`, `models[].category`, `models[].image.resolutions`, and `models[].pricing.effective.tiers`. A tier is ignored when its price is missing or non-numeric, so a stale or incomplete file fails closed instead of silently inventing a rate.

The live 2026-10-07 catalog records these effective rates per returned image:

| Model | 1K | 2K | 4K | Reference-image route |
| --- | ---: | ---: | ---: | --- |
| `nano-banana-2` | $0.020 | $0.020 | $0.025 | `POST /v1/images/edits`, up to 14 references |
| `gpt-image-2` | $0.015 | $0.015 | $0.020 | `POST /v1/images/edits`, up to 16 references |

The table is a snapshot, not a promise that future prices stay the same. Check the catalog revision and model page before a production decision.

## Selection rule

1. The longest requested edge maps to a tier: up to 1024 pixels is `1k`, 1025–2048 is `2k`, and 2049–4096 is `4k`. Larger requests are rejected so an unverified tier cannot slip through.
2. Only the two explicit model IDs above are candidates. Other image, video, or provider rows are ignored.
3. Candidates must declare the requested tier and have a numeric effective price no greater than `--budget`.
4. `high` prefers `gpt-image-2`; `low` and `medium` prefer `nano-banana-2`. If that preference is unavailable within budget, the other supported model can be selected. Price then breaks ties.
5. The output records the model, tier, dimensions, budget, estimate, and catalog revision for a job manifest.

“Quality” is a routing preference, not a claim that either model is universally better. Both model pages remain the source of truth for output pixels, reference limits, safety rules, and accepted parameters.

## Run a safe decision

```bash
python3 -m router.choose \
  --catalog catalog-2026-10-07.json \
  --width 2048 --height 1152 \
  --quality high --budget 0.02 --dry-run
```

Example output:

```json
{
  "model": "gpt-image-2",
  "display_name": "GPT Image 2",
  "tier": "2k",
  "estimated_usd": 0.015,
  "width": 2048,
  "height": 1152,
  "quality": "high",
  "budget_usd": 0.02,
  "selection": "quality preference, then lowest catalog price",
  "catalog_revision": "2026-10-07"
}
```

`--dry-run` is mandatory as a visible acknowledgement. There is no execution mode in this repository. A separate application may consume the selected ID only after reviewing the manifest, validating the model page, and applying its own idempotency and billing controls.

## Catalog shape

A minimal local fixture looks like this:

```json
{
  "generated_at": "2026-10-07",
  "models": [
    {
      "id": "gpt-image-2",
      "category": "image",
      "image": {"resolutions": ["1k", "2k", "4k"]},
      "pricing": {"effective": {"tiers": [
        {"label": "1K", "price": 0.015},
        {"label": "2K", "price": 0.015},
        {"label": "4K", "price": 0.02}
      ]}}
    }
  ]
}
```

Do not paste API keys into this file or commit production response payloads. Keep catalog snapshots separate from secrets and label their retrieval date.

## Tests and boundaries

```bash
python3 -m unittest discover -s tests -v
```

Tests are offline and cover tier boundaries, quality preference, budget failure, invalid dimensions, and unknown catalog rows. The selector does not implement retries, uploads, image editing, or a chat/video route. Those behaviors have different contracts and belong in reviewed clients that use `https://argolink.io/v1` and send a descriptive `User-Agent` on every request.
