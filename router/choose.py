"""Budget-aware image model selection from a local, dated catalog.

This module deliberately has no network or billing side effects.  A caller must
refresh a catalog separately, review it, and pass the resulting JSON file here.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
from typing import Any

SUPPORTED_MODELS = ("nano-banana-2", "gpt-image-2")
QUALITY_PREFERENCE = {
    "low": ("nano-banana-2", "gpt-image-2"),
    "medium": ("nano-banana-2", "gpt-image-2"),
    "high": ("gpt-image-2", "nano-banana-2"),
}


def resolution_tier(width: int, height: int) -> str:
    """Map requested pixels to the billing tier used by the live catalog."""
    if not isinstance(width, int) or not isinstance(height, int):
        raise ValueError("width and height must be integers")
    if width < 1 or height < 1:
        raise ValueError("width and height must be positive")
    longest_edge = max(width, height)
    if longest_edge <= 1024:
        return "1k"
    if longest_edge <= 2048:
        return "2k"
    if longest_edge <= 4096:
        return "4k"
    raise ValueError("the selector supports output dimensions up to 4096 pixels")


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip().replace("$", ""))
        except ValueError:
            return None
    else:
        return None
    return number if math.isfinite(number) and number >= 0 else None


def _tier_price(model: dict[str, Any], tier: str) -> float | None:
    pricing = model.get("pricing", {}).get("effective", {})
    tiers = pricing.get("tiers", [])
    if isinstance(tiers, list):
        wanted = tier.replace("k", "K")
        for row in tiers:
            if not isinstance(row, dict):
                continue
            label = str(row.get("label", "")).replace(" ", "").lower()
            if label in {tier.lower(), wanted.lower()}:
                return _number(row.get("price"))
    # Older local catalogs may use a flat map; retain a narrow compatibility path.
    for key in (tier, f"image_{tier}", f"image_{tier.lower()}"):
        price = _number(pricing.get(key))
        if price is not None:
            return price
    return _number(pricing.get("generation_per_unit")) if tier == "1k" else None


def _models(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    rows = catalog.get("models")
    if not isinstance(rows, list):
        raise ValueError("catalog must contain a models list")
    return [row for row in rows if isinstance(row, dict)]


def choose(catalog: dict[str, Any], width: int, height: int, quality: str, budget: float) -> dict[str, Any]:
    """Return the best supported candidate without making an API request."""
    if quality not in QUALITY_PREFERENCE:
        raise ValueError("quality must be one of low, medium, or high")
    if not isinstance(budget, (int, float)) or not math.isfinite(float(budget)) or budget < 0:
        raise ValueError("budget must be a finite non-negative USD amount")
    tier = resolution_tier(width, height)
    preference = {model_id: rank for rank, model_id in enumerate(QUALITY_PREFERENCE[quality])}
    candidates: list[tuple[int, float, str, dict[str, Any]]] = []
    for model in _models(catalog):
        model_id = str(model.get("id", ""))
        if model_id not in SUPPORTED_MODELS or model.get("category") not in {None, "image"}:
            continue
        declared = {str(item).lower() for item in model.get("image", {}).get("resolutions", [])}
        if declared and tier not in declared:
            continue
        price = _tier_price(model, tier)
        if price is None or price > float(budget):
            continue
        candidates.append((preference[model_id], price, model_id, model))
    if not candidates:
        raise ValueError(f"no supported image model provides {tier} within a ${float(budget):.4f} budget")
    candidates.sort(key=lambda row: (row[0], row[1], row[2]))
    rank, price, model_id, model = candidates[0]
    return {
        "model": model_id,
        "display_name": model.get("display_name", model_id),
        "tier": tier,
        "estimated_usd": price,
        "width": width,
        "height": height,
        "quality": quality,
        "budget_usd": float(budget),
        "selection": "quality preference, then lowest catalog price",
        "catalog_revision": catalog.get("generated_at") or catalog.get("retrieved_at"),
    }


def load_catalog(path: pathlib.Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read catalog {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("catalog root must be a JSON object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Select an image model from a local catalog (never submits a request).")
    parser.add_argument("--catalog", required=True, type=pathlib.Path)
    parser.add_argument("--width", required=True, type=int)
    parser.add_argument("--height", required=True, type=int)
    parser.add_argument("--quality", choices=tuple(QUALITY_PREFERENCE), default="medium")
    parser.add_argument("--budget", required=True, type=float, help="maximum USD per returned image")
    parser.add_argument("--dry-run", action="store_true", help="required acknowledgement that no request will be sent")
    args = parser.parse_args()
    if not args.dry_run:
        parser.error("--dry-run is required; this CLI never sends a billable request")
    print(json.dumps(choose(load_catalog(args.catalog), args.width, args.height, args.quality, args.budget), indent=2))


if __name__ == "__main__":
    main()
