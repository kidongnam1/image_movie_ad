from __future__ import annotations
import argparse, json, traceback
from pathlib import Path

try:
    from . import creative_package_v26 as v26
except ImportError:
    import creative_package_v26 as v26  # type: ignore

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_PERFORMANCE_DB=ROOT/"database/ad_performance.sqlite"

def augment_v27(project_dir:Path,generated:dict)->None:
    registry=generated.get("creative_registry",{});assets=generated.get("input_assets",{})
    v26.core.write_json(project_dir/"creative_registry.json",registry)
    v26.core.write_json(project_dir/"input_assets.json",assets)
    project_path=project_dir/"project.json";project=json.loads(project_path.read_text(encoding="utf-8"));project["creative_registry"]=registry;project["input_assets"]=assets;project["script_generator_version"]="2.7";v26.core.write_json(project_path,project)
    manifest_path=project_dir/"manifest.json";manifest=json.loads(manifest_path.read_text(encoding="utf-8"));
    for name in ("creative_registry.json","input_assets.json"):
        if name not in manifest.get("generated_files",[]):manifest.setdefault("generated_files",[]).append(name)
    manifest["milestone"]="CREATIVE_PACKAGE_V27_PLATFORM_READY";manifest["script_generator_version"]="2.7";v26.core.write_json(manifest_path,manifest)

def parse_args():
    p=argparse.ArgumentParser(description="Creative Package V2.7");p.add_argument("product",nargs="?");p.add_argument("--description",default="");p.add_argument("--target",default="일반 소비자");p.add_argument("--duration",type=int,choices=(15,30,45,60),default=30);p.add_argument("--category",default="");p.add_argument("--must-emphasize",default="");p.add_argument("--features",default="");p.add_argument("--pain-point",default="");p.add_argument("--intensity",type=int,choices=(1,2,3,4,5),default=4);p.add_argument("--url",default="");p.add_argument("--image",default="");p.add_argument("--project-id",default=None);p.add_argument("--outdir",type=Path,default=ROOT/"outputs_creative");p.add_argument("--require-db",action="store_true");p.add_argument("--performance-file",default="");p.add_argument("--performance-db",default=str(DEFAULT_PERFORMANCE_DB));p.add_argument("--experiment-min-impressions",type=int,default=1000);return p.parse_args()
def main():
    a=parse_args();original=None
    try:
        if not a.product:raise ValueError("product is required")
        if a.performance_file:print("PERFORMANCE_IMPORT=",v26.perf.import_file(a.performance_file,a.performance_db))
        generated=v26.generator.generate(a.product,category=a.category,features=a.features,must_emphasize=a.must_emphasize,pain_point=a.pain_point,target=a.target,description=a.description,product_image=a.image,product_url=a.url,intensity=a.intensity,performance_db=a.performance_db,experiment_min_impressions=a.experiment_min_impressions,source_project=a.project_id or "")
        if a.require_db and not generated.get("db_integration",{}).get("connected"):raise RuntimeError("Content DB is not connected or empty")
        config=v26.core.build_project_config(product_name=a.product,product_description=a.description,target_audience=a.target,duration_sec=a.duration,product_url=a.url,product_image=a.image,project_id=a.project_id,category=a.category,must_emphasize=a.must_emphasize,features=a.features,pain_point=a.pain_point,intensity=a.intensity)
        original=v26.core.call_legacy;v26.core.call_legacy=lambda _config:generated;project_dir=v26.core.generate_package(config,a.outdir,require_db=a.require_db);v26.core.call_legacy=original;original=None
        v26.augment_package(project_dir,generated);augment_v27(project_dir,generated)
        print("OUTPUT_DIR=",project_dir);print("SCRIPT_GENERATOR_VERSION=",generated.get("version"));print("REGISTRY=",generated.get("creative_registry"));return 0
    except Exception as exc:
        if original is not None:v26.core.call_legacy=original
        print("ERROR:",exc);print(traceback.format_exc());return 1
if __name__=="__main__":raise SystemExit(main())
