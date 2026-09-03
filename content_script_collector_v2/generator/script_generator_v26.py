from __future__ import annotations

import argparse
import copy
import json
import re
import traceback
from dataclasses import fields
from pathlib import Path
from typing import Any

try:
    from . import script_generator_v25 as core
    from .script_generator_v25 import *  # type: ignore # noqa: F401,F403
    from . import ad_performance_learning as learner
except ImportError:
    import script_generator_v25 as core  # type: ignore
    from script_generator_v25 import *  # type: ignore # noqa: F401,F403
    import ad_performance_learning as learner  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PERFORMANCE_DB = ROOT / "database" / "ad_performance.sqlite"


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return round(max(lo, min(hi, value)), 2)


def _hook_obj(payload: dict[str, Any]):
    names = {f.name for f in fields(core.Hook)}
    return core.Hook(**{k: payload[k] for k in names})


def _combined_adjustment(product: str, category: str, angle: str, hook_text: str, profile: dict[str, Any]) -> tuple[float, dict[str, float]]:
    angle_adj = float(profile.get("angle_adjustments", {}).get(angle, 0.0) or 0.0)
    hook_adj = float(profile.get("hook_adjustments", {}).get(hook_text, 0.0) or 0.0)
    cid = learner.creative_id(product, category, angle, hook_text)
    creative_adj = float(profile.get("creative_adjustments", {}).get(cid, 0.0) or 0.0)
    total = max(-8.0, min(8.0, angle_adj + hook_adj + creative_adj))
    return round(total, 2), {"angle": round(angle_adj, 2), "hook": round(hook_adj, 2), "creative": round(creative_adj, 2)}


def _apply_hook_learning(hooks: list[dict[str, Any]], profile: dict[str, Any], product: str, category: str) -> list[dict[str, Any]]:
    out = []
    for raw in hooks:
        h = copy.deepcopy(raw)
        adj, parts = _combined_adjustment(product, category, h.get("angle", ""), h.get("text", ""), profile)
        h["base_score"] = float(h.get("score", 0.0) or 0.0)
        h["performance_adjustment"] = adj
        h["performance_adjustment_parts"] = parts
        h["learned_score"] = _clamp(h["base_score"] + adj)
        out.append(h)
    return out


