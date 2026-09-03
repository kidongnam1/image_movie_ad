import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "generator"))
import ad_performance_learning as perf


class AdPerformanceLearningTests(unittest.TestCase):
    def _make_csv(self, path: Path, a_impressions=10000, a_clicks=600):
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(perf.TEMPLATE_FIELDS)
            w.writerow(["2026-09-01", "C1", "A1", "골프 거리측정기", "golf", "meta", "problem_attack", "hook A", "0.2초 측정", a_impressions, 9000, 8000, 6500, a_clicks, 500, 60, 3000000, 1000000])
            w.writerow(["2026-09-01", "C1", "B1", "골프 거리측정기", "golf", "meta", "comparison", "hook B", "0.2초 측정", 10000, 9000, 5500, 4000, 250, 200, 10, 400000, 1000000])
            w.writerow(["2026-09-01", "C1", "C1", "골프 거리측정기", "golf", "meta", "curiosity", "hook C", "0.2초 측정", 10000, 9000, 7000, 5500, 450, 350, 35, 1800000, 1000000])

    def test_import_dedupe_and_directional_learning(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "perf.csv"
            db_path = Path(td) / "perf.sqlite"
            self._make_csv(csv_path)
            first = perf.import_file(csv_path, db_path)
            second = perf.import_file(csv_path, db_path)
            self.assertEqual(first["inserted"], 3)
            self.assertEqual(second["duplicates_skipped"], 3)
            self.assertEqual(second["updated"], 0)
            profile = perf.build_learning_profile("golf", db_path)
            self.assertTrue(profile["active"])
            self.assertGreater(profile["angle_adjustments"]["problem_attack"], 0)
            self.assertLess(profile["angle_adjustments"]["comparison"], 0)
            self.assertGreater(profile["hook_adjustments"]["hook A"], 0)
            self.assertLess(profile["hook_adjustments"]["hook B"], 0)
            self.assertGreater(profile["creative_adjustments"]["A1"], 0)
            self.assertLess(profile["creative_adjustments"]["B1"], 0)
            self.assertLessEqual(abs(profile["angle_adjustments"]["problem_attack"]), 6)
            self.assertLessEqual(abs(profile["hook_adjustments"]["hook A"]), 3)
            self.assertLessEqual(abs(profile["creative_adjustments"]["A1"]), 2)
            self.assertEqual(profile["total_impressions"], 30000)

    def test_refreshed_snapshot_updates_instead_of_double_counting(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "perf.csv"
            db_path = Path(td) / "perf.sqlite"
            self._make_csv(csv_path)
            perf.import_file(csv_path, db_path)
            self._make_csv(csv_path, a_impressions=12000, a_clicks=720)
            result = perf.import_file(csv_path, db_path)
            self.assertEqual(result["updated"], 1)
            self.assertEqual(result["duplicates_skipped"], 2)
            self.assertEqual(result["database_rows"], 3)
            profile = perf.build_learning_profile("golf", db_path)
            self.assertEqual(profile["total_impressions"], 32000)

    def test_invalid_funnel_row_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "bad.csv"
            db_path = Path(td) / "perf.sqlite"
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(perf.TEMPLATE_FIELDS)
                w.writerow(["2026-09-01", "C1", "A1", "청소기", "home_appliance", "meta", "problem_attack", "hook", "흡입력", 100, 100, 120, 80, 10, 8, 1, 10000, 5000])
            result = perf.import_file(csv_path, db_path)
            self.assertEqual(result["inserted"], 0)
            self.assertEqual(result["errors"], 1)

    def test_tiny_sample_is_shrunk(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "perf.sqlite"
            csv_path = Path(td) / "tiny.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(perf.TEMPLATE_FIELDS)
                w.writerow(["2026-09-01", "C", "A", "청소기", "home_appliance", "meta", "problem_attack", "hook", "흡입력", 20, 20, 20, 20, 10, 10, 5, 100000, 10000])
                w.writerow(["2026-09-01", "C", "B", "청소기", "home_appliance", "meta", "comparison", "hook", "흡입력", 20, 20, 5, 4, 1, 1, 0, 0, 10000])
            perf.import_file(csv_path, db_path)
            profile = perf.build_learning_profile("home_appliance", db_path)
            self.assertLess(abs(profile["angle_adjustments"]["problem_attack"]), 1.0)
            self.assertEqual(profile["hook_adjustments"]["hook"], 0.0)
            self.assertEqual(profile["creative_adjustments"]["A"], 0.0)


if __name__ == "__main__":
    unittest.main()
