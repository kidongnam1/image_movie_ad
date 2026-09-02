import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator"))
import media_render_v1 as mr


def make_package(root: Path):
    project = root / "demo_project"
    variant = project / "ugc"
    variant.mkdir(parents=True)
    (project / "project.json").write_text(json.dumps({
        "project_id": "demo_project", "product_name": "세럼", "duration_sec": 30,
        "aspect_ratio": "9:16", "language": "ko-KR"
    }, ensure_ascii=False), encoding="utf-8")
    (project / "manifest.json").write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    (project / "creative_scores.json").write_text(json.dumps({"recommended_variant": "ugc"}), encoding="utf-8")
    shots = []
    images = []
    videos = []
    for i in range(1, 8):
        shots.append({"scene_no": i, "start_sec": i - 1, "end_sec": i, "duration_sec": 1})
        images.append({"scene_no": i, "prompt": f"image {i}"})
        videos.append({"scene_no": i, "prompt": f"video {i}"})
    (variant / "shot_list.json").write_text(json.dumps(shots), encoding="utf-8")
    (variant / "image_prompts.json").write_text(json.dumps(images), encoding="utf-8")
    (variant / "video_prompts.json").write_text(json.dumps({"kling": videos}), encoding="utf-8")
    (variant / "voiceover.txt").write_text("voiceover", encoding="utf-8")
    (variant / "subtitles.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\n테스트\n", encoding="utf-8")
    return project


class MediaRenderV1Tests(unittest.TestCase):
    def test_load_and_plan(self):
        with tempfile.TemporaryDirectory() as td:
            project = make_package(Path(td))
            package = mr.load_package(project, "recommended")
            plan = mr.build_render_plan(package, "kling")
            self.assertEqual(plan["variant"], "ugc")
            self.assertEqual(len(plan["scenes"]), 7)
            self.assertTrue(plan["paths"]["final_output"].endswith("ugc_ad_30s.mp4"))

    def test_export_requests(self):
        with tempfile.TemporaryDirectory() as td:
            project = make_package(Path(td))
            package = mr.load_package(project, "ugc")
            plan = mr.build_render_plan(package, "kling")
            paths = mr.export_provider_requests(project, plan, package)
            self.assertEqual(len(paths), 3)
            video = json.loads(paths[1].read_text(encoding="utf-8"))
            self.assertEqual(len(video), 7)
            self.assertEqual(video[0]["model"], "kling")

    def test_readiness_reports_missing_assets(self):
        with tempfile.TemporaryDirectory() as td:
            project = make_package(Path(td))
            package = mr.load_package(project, "ugc")
            plan = mr.build_render_plan(package, "kling")
            readiness = mr.build_readiness(project, plan, ffmpeg_bin="definitely_missing_ffmpeg_binary")
            self.assertFalse(readiness["ffmpeg_ready"])
            self.assertEqual(len(readiness["missing_scene_videos"]), 7)
            self.assertFalse(readiness["ready_to_render"])

    def test_prepare_writes_plan_and_readiness(self):
        with tempfile.TemporaryDirectory() as td:
            project = make_package(Path(td))
            result = mr.prepare_media_render(project, "recommended", "kling", "definitely_missing_ffmpeg_binary")
            self.assertTrue((project / "render_plan.json").exists())
            self.assertTrue((project / "render_readiness.json").exists())
            self.assertFalse(result["readiness"]["ready_to_render"])


if __name__ == "__main__":
    unittest.main()
