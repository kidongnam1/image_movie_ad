import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator"))
import creative_package_v1 as cp


def fake_legacy_generate(product):
    cats = ["problem", "demo", "curiosity"]
    hooks = []
    for i in range(30):
        hooks.append({
            "rank": i + 1,
            "text": f"{product} 테스트 훅 {i + 1}",
            "category": cats[i % 3],
            "score": 90 - i / 10,
            "risk": 0,
            "db_source_id": i + 1,
            "db_hook_id": i + 1,
        })
    return {
        "product": product,
        "db_integration": {
            "connected": True,
            "database": "fake.sqlite",
            "counts": {"sources": 377, "viral_hooks": 1355},
            "commercial_policy": "COMMERCIAL_OK + TRANSFORM_ONLY only",
            "selected_references": {},
            "hook_reference_ids": [
                {"hook_id": 1, "source_id": 1, "category": "problem"},
                {"hook_id": 2, "source_id": 2, "category": "demo"},
                {"hook_id": 3, "source_id": 3, "category": "curiosity"},
            ],
            "top3_diversity": {"unique_hook_ids": 3, "unique_categories": 3},
        },
        "hooks": hooks,
        "top3": hooks[:3],
        "script_30s": [],
        "cta": "제품 정보와 사용법을 확인해보세요.",
        "video_prompts": {},
    }


class CreativePackageV1Tests(unittest.TestCase):
    def test_project_validation(self):
        with self.assertRaises(ValueError):
            cp.build_project_config("")
        with self.assertRaises(ValueError):
            cp.build_project_config("세럼", duration_sec=20)
        config = cp.build_project_config("세럼", duration_sec=30, project_id="test_project")
        self.assertEqual(config.project_id, "test_project")

    def test_timeline_is_contiguous(self):
        timeline = cp.allocate_timeline(30, 7)
        self.assertEqual(timeline[0][0], 0)
        self.assertEqual(timeline[-1][1], 30)
        for prev, cur in zip(timeline, timeline[1:]):
            self.assertEqual(prev[1], cur[0])
            self.assertGreater(prev[1], prev[0])

    @patch.object(cp.legacy, "generate", side_effect=fake_legacy_generate)
    def test_end_to_end_package(self, _mock_generate):
        config = cp.build_project_config(
            "세럼", "탄력과 보습을 위한 데일리 세럼", "40~60대 여성", 30, project_id="serum_test"
        )
        with tempfile.TemporaryDirectory() as td:
            out = cp.generate_package(config, Path(td), require_db=True)
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "PASS")
            self.assertEqual(manifest["compliance_status"], "PASS")
            for variant in cp.VARIANTS:
                shot = json.loads((out / variant / "shot_list.json").read_text(encoding="utf-8"))
                self.assertEqual(len(shot), 7)
                self.assertEqual(shot[0]["start_sec"], 0)
                self.assertEqual(shot[-1]["end_sec"], 30)
                self.assertTrue((out / variant / "image_prompts.json").exists())
                self.assertTrue((out / variant / "video_prompts.json").exists())
                self.assertTrue((out / variant / "subtitles.srt").exists())
            scores = json.loads((out / "creative_scores.json").read_text(encoding="utf-8"))
            self.assertIn(scores["recommended_variant"], cp.VARIANTS)

    @patch.object(cp.legacy, "generate", side_effect=fake_legacy_generate)
    def test_non_beauty_package_does_not_fall_back_to_skincare(self, _mock_generate):
        config = cp.build_project_config(
            "골프 거리측정기",
            target_audience="40~60대 골퍼",
            duration_sec=30,
            project_id="golf_test",
            must_emphasize="0.2초 측정",
            pain_point="거리 판단이 늦어 샷 템포가 끊기는 문제",
            intensity=4,
        )
        with tempfile.TemporaryDirectory() as td:
            out = cp.generate_package(config, Path(td), require_db=True)
            project = json.loads((out / "project.json").read_text(encoding="utf-8"))
            self.assertEqual(project["product_analysis"]["category"], "golf")
            self.assertEqual(project["product_analysis"]["primary_selling_point"], "0.2초 측정")
            for variant in cp.VARIANTS:
                script = (out / variant / "script.md").read_text(encoding="utf-8")
                image_prompts = (out / variant / "image_prompts.json").read_text(encoding="utf-8").lower()
                video_prompts = (out / variant / "video_prompts.json").read_text(encoding="utf-8").lower()
                self.assertNotIn("피부", script)
                self.assertNotIn("제형", script)
                self.assertNotIn("korean beauty", image_prompts)
                self.assertNotIn("korean beauty", video_prompts)

    def test_claim_gate_blocks(self):
        variants = {
            "ugc": {"scenes": [{"spoken": "100% 치료", "caption": "", "visual": ""}]},
        }
        report = cp.build_compliance_report(variants)
        self.assertEqual(report["status"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
