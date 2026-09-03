import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator"))
import creative_package_v26 as cp26


class CreativePackageV26Tests(unittest.TestCase):
    def test_augment_package_writes_learning_sidecars(self):
        generated = {
            "version": "2.6",
            "performance_learning": {
                "active": True,
                "total_rows": 3,
                "total_impressions": 30000,
                "angle_adjustments": {"problem_attack": 3.2, "comparison": -2.1},
            },
            "experiment_plan": {
                "candidates": [
                    {"slot": "A", "angle_label": "문제공격형", "creative_id": "CR-AAA", "hook": "강한 훅", "traffic_share_pct": 40, "minimum_impressions": 1000},
                    {"slot": "B", "angle_label": "호기심형", "creative_id": "CR-BBB", "hook": "호기심 훅", "traffic_share_pct": 30, "minimum_impressions": 1000},
                    {"slot": "C", "angle_label": "손실회피형", "creative_id": "CR-CCC", "hook": "손실 훅", "traffic_share_pct": 30, "minimum_impressions": 1000},
                ]
            },
        }
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "project.json").write_text(json.dumps({"project_id": "x"}), encoding="utf-8")
            (p / "strategy.md").write_text("# 전략\n", encoding="utf-8")
            (p / "manifest.json").write_text(json.dumps({"generated_files": []}), encoding="utf-8")
            cp26.augment_package(p, generated)
            self.assertTrue((p / "performance_learning.json").exists())
            self.assertTrue((p / "experiment_plan.json").exists())
            project = json.loads((p / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(project["script_generator_version"], "2.6")
            self.assertEqual(len(project["experiment_plan"]["candidates"]), 3)
            strategy = (p / "strategy.md").read_text(encoding="utf-8")
            self.assertIn("CR-AAA", strategy)
            manifest = json.loads((p / "manifest.json").read_text(encoding="utf-8"))
            self.assertIn("performance_learning.json", manifest["generated_files"])
            self.assertEqual(manifest["milestone"], "CREATIVE_PACKAGE_V26_PERFORMANCE_LEARNING")


if __name__ == "__main__":
    unittest.main()
