import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generator import script_generator_v2 as gen


CASES = [
    ("세럼", "끈적임 적음|빠른 흡수감", "가벼운 제형|데일리 사용", "30~50대 여성", "beauty"),
    ("골프 거리측정기", "0.2초 측정|손떨림 보정", "800m 측정|150g 초경량", "40~60대 골퍼", "golf"),
    ("무선 청소기", "18,000Pa 흡입력|480g 초경량", "USB-C 충전|25분 사용", "차량/집 청소 사용자", "home_appliance"),
    ("여행용 캐리어", "저소음 바퀴|확장 수납", "TSA 잠금|경량 바디", "해외 여행자", "travel"),
    ("고양이 자동급식기", "정량 급여|앱 원격급여", "급여 기록|분리세척", "고양이 보호자", "pet"),
]


class ScriptGeneratorV25Tests(unittest.TestCase):
    def test_five_product_category_and_quality_regression(self):
        for product, must, features, target, category in CASES:
            with self.subTest(product=product):
                data = gen.generate(
                    product,
                    must_emphasize=must,
                    features=features,
                    target=target,
                    intensity=5,
                )
                self.assertEqual(data["version"], "2.5")
                self.assertEqual(data["product_analysis"]["category"], category)
                self.assertEqual(len(data["hooks"]), 30)
                self.assertGreaterEqual(min(x["score"] for x in data["hooks"]), 84.0)
                self.assertEqual(data["quality_audit"]["generic_hook_hits"], 0)
                self.assertEqual(data["quality_audit"]["banned_hook_hits"], 0)
                self.assertTrue(data["quality_audit"]["category_neutral"])

                primary = data["product_analysis"]["primary_selling_point"]
                self.assertIn(primary, data["top3"][0]["text"])
                self.assertEqual(data["quality_audit"]["must_emphasize_coverage"]["30s"], 100.0)
                self.assertEqual(data["quality_audit"]["must_emphasize_coverage"]["45s"], 100.0)

                script_text = " ".join(x["spoken"] for x in data["script_30s"])
                for bad in ("보정가", "흡입력와", "수납가", "급여가", "적음와", "세럼는", "측정였습니다"):
                    self.assertNotIn(bad, script_text)

    def test_intensity_five_has_stronger_first_two_seconds(self):
        low = gen.generate("골프 거리측정기", must_emphasize="0.2초 측정", intensity=2)
        high = gen.generate("골프 거리측정기", must_emphasize="0.2초 측정", intensity=5)
        self.assertGreater(high["top3"][0]["first_2s_power"], low["top3"][0]["first_2s_power"])
        self.assertGreaterEqual(high["ad_settings"]["minimum_score"], 84.0)

    def test_numeric_comma_feature_is_not_split(self):
        data = gen.generate("무선 청소기", must_emphasize="18,000Pa 흡입력|480g 초경량", intensity=5)
        self.assertEqual(data["product_analysis"]["must_emphasize"][0], "18,000Pa 흡입력")
        self.assertIn("18,000Pa 흡입력", data["top3"][0]["text"])


if __name__ == "__main__":
    unittest.main()
