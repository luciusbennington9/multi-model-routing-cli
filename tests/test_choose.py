import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))
from router.choose import choose, resolution_tier


def row(model_id, prices, resolutions=None):
    return {
        "id": model_id,
        "category": "image",
        "display_name": model_id.title(),
        "image": {"resolutions": resolutions or ["1k", "2k", "4k"]},
        "pricing": {"effective": {"tiers": [{"label": k.upper(), "price": v} for k, v in prices.items()]}},
    }


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {"generated_at": "2026-10-07", "models": [
            row("nano-banana-2", {"1k": .02, "2k": .02, "4k": .025}),
            row("gpt-image-2", {"1k": .015, "2k": .015, "4k": .02}),
            row("seedance-2.5", {"1k": .1}),
        ]}

    def test_tier_boundaries(self):
        self.assertEqual(resolution_tier(1024, 768), "1k")
        self.assertEqual(resolution_tier(2048, 1025), "2k")
        self.assertEqual(resolution_tier(4096, 2160), "4k")

    def test_high_quality_prefers_gpt_even_when_nano_is_cheaper(self):
        result = choose(self.catalog, 1024, 1024, "high", .03)
        self.assertEqual(result["model"], "gpt-image-2")
        self.assertEqual(result["tier"], "1k")

    def test_budget_falls_back_to_nano(self):
        result = choose(self.catalog, 2048, 1152, "high", .016)
        self.assertEqual(result["model"], "gpt-image-2")
        with self.assertRaises(ValueError):
            choose(self.catalog, 4096, 2160, "high", .01)

    def test_unsupported_resolution_and_bad_input(self):
        self.assertEqual(choose(self.catalog, 1024, 1024, "medium", .02)["model"], "nano-banana-2")
        with self.assertRaises(ValueError):
            resolution_tier(0, 1024)
        with self.assertRaises(ValueError):
            resolution_tier(5000, 1024)

    def test_unknown_rows_are_ignored(self):
        with self.assertRaises(ValueError):
            choose({"models": [row("unlisted-model", {"1k": .001})]}, 512, 512, "low", .01)


if __name__ == "__main__":
    unittest.main()
