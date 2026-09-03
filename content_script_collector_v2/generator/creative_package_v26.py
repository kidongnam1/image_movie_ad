from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

try:
    from . import creative_package_v1 as core
    from . import script_generator_v2 as generator
    from . import ad_performance_learning as perf
except ImportError:
    import creative_package_v1 as core  # type: ignore
    import script_generator_v2 as generator  # type: ignore
    import ad_performance_learning as perf  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PERFORMANCE_DB = ROOT / "database" / "ad_performance.sqlite"


def augment_package(project_dir: Path, generated: dict) -> None:
    learning = generated.get("performance_learning", {})
    experiment = generated.get("experiment_plan", {})
    core.write_json(project_dir / "performance_learning.json", learning)
    core.write_json(project_dir / "experiment_plan.json", experiment)

    project_path = project_dir / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["script_generator_version"] = generated.get("version", "2.6")
    project["performance_learning"] = learning
    project["experiment_plan"] = experiment
    core.write_json(project_path, project)

    strategy_path = project_dir / "strategy.md"
    strategy = strategy_path.read_text(encoding="utf-8")
    lines = [
        strategy.rstrip(), "", "## V2.6 성과학습",
        f"- 학습 활성: **{learning.get('active', False)}**",
        f"- 누적 성과 행: {learning.get('total_rows', 0)}",
        f"- 누적 노출: {learning.get('total_impressions', 0)}",
        f"- Angle 성과보정: `{json.dumps(learning.get('angle_adjustments', {}), ensure_ascii=False)}`",
        "", "## A/B/C 실험 후보",
    ]
    for c in experiment.get("candidates", []):
        lines += [
            f"- **{c['slot']} / {c['angle_label']}** — `{c['creative_id']}`",
            f"  - Hook: {c['hook']}",
            f"  - 권장 트래픽: {c['traffic_share_pct']}% / 최소 노출 {c['minimum_impressions']:,}",
        ]
    lines += ["", "> 실제 광고 게시 및 예산 집행은 자동 수행하지 않습니다.", ""]
    core.write_text(strategy_path, "\n".join(lines))

    manifest_path = project_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name in ("performance_learning.json", "experiment_plan.json"):
        if name not in manifest.get("generated_files", []):
            manifest.setdefault("generated_files", []).append(name)
    manifest["milestone"] = "CREATIVE_PACKAGE_V26_PERFORMANCE_LEARNING"
    manifest["script_generator_version"] = generated.get("version", "2.6")
    manifest["performance_learning_active"] = learning.get("active", False)
    core.write_json(manifest_path, manifest)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Creative Package V2.6 performance-learning wrapper")
    p.add_argument("product", nargs="?", help="상품명")
    p.add_argument("--description", default="")
    p.add_argument("--target", default="일반 소비자")
    p.add_argument("--duration", type=int, choices=(15, 30, 45, 60), default=30)
    p.add_argument("--category", default="")
    p.add_argument("--must-emphasize", default="")
    p.add_argument("--features", default="")
    p.add_argument("--pain-point", default="")
    p.add_argument("--intensity", type=int, choices=(1, 2, 3, 4, 5), default=4)
    p.add_argument("--url", default="")
    p.add_argument("--image", default="")
    p.add_argument("--project-id", default=None)
    p.add_argument("--outdir", type=Path, default=ROOT / "outputs_creative")
    p.add_argument("--require-db", action="store_true")
    p.add_argument("--performance-file", default="")
    p.add_argument("--performance-db", default=str(DEFAULT_PERFORMANCE_DB))
    p.add_argument("--experiment-min-impressions", type=int, default=1000)
    return p.parse_args()


def main() -> int:
    a = parse_args()
    try:
        if not a.product:
            raise ValueError("product is required")
        if a.performance_file:
            result = perf.import_file(a.performance_file, a.performance_db)
            print("PERFORMANCE_IMPORT=", result)
        config = core.build_project_config(
            product_name=a.product,
            product_description=a.description,
            target_audience=a.target,
            duration_sec=a.duration,
            product_url=a.url,
            product_image=a.image,
            project_id=a.project_id,
            category=a.category,
            must_emphasize=a.must_emphasize,
            features=a.features,
            pain_point=a.pain_point,
            intensity=a.intensity,
        )
        project_dir = core.generate_package(config, a.outdir, require_db=a.require_db)
        generated = generator.generate(
            a.product,
            category=a.category,
            features=a.features,
            must_emphasize=a.must_emphasize,
            pain_point=a.pain_point,
            target=a.target,
            description=a.description,
            intensity=a.intensity,
            performance_db=a.performance_db,
            experiment_min_impressions=a.experiment_min_impressions,
        )
        augment_package(project_dir, generated)
        print("OUTPUT_DIR=", project_dir)
        print("SCRIPT_GENERATOR_VERSION=", generated.get("version"))
        print("EXPERIMENT_IDS=", [c["creative_id"] for c in generated["experiment_plan"]["candidates"]])
        return 0
    except Exception as exc:
        tb = traceback.format_exc()
        print("ERROR:", exc)
        print(tb)
        core.LOGGER.error("Creative Package V2.6 failed: %s\n%s", exc, tb)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
