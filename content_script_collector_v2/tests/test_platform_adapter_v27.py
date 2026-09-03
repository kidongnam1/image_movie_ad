import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"generator"))
import performance_store_v26 as store
import performance_registry_v27 as registry
import platform_performance_adapter_v27 as adapter

class PlatformAdapterV27Tests(unittest.TestCase):
    def _seed(self,db):
        c=store.connect(db)
        data={"version":"2.7","product":"골프 거리측정기","product_analysis":{"category":"golf"},"experiment_plan":{"candidates":[{"creative_id":"CR-ABCDEF123456","angle":"problem_attack","angle_label":"문제공격형","hook":"아직도 거리 재느라 늦으세요?","selling_point":"0.2초 측정","slot":"A"}]}}
        registry.register_candidates(c,data);c.close()
    def _write(self,path,headers,row):
        with path.open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.writer(f);w.writerow(headers);w.writerow(row)
    def test_four_platforms_auto_detect_and_registry_enrich(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);db=td/"perf.sqlite";self._seed(db)
            cases=[
                ("meta",["Reporting starts","Campaign ID","Ad name","Impressions","2-second continuous video plays","3-second video plays","Link clicks","Landing page views","Purchases","Purchase conversion value","Amount spent"],["2026-09-04","M1","Golf CR-ABCDEF123456",10000,8000,6500,500,400,50,2500000,700000]),
                ("tiktok",["Date","Campaign ID","Ad name","Impressions","2-second video views","Clicks","Conversions","Sales","Spend"],["2026-09-04","T1","TikTok CR-ABCDEF123456",9000,7000,420,40,2000000,600000]),
                ("naver",["날짜","캠페인ID","광고명","노출수","클릭수","전환수","전환매출액","총비용"],["2026-09-04","N1","네이버 CR-ABCDEF123456",8000,300,30,1400000,400000]),
                ("coupang",["날짜","캠페인ID","광고명","노출수","클릭수","주문수","매출액","광고비"],["2026-09-04","C1","쿠팡 CR-ABCDEF123456",7000,280,28,1200000,350000]),
            ]
            for name,headers,row in cases:
                p=td/f"{name}.csv";self._write(p,headers,row);res=adapter.import_platform(p,"auto",db)
                self.assertEqual(res["adapter"]["platform"],name)
                self.assertEqual(res["adapter"]["registry_enriched_rows"],1)
                self.assertEqual(res["import"]["errors"],0)
            c=store.connect(db);rows=c.execute("SELECT * FROM performance_events").fetchall();c.close()
            self.assertEqual(len(rows),4)
            self.assertTrue(all(r["product"]=="골프 거리측정기" for r in rows))
            self.assertTrue(all(r["angle"]=="problem_attack" for r in rows))
    def test_default_product_allows_unregistered_generic_file(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);db=td/"p.sqlite";p=td/"generic.csv"
            self._write(p,["Date","Impressions","Clicks","Sales","Cost"],["2026-09-04",1000,40,300000,100000])
            res=adapter.import_platform(p,"generic",db,default_product="테스트 상품",default_category="general")
            self.assertEqual(res["adapter"]["missing_product_rows"],0)
            c=store.connect(db);r=c.execute("SELECT product,category FROM performance_events").fetchone();c.close()
            self.assertEqual(r["product"],"테스트 상품")
            self.assertEqual(r["category"],"general")

if __name__=="__main__":unittest.main()
