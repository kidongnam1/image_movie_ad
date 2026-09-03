from __future__ import annotations
import argparse, json, re, traceback
from pathlib import Path
from typing import Any

try:
    from . import script_generator_v26 as core
    from .script_generator_v26 import *  # type: ignore # noqa: F401,F403
    from . import performance_store_v26 as store
    from . import performance_registry_v27 as registry
except ImportError:
    import script_generator_v26 as core  # type: ignore
    from script_generator_v26 import *  # type: ignore # noqa: F401,F403
    import performance_store_v26 as store  # type: ignore
    import performance_registry_v27 as registry  # type: ignore

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_PERFORMANCE_DB=ROOT/"database/ad_performance.sqlite"

def generate(product: str, **kwargs: Any):
    source_project=str(kwargs.pop("source_project","") or "")
    product_image=str(kwargs.pop("product_image","") or "")
    data=core.generate(product,**kwargs)
    db_path=Path(kwargs.get("performance_db") or DEFAULT_PERFORMANCE_DB)
    conn=store.connect(db_path)
    registered=registry.register_candidates(conn,data,source_project=source_project)
    conn.close()
    data["version"]="2.7"
    data["creative_registry"]={"database":str(db_path),"registered_candidates":registered,"id_pattern":"CR-XXXXXXXXXXXX","usage":"광고명에 creative_id를 포함하면 플랫폼 성과 CSV를 자동으로 상품/Angle/Hook에 연결할 수 있습니다."}
    data["input_assets"]={"product_image":product_image,"image_available":bool(product_image),"image_usage":"대본 생성에서는 참조 메타데이터로 보존하고 Creative Package에서는 product_image로 전달합니다."}
    return data

def render_md(data:dict[str,Any])->str:
    text=core.render_md(data).replace("Script Generator V2.6","Script Generator V2.7",1);r=data.get("creative_registry",{});asset=data.get("input_assets",{})
    return text+f"\n\n## V2.7 Creative Registry\n- 등록된 A/B/C: {r.get('registered_candidates',0)}개\n- 광고명에 `CR-...` ID를 포함하세요.\n\n## 입력 상품 이미지\n- 이미지: `{asset.get('product_image') or '미입력'}`\n"

def parse_args():
    p=argparse.ArgumentParser(description="Script Generator V2.7 with creative registry");p.add_argument("product");p.add_argument("--category",default="");p.add_argument("--features",default="");p.add_argument("--must-emphasize",default="");p.add_argument("--pain-point",default="");p.add_argument("--target",default="일반 소비자");p.add_argument("--description",default="");p.add_argument("--image",default="",help="상품 이미지 경로");p.add_argument("--intensity",type=int,choices=(1,2,3,4,5),default=4);p.add_argument("--min-score",type=float,default=80);p.add_argument("--outdir",default="outputs");p.add_argument("--require-db",action="store_true");p.add_argument("--performance-db",default=str(DEFAULT_PERFORMANCE_DB));p.add_argument("--performance-file",default="");p.add_argument("--learning-off",action="store_true");p.add_argument("--experiment-min-impressions",type=int,default=1000);return p.parse_args()
def main():
    a=parse_args()
    try:
        d=generate(a.product,category=a.category,features=a.features,must_emphasize=a.must_emphasize,pain_point=a.pain_point,target=a.target,description=a.description,product_image=a.image,intensity=a.intensity,min_score=a.min_score,performance_db=a.performance_db,performance_file=(a.performance_file or None),learning=not a.learning_off,experiment_min_impressions=a.experiment_min_impressions)
        if a.require_db and not d["db_integration"]["connected"]:raise RuntimeError("Content DB is not connected or empty.")
        out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);safe=re.sub(r"[^0-9A-Za-z가-힣_-]+","_",a.product);(out/f"{safe}_script_v2.json").write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8");md=out/f"{safe}_script_v2.md";md.write_text(render_md(d),encoding="utf-8");print("Version:",d["version"]);print("Creative registry:",d["creative_registry"]);print("Product image:",d["input_assets"]["product_image"]);print("Generated:",md);return 0
    except Exception as e:
        print("ERROR:",e);print(traceback.format_exc());return 1
if __name__=="__main__":raise SystemExit(main())
