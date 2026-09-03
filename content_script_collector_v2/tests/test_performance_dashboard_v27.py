import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generator"))
import performance_store_v26 as store
import performance_dashboard_v27 as dashboard

class DashboardV27Tests(unittest.TestCase):
    def test_standalone_dashboard_and_kpis(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);db=td/"perf.sqlite";csv_path=td/"perf.csv"
            with csv_path.open("w",encoding="utf-8-sig",newline="") as f:
                w=csv.writer(f);w.writerow(store.TEMPLATE_FIELDS)
                w.writerow(["2026-09-04","C1","CR-A","골프 거리측정기","golf","meta","problem_attack","hook","0.2초 측정",10000,9000,8000,6500,500,400,50,2500000,700000])
                w.writerow(["2026-09-04","C2","CR-B","무선 청소기","home_appliance","naver","comparison","hook2","흡입력",5000,0,0,0,200,150,20,800000,300000])
            store.import_file(csv_path,db)
            out=td/"dashboard.html";result=dashboard.generate(db,out)
            self.assertEqual(result["rows"],2)
            self.assertEqual(result["overall"]["impressions"],15000)
            self.assertGreater(result["overall"]["roas"],0)
            text=out.read_text(encoding="utf-8")
            self.assertIn("V2.7 광고 성과 대시보드",text)
            self.assertIn("골프 거리측정기",text)
            self.assertNotIn("https://",text)
            self.assertTrue(out.with_suffix('.json').exists())

if __name__=="__main__":unittest.main()
