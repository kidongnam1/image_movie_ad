import csv
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator"))
import ad_performance_learning as perf
import script_generator_v26 as v26


def fake_base(product, **kwargs):
    pc = {
        "product": product,
        "category": "golf",
        "category_label": "골프",
        "target": "40~60대 골퍼",
        "pain_point": "거리 판단이 늦어 샷 템포가 끊기는 상황",
        "must_emphasize": ["0.2초 측정", "손떨림 보정"],
        "features": ["800m 측정"],
        "selling_points": ["0.2초 측정", "손떨림 보정", "800m 측정"],
        "primary_selling_point": "0.2초 측정",
        "secondary_selling_points": ["손떨림 보정", "800m 측정"],
        "demo_action": "실제 측정 장면",
        "proof_action": "같은 지점을 반복 측정",
        "environment": "golf course",
        "buyer_motive": "판단 시간을 줄이는 것",
        "stake": "샷 흐름을 놓치는 것",
        "claim_verification_required": True,
        "emphasis_strategy": {},
    }
    angles = ["problem_attack", "comparison", "curiosity", "loss_aversion", "contrarian", "discovery", "proof"]
    hooks = []
    for i in range(30):
        angle = angles[i % len(angles)]
        hooks.append(asdict(v26.core.Hook(
            i + 1, f"{angle} hook {i} 0.2초 측정", angle, angle,
            90.0, 94.0, 93.0, 90.0, 92.0, 94.0, 95.0, 0.0,
            90.0, 92.0, 94.0, 94.0, 90.0, 0.0, None, None,
        )))
    competition = []
    for angle in ["problem_attack", "comparison", "curiosity", "loss_aversion", "contrarian"]:
        competition.append({
            "copywriter": angle,
            "angle": angle,
            "angle_label": angle,
            "hook": next(h for h in hooks if h["angle"] == angle),
            "script_30s": [],
            "scores": {"total": 90.0, "first_2s_power": 94.0},
            "qualified": True,
        })
    return {
        "version": "2.5",
        "product": product,
        "product_analysis": pc,
        "ad_settings": {"intensity": kwargs.get("intensity", 4), "minimum_score": 84.0},
        "quality_audit": {},
        "db_integration": {"connected": True},
        "hooks": hooks,
        "top3": hooks[:3],
        "creative_competition": competition,
        "winner": {"angle": "comparison", "scores": {"total": 90.0}},
        "scripts_by_duration": {}, "script_15s": [], "script_30s": [], "script_45s": [],
        "cta": "cta", "video_prompts_by_duration": {}, "video_prompts": {}, "claim_note": "note",
    }


def fake_build_script(pc, hook, duration, angle, intensity):
    return [
        {"time": "0-2s", "role": "HOOK", "spoken": hook.text, "onscreen": hook.text, "visual": "v", "angle": angle},
        {"time": "2-20s", "role": "PROOF", "spoken": "0.2초 측정 손떨림 보정", "onscreen": "0.2초 측정", "visual": "v", "angle": angle},
        {"time": "20-30s", "role": "CTA", "spoken": "cta", "onscreen": "cta", "visual": "v", "angle": angle},
    ]


class ScriptGeneratorV26Tests(unittest.TestCase):
    @patch.object(v26.core, "generate", side_effect=fake_base)
    @patch.object(v26.core, "build_script", side_effect=fake_build_script)
    @patch.object(v26.core, "emphasis_coverage", return_value=100.0)
    @patch.object(v26.core, "prompt", side_effect=lambda model, pc, beat: f"{model}:{beat['role']}")
    @patch.object(v26.core, "cta", return_value="cta")
    def test_learning_promotes_winning_angle_and_builds_abc(self, *_mocks):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "perf.sqlite"
            csv_path = Path(td) / "perf.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(perf.TEMPLATE_FIELDS)
                w.writerow(["2026-09-01", "C", "A", "골프 거리측정기", "golf", "meta", "problem_attack", "hA", "0.2초 측정", 10000, 9000, 8000, 6500, 600, 500, 60, 3000000, 1000000])
                w.writerow(["2026-09-01", "C", "B", "골프 거리측정기", "golf", "meta", "comparison", "hB", "0.2초 측정", 10000, 9000, 5000, 3500, 200, 150, 5, 200000, 1000000])
            data = v26.generate("골프 거리측정기", performance_db=db, performance_file=csv_path)
            self.assertEqual(data["version"], "2.6")
            self.assertTrue(data["performance_learning"]["active"])
            self.assertGreater(data["performance_learning"]["angle_adjustments"]["problem_attack"], 0)
            self.assertLess(data["performance_learning"]["angle_adjustments"]["comparison"], 0)
            self.assertEqual(data["winner"]["angle"], "problem_attack")
            self.assertEqual(len(data["experiment_plan"]["candidates"]), 3)
            self.assertEqual([c["traffic_share_pct"] for c in data["experiment_plan"]["candidates"]], [40, 30, 30])
            self.assertTrue(all(c["creative_id"].startswith("CR-") for c in data["experiment_plan"]["candidates"]))

    @patch.object(v26.core, "generate", side_effect=fake_base)
    @patch.object(v26.core, "build_script", side_effect=fake_build_script)
    @patch.object(v26.core, "emphasis_coverage", return_value=100.0)
    @patch.object(v26.core, "prompt", side_effect=lambda model, pc, beat: f"{model}:{beat['role']}")
    @patch.object(v26.core, "cta", return_value="cta")
    def test_cold_start_keeps_learning_neutral(self, *_mocks):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "empty.sqlite"
            data = v26.generate("골프 거리측정기", performance_db=db)
            self.assertFalse(data["performance_learning"]["active"])
            self.assertTrue(all(v == 0 for v in data["performance_learning"]["angle_adjustments"].values()))
            self.assertEqual([c["traffic_share_pct"] for c in data["experiment_plan"]["candidates"]], [34, 33, 33])


if __name__ == "__main__":
    unittest.main()