def _diverse_top3(hooks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pool = sorted(
        hooks,
        key=lambda h: (h.get("learned_score", h.get("score", 0)), h.get("first_2s_power", 0), h.get("specificity", 0)),
        reverse=True,
    )
    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    for h in pool:
        angle = str(h.get("angle", ""))
        if angle not in used:
            selected.append(h); used.add(angle)
        if len(selected) == 3:
            return selected
    for h in pool:
        if h not in selected:
            selected.append(h)
        if len(selected) == 3:
            break
    return selected


def _apply_competition_learning(items: list[dict[str, Any]], profile: dict[str, Any], product: str, category: str) -> list[dict[str, Any]]:
    out = []
    for raw in items:
        item = copy.deepcopy(raw)
        angle = item.get("angle", "")
        hook_text = str(item.get("hook", {}).get("text", ""))
        adj, parts = _combined_adjustment(product, category, angle, hook_text, profile)
        scores = item.setdefault("scores", {})
        base_total = float(scores.get("total", 0.0) or 0.0)
        scores["base_total"] = base_total
        scores["performance_adjustment"] = round(adj, 2)
        scores["performance_adjustment_parts"] = parts
        scores["learned_total"] = _clamp(base_total + adj)
        out.append(item)
    return sorted(
        out,
        key=lambda x: (bool(x.get("qualified", True)), x["scores"]["learned_total"], x["scores"].get("first_2s_power", 0)),
        reverse=True,
    )


def _best_hook_for_angle(hooks: list[dict[str, Any]], angle: str) -> dict[str, Any]:
    candidates = [h for h in hooks if h.get("angle") == angle]
    if not candidates:
        candidates = hooks
    return max(candidates, key=lambda h: h.get("learned_score", h.get("score", 0)))


def _build_experiment_candidates(
    data: dict[str, Any], profile: dict[str, Any], minimum_impressions: int
) -> list[dict[str, Any]]:
    competition = data.get("creative_competition", [])[:3]
    hooks = data.get("hooks", [])
    active = bool(profile.get("active")) and profile.get("total_impressions", 0) >= 5000
    shares = (40, 30, 30) if active else (34, 33, 33)
    candidates = []
    for index, (item, share) in enumerate(zip(competition, shares), start=1):
        angle = item["angle"]
        hook = _best_hook_for_angle(hooks, angle)
        hobj = _hook_obj(hook)
        script = core.build_script(data["product_analysis"], hobj, 30, angle, data["ad_settings"]["intensity"])
        cid = learner.creative_id(data["product"], data["product_analysis"]["category"], angle, hook["text"])
        candidates.append({
            "slot": chr(64 + index),
            "creative_id": cid,
            "angle": angle,
            "angle_label": item.get("angle_label", angle),
            "hook": hook["text"],
            "selling_point": data["product_analysis"]["primary_selling_point"],
            "base_score": item["scores"].get("base_total", item["scores"].get("total", 0)),
            "performance_adjustment": item["scores"].get("performance_adjustment", 0),
            "learned_score": item["scores"].get("learned_total", item["scores"].get("total", 0)),
            "traffic_share_pct": share,
            "minimum_impressions": int(minimum_impressions),
            "script_30s": script,
        })
    return candidates


def generate(
    product: str,
    *,
    category: str = "",
    features=None,
    must_emphasize=None,
    pain_point: str = "",
    target: str = "일반 소비자",
    description: str = "",
    intensity: int = 4,
    min_score: float = 80.0,
    performance_db: str | Path | None = None,
    performance_file: str | Path | None = None,
    learning: bool = True,
    experiment_min_impressions: int = 1000,
):
    db_path = Path(performance_db) if performance_db else DEFAULT_PERFORMANCE_DB
    import_result = None
    if performance_file:
        import_result = learner.import_file(performance_file, db_path)
        print("[V2.6] Performance import:", import_result)

    base = core.generate(
        product,
        category=category,
        features=features,
        must_emphasize=must_emphasize,
        pain_point=pain_point,
        target=target,
        description=description,
        intensity=intensity,
        min_score=min_score,
    )
    profile = learner.build_learning_profile(base["product_analysis"]["category"], db_path) if learning else {
        "active": False, "reason": "learning disabled", "total_rows": 0, "total_impressions": 0,
        "category": base["product_analysis"]["category"], "angle_adjustments": {a: 0.0 for a in learner.ANGLE_NAMES},
        "angle_details": {}, "hook_adjustments": {}, "creative_adjustments": {}, "baselines": {},
    }

    product_name = base["product"]
    category_name = base["product_analysis"]["category"]
    learned_hooks = _apply_hook_learning(base["hooks"], profile, product_name, category_name)
    top3 = _diverse_top3(learned_hooks)
    competition = _apply_competition_learning(base["creative_competition"], profile, product_name, category_name)
    winner = next((x for x in competition if x.get("qualified", True)), competition[0])
    winner_angle = winner["angle"]
    winner_hook = _best_hook_for_angle(learned_hooks, winner_angle)
    hobj = _hook_obj(winner_hook)

    scripts: dict[str, Any] = {}
    prompts: dict[str, Any] = {}
    coverage: dict[str, float] = {}
    for duration in (15, 30, 45):
        key = f"{duration}s"
        beats = core.build_script(base["product_analysis"], hobj, duration, winner_angle, intensity)
        scripts[key] = beats
        coverage[key] = core.emphasis_coverage(base["product_analysis"], beats)
        prompts[key] = {m: [core.prompt(m, base["product_analysis"], b) for b in beats] for m in ("kling", "veo", "seedance")}

    base["version"] = "2.6"
    base["hooks"] = learned_hooks
    base["top3"] = top3
    base["creative_competition"] = competition
    base["winner"] = {
        "copywriter": winner.get("copywriter"), "angle": winner_angle,
        "angle_label": winner.get("angle_label"), "scores": winner.get("scores", {}),
        "hook": winner_hook["text"],
    }
    base["scripts_by_duration"] = scripts
    base["script_15s"] = scripts["15s"]
    base["script_30s"] = scripts["30s"]
    base["script_45s"] = scripts["45s"]
    base["video_prompts_by_duration"] = prompts
    base["video_prompts"] = prompts["30s"]
    base["cta"] = core.cta(intensity, base["product_analysis"])
    base.setdefault("quality_audit", {})["must_emphasize_coverage"] = coverage
    base["quality_audit"]["performance_learning_active"] = bool(profile.get("active"))
    base["quality_audit"]["performance_sample_impressions"] = int(profile.get("total_impressions", 0))

    candidates = _build_experiment_candidates(base, profile, experiment_min_impressions)
    base["performance_learning"] = {
        "database": str(db_path), "enabled": bool(learning), "import_result": import_result,
        **profile,
    }
    base["experiment_plan"] = {
        "mode": "A/B/C",
        "status": "PLAN_ONLY_NO_AD_SPEND",
        "candidates": candidates,
        "metrics_to_collect": ["impressions", "views_2s", "views_3s", "clicks", "detail_views", "purchases", "revenue", "spend"],
        "decision_rule": "각 후보 최소 노출을 채운 뒤 learned_score와 구매전환을 함께 비교",
        "minimum_impressions_per_candidate": int(experiment_min_impressions),
        "note": "실제 광고 게시/예산 집행은 자동 수행하지 않습니다.",
    }
    return base


def render_md(data: dict[str, Any]) -> str:
    text = core.render_md(data).replace("Script Generator V2.5", "Script Generator V2.6", 1)
    learning = data["performance_learning"]
    lines = [text, "", "## V2.6 성과학습", f"- 학습 활성: **{learning.get('active', False)}**",
             f"- 누적 행: {learning.get('total_rows', 0)}", f"- 누적 노출: {learning.get('total_impressions', 0)}",
             f"- Angle 보정: `{json.dumps(learning.get('angle_adjustments', {}), ensure_ascii=False)}`", "",
             "## A/B/C 실험 후보"]
    for c in data["experiment_plan"]["candidates"]:
        lines += [f"### {c['slot']} · {c['angle_label']} · `{c['creative_id']}`",
                  f"- Hook: {c['hook']}", f"- 학습점수: {c['learned_score']} (성과보정 {c['performance_adjustment']:+})",
                  f"- 권장 트래픽: {c['traffic_share_pct']}%", f"- 최소 노출: {c['minimum_impressions']:,}", ""]
    lines += ["## 성과 수집 항목", "`impressions, views_2s, views_3s, clicks, detail_views, purchases, revenue, spend`",
              "", "> 실제 광고 게시와 예산 집행은 이 프로그램이 자동 수행하지 않습니다."]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Script Generator V2.6 with performance learning")
    ap.add_argument("product")
    ap.add_argument("--category", default="")
    ap.add_argument("--features", default="")
    ap.add_argument("--must-emphasize", default="")
    ap.add_argument("--pain-point", default="")
    ap.add_argument("--target", default="일반 소비자")
    ap.add_argument("--description", default="")
    ap.add_argument("--intensity", type=int, choices=(1, 2, 3, 4, 5), default=4)
    ap.add_argument("--min-score", type=float, default=80)
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--require-db", action="store_true")
    ap.add_argument("--performance-db", default=str(DEFAULT_PERFORMANCE_DB))
    ap.add_argument("--performance-file", default="")
    ap.add_argument("--learning-off", action="store_true")
    ap.add_argument("--experiment-min-impressions", type=int, default=1000)
    return ap.parse_args()


def main() -> int:
    a = parse_args()
    try:
        data = generate(
            a.product, category=a.category, features=a.features, must_emphasize=a.must_emphasize,
            pain_point=a.pain_point, target=a.target, description=a.description, intensity=a.intensity,
            min_score=a.min_score, performance_db=a.performance_db,
            performance_file=(a.performance_file or None), learning=not a.learning_off,
            experiment_min_impressions=a.experiment_min_impressions,
        )
        if a.require_db and not data["db_integration"]["connected"]:
            raise RuntimeError("Content DB is not connected or empty.")
        out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", a.product)
        (out / f"{safe}_script_v2.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        md = out / f"{safe}_script_v2.md"; md.write_text(render_md(data), encoding="utf-8")
        print("Version:", data["version"])
        print("Performance learning:", data["performance_learning"].get("active"))
        print("Winner:", data["winner"])
        print("Experiment candidates:", [c["creative_id"] for c in data["experiment_plan"]["candidates"]])
        print("Generated:", md)
        return 0
    except Exception as exc:
        tb = traceback.format_exc()
        print("ERROR:", exc); print(tb)
        try:
            core.LOGGER.error("Script Generator V2.6 failed: %s\n%s", exc, tb)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
