import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generator"))
import performance_store_v26 as store
import script_generator_v27 as v27

FAKE={
    "version":"2.6","product":"골프 거리측정기","product_analysis":{"category":"golf"},
    "experiment_plan":{"candidates":[
        {"slot":"A","creative_id":"CR-111111111111","angle":"problem_attack","angle_label":"문제공격형","hook":"hook A","selling_point":"0.2초 측정"},
        {"slot":"B","creative_id":"CR-222222222222","angle":"curiosity","angle_label":"호기심형","hook":"hook B","selling_point":"0.2초 측정"},
        {"slot":"C","creative_id":"CR-333333333333","angle":"comparison","angle_label":"비교형","hook":"hook C","selling_point":"0.2초 측정"},
    ]},
}

class ScriptGeneratorV27Tests(unittest.TestCase):
    def test_generate_registers_abc_creatives(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"perf.sqlite"
            with patch.object(v27.core,"generate",return_value=dict(FAKE)):
                d=v27.generate("골프 거리측정기",performance_db=db)
            self.assertEqual(d["version"],"2.7")
            self.assertEqual(d["creative_registry"]["registered_candidates"],3)
            c=store.connect(db);rows=c.execute("SELECT creative_id,product,angle FROM creative_registry ORDER BY creative_id").fetchall();c.close()
            self.assertEqual(len(rows),3)
            self.assertEqual(rows[0]["product"],"골프 거리측정기")

if __name__=="__main__":unittest.main()
