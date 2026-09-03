import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generator.script_generator_v2 import generate

beauty=generate("세럼")
assert len(beauty["hooks"])==30
assert len(beauty["top3"])==3
assert len(beauty["script_15s"])==5
assert len(beauty["script_30s"])==5
assert len(beauty["script_45s"])==5
assert all(len(beauty["video_prompts"][m])==5 for m in ("kling","veo","seedance"))
assert beauty["product_analysis"]["category"]=="beauty"
assert all(h["score"]>=80 for h in beauty["hooks"])

golf=generate(
    "골프 거리측정기",
    must_emphasize="0.2초 측정, 손떨림 보정",
    pain_point="거리 판단이 늦어 샷 템포가 끊기는 문제",
    target="40~60대 골퍼",
    intensity=4,
)
assert golf["product_analysis"]["category"]=="golf"
assert golf["product_analysis"]["primary_selling_point"]=="0.2초 측정"
assert len(golf["hooks"])==30
assert all(h["score"]>=80 for h in golf["hooks"])
assert all("골프 거리측정기" in h["text"] for h in golf["top3"])
assert "피부" not in " ".join(x["spoken"] for x in golf["script_30s"])
assert "beauty" not in " ".join(golf["video_prompts"]["veo"]).lower()

vacuum=generate(
    "무선 청소기",
    must_emphasize="18,000Pa 흡입력",
    features="480g 초경량|USB-C 충전",
)
assert vacuum["product_analysis"]["category"]=="home_appliance"
assert vacuum["product_analysis"]["primary_selling_point"]=="18,000Pa 흡입력"
assert "18,000Pa 흡입력" in vacuum["product_analysis"]["selling_points"]
assert "피부" not in " ".join(x["spoken"] for x in vacuum["script_30s"])

print("V2.4 SELFTEST PASS")
