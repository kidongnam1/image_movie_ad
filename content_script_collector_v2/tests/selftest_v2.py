import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from generator.script_generator_v2 import generate
d=generate("세럼")
assert len(d["hooks"])==30
assert len(d["top3"])==3
assert len(d["script_30s"])==5
assert all(len(d["video_prompts"][m])==5 for m in ("kling","veo","seedance"))
assert all("세럼" in h["text"] for h in d["top3"])
print("V2 SELFTEST PASS")
