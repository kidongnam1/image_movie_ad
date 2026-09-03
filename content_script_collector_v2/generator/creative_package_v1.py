from __future__ import annotations

import argparse
import json
import logging
import re
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import script_generator_v2 as legacy

ROOT = Path(__file__).resolve().parents[1]
KST = timezone(timedelta(hours=9))
VARIANTS = ("ugc", "product_demo", "cinematic")
BANNED_CLAIMS = (
    "치료", "완치", "주름 제거", "여드름 치료", "100%", "즉시 효과", "완전히 사라", "무조건", "절대",
)

VARIANT_LABELS = {
    "ugc": "UGC 후기형",
    "product_demo": "Product Demo 제품 시연형",
    "cinematic": "Cinematic 브랜드형",
}

VARIANT_DIRECTIONS = {
    "ugc": "실사용자가 직접 불편을 발견하고 해결 포인트를 보여주는 자연스러운 퍼포먼스 광고",
    "product_demo": "핵심 기능이 실제로 어떻게 작동하는지 짧고 명확하게 증명하는 제품 시연 광고",
    "cinematic": "상품의 핵심 Selling Point를 라이프스타일과 프리미엄 영상미로 강조하는 브랜드 광고",
}

CAMERA_BY_VARIANT = {
    "ugc": ["handheld problem close-up", "POV reaction", "product reveal", "hands-on demo", "proof close-up", "quick comparison", "direct CTA end card"],
    "product_demo": ["tight product close-up", "top-down problem setup", "feature macro", "hands-on operation", "result close-up", "side-by-side comparison", "packshot end card"],
    "cinematic": ["cinematic problem cold open", "slow lifestyle detail", "hero product reveal", "macro feature detail", "smooth use sequence", "lifestyle payoff", "premium packshot"],
}


@dataclass(frozen=True)
class ProjectConfig:
    project_id: str
    product_name: str
    product_description: str
    target_audience: str
    duration_sec: int
    product_url: str = ""
    product_image: str = ""
    language: str = "ko-KR"
    aspect_ratio: str = "9:16"
    ad_variants: tuple[str, ...] = VARIANTS
    category: str = ""
    must_emphasize: str = ""
    features: str = ""
    pain_point: str = ""
    intensity: int = 4


def configure_logging() -> logging.Logger:
    log_dir = ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("creative_package_v1")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


LOGGER = configure_logging()


def log_status(message: str) -> None:
    print(message)
    LOGGER.info(message)


def now_kst() -> datetime:
    return datetime.now(KST)


def slugify(text: str) -> str:
    value = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", (text or "").strip()).strip("_")
    return value or "project"


def build_project_config(
    product_name: str,
    product_description: str = "",
    target_audience: str = "일반 소비자",
    duration_sec: int = 30,
    product_url: str = "",
    product_image: str = "",
    project_id: str | None = None,
    category: str = "",
    must_emphasize: str = "",
    features: str = "",
    pain_point: str = "",
    intensity: int = 4,
) -> ProjectConfig:
    product_name = (product_name or "").strip()
    if not product_name:
        raise ValueError("product_name is required")
    if duration_sec not in (15, 30, 45, 60):
        raise ValueError("duration_sec must be one of 15, 30, 45, 60")
    if intensity not in (1, 2, 3, 4, 5):
        raise ValueError("intensity must be 1..5")
    stamp = now_kst().strftime("%Y%m%d_%H%M%S")
    pid = project_id or f"{slugify(product_name)}_{stamp}"
    return ProjectConfig(
        project_id=pid,
        product_name=product_name,
        product_description=(product_description or "").strip(),
        target_audience=(target_audience or "일반 소비자").strip(),
        duration_sec=duration_sec,
        product_url=(product_url or "").strip(),
        product_image=(product_image or "").strip(),
        category=(category or "").strip(),
        must_emphasize=(must_emphasize or "").strip(),
        features=(features or "").strip(),
        pain_point=(pain_point or "").strip(),
        intensity=intensity,
    )


def load_project_config(path: Path) -> ProjectConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    return build_project_config(
        product_name=data.get("product_name", ""),
        product_description=data.get("product_description", ""),
        target_audience=data.get("target_audience", "일반 소비자"),
        duration_sec=int(data.get("duration_sec", 30)),
        product_url=data.get("product_url", ""),
        product_image=data.get("product_image", ""),
        project_id=data.get("project_id"),
        category=data.get("category", ""),
        must_emphasize=data.get("must_emphasize", ""),
        features=data.get("features", ""),
        pain_point=data.get("pain_point", ""),
        intensity=int(data.get("intensity", 4)),
    )


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def allocate_timeline(duration_sec: int, count: int = 7) -> list[tuple[int, int]]:
    if count < 2:
        raise ValueError("scene count must be >= 2")
    weights = [10, 14, 14, 18, 16, 14, 14]
    if count != len(weights):
        weights = [1] * count
    total = sum(weights)
    cumulative = 0
    starts = [0]
    for weight in weights[:-1]:
        cumulative += weight
        starts.append(round(duration_sec * cumulative / total))
    ends = starts[1:] + [duration_sec]
    timeline = list(zip(starts, ends))
    if any(end <= start for start, end in timeline):
        raise ValueError("duration is too short for scene count")
    return timeline


def config_product_context(config: ProjectConfig) -> dict[str, Any]:
    if hasattr(legacy, "product_profile"):
        return legacy.product_profile(
            config.product_name,
            category=config.category,
            features=config.features,
            must_emphasize=config.must_emphasize,
            pain_point=config.pain_point,
            target=config.target_audience,
            description=config.product_description,
        )
    return {
        "product": config.product_name,
        "category": "general",
        "category_label": "일반 상품",
        "target": config.target_audience,
        "pain_point": config.pain_point or "반복되는 사용 불편",
        "primary_selling_point": config.must_emphasize or config.product_description or "핵심 기능",
        "selling_points": [config.must_emphasize or config.product_description or "핵심 기능"],
        "demo_action": "제품의 대표 기능을 실제 사용 환경에서 보여준다",
        "proof_action": "실제 작동 과정을 연속으로 보여준다",
        "environment": "realistic everyday product-use setting",
        "buyer_motive": "실제 불편을 줄이는 것",
    }


def call_legacy(config: ProjectConfig) -> dict[str, Any]:
    advanced = bool(config.category or config.must_emphasize or config.features or config.pain_point or config.intensity != 4)
    if advanced:
        try:
            return legacy.generate(
                config.product_name,
                category=config.category,
                features=config.features,
                must_emphasize=config.must_emphasize,
                pain_point=config.pain_point,
                target=config.target_audience,
                description=config.product_description,
                intensity=config.intensity,
            )
        except TypeError:
            pass
    return legacy.generate(config.product_name)


def safe_hook(top3: list[dict[str, Any]], index: int, product: str) -> dict[str, Any]:
    if top3:
        return top3[index % len(top3)]
    return {
        "rank": index + 1,
        "text": f"{product}, 구매 전에 이 핵심 포인트부터 확인해보세요.",
        "category": "curiosity",
        "angle": "curiosity",
        "score": 82.0,
        "risk": 0,
        "db_source_id": None,
        "db_hook_id": None,
    }


def build_variant_beats(config: ProjectConfig, variant: str, hook: dict[str, Any], legacy_data: dict[str, Any]) -> list[dict[str, Any]]:
    ctx = config_product_context(config)
    product = config.product_name
    target = config.target_audience
    pain = ctx["pain_point"]
    point = ctx["primary_selling_point"]
    cta = legacy_data.get("cta") or "제품의 핵심 기능과 가격 조건을 확인해보세요."

    if variant == "ugc":
        content = [
            ("HOOK", hook["text"], hook["text"], f"{target} 사용자가 {product}을 들고 문제 상황을 바로 언급한다."),
            ("PROBLEM", f"저는 {pain} 때문에 비슷한 제품을 계속 비교하게 됐습니다.", "이 불편, 계속 반복?", f"{pain}이 드러나는 일상 장면을 짧게 보여준다."),
            ("DISCOVERY", f"그러다 {product}에서 {point}를 먼저 보게 됐습니다.", f"핵심 포인트: {point}", f"{product}을 가까이 보여주며 핵심 특징을 짚는다."),
            ("DEMO", f"말로 설명하는 것보다 실제로 써보면 더 빠릅니다. {point}가 어떻게 작동하는지 보세요.", "말보다 실제 사용", ctx["demo_action"]),
            ("EXPERIENCE", f"제가 보는 기준은 단순합니다. {point}가 실제 불편을 줄이는지입니다.", "체감되는지 확인", ctx["proof_action"]),
            ("COMPARE", f"비슷한 {product}과 비교할 때도 가격만 보지 말고 {point}를 같이 보세요.", "가격 + 핵심 기능 비교", f"두 선택지를 나란히 두고 {point} 기준으로 비교한다."),
            ("CTA", cta, "가격 · 조건 · 핵심 기능 확인", f"{product}과 {point}를 한 화면에 정리한 엔드카드."),
        ]
    elif variant == "product_demo":
        content = [
            ("HOOK", hook["text"], hook["text"], f"{product}을 첫 프레임 중앙에 크게 보여준다."),
            ("SETUP", f"먼저 해결하려는 문제는 {pain}입니다.", "문제부터 확인", f"실제 문제 상황을 제품 없이 먼저 보여준다."),
            ("FEATURE", f"이 제품에서 가장 먼저 볼 것은 {point}입니다.", f"핵심: {point}", f"제품의 {point} 관련 부위나 기능을 클로즈업한다."),
            ("DEMO", f"이제 실제로 작동시켜 보겠습니다. 광고 문구보다 사용 장면을 보세요.", "실제로 작동시켜 보기", ctx["demo_action"]),
            ("PROOF", f"핵심은 {point}가 실제 사용에서 체감되는지입니다.", "실사용 체크", ctx["proof_action"]),
            ("COMPARE", f"구매 전에는 같은 가격대 제품과 {point} 기준으로 비교해보세요.", "같은 조건으로 비교", f"동일한 사용 조건에서 핵심 기능을 비교하는 컷."),
            ("CTA", cta, "상세 조건 확인", f"{product} 정면 팩샷과 핵심 기능·가격 확인 CTA."),
        ]
    elif variant == "cinematic":
        content = [
            ("HOOK", hook["text"], hook["text"], f"{pain}이 드러나는 강한 첫 장면 뒤 {product} 실루엣을 짧게 공개한다."),
            ("MOOD", f"반복되는 불편은 작아 보여도 매일 쌓입니다. {pain}이 그런 순간입니다.", "작은 불편이 매일 쌓일 때", f"{ctx['environment']}에서 문제 상황을 감각적으로 보여준다."),
            ("REVEAL", f"{product}의 중심은 화려한 기능 수가 아니라 {point}입니다.", f"중심은 {point}", f"프리미엄 라이팅으로 {product}와 핵심 기능을 히어로 컷으로 보여준다."),
            ("DETAIL", f"{point}가 실제 사용에서 어떻게 연결되는지 가까이 보여드립니다.", "기능을 눈으로 확인", ctx["demo_action"]),
            ("PAYOFF", f"목표는 하나입니다. {ctx['buyer_motive']}.", "불편은 줄이고 사용은 단순하게", ctx["proof_action"]),
            ("LIFESTYLE", f"과장된 변화보다 실제 생활에서 반복해서 쓰게 되는 이유를 보여줍니다.", "실생활에서 계속 쓰는 이유", f"{ctx['environment']}에서 자연스럽게 제품을 사용하는 라이프스타일 장면."),
            ("CTA", cta, "핵심 기능 확인", f"프리미엄 팩샷과 {point} 한 줄로 마무리."),
        ]
    else:
        raise ValueError(f"unsupported variant: {variant}")

    timeline = allocate_timeline(config.duration_sec, len(content))
    cameras = CAMERA_BY_VARIANT[variant]
    scenes: list[dict[str, Any]] = []
    for idx, ((role, spoken, caption, visual), (start, end)) in enumerate(zip(content, timeline), 1):
        scenes.append({
            "scene_no": idx,
            "start_sec": start,
            "end_sec": end,
            "duration_sec": end - start,
            "scene_type": role.lower(),
            "role": role,
            "spoken": spoken,
            "caption": caption,
            "visual": visual,
            "camera": cameras[idx - 1],
            "transition": "cut" if idx < len(content) else "end",
        })
    return scenes


def image_prompt(config: ProjectConfig, variant: str, scene: dict[str, Any]) -> str:
    ctx = config_product_context(config)
    return (
        f"Vertical {config.aspect_ratio} Korean advertising still for {config.product_name}. "
        f"Product category: {ctx['category_label']}. Audience: {config.target_audience}. "
        f"Creative direction: {VARIANT_DIRECTIONS[variant]}. Scene purpose: {scene['role']}. "
        f"Visual: {scene['visual']} Camera composition: {scene['camera']}. Environment: {ctx['environment']}. "
        "Realistic product-focused commercial, premium controlled lighting, consistent product packaging, strong visual hierarchy, "
        "no text baked into image, no fabricated review evidence, no fake scarcity, no unsupported medical or performance claim visualization."
    )


def video_prompt(config: ProjectConfig, variant: str, scene: dict[str, Any], model: str) -> str:
    ctx = config_product_context(config)
    base = (
        f"Vertical {config.aspect_ratio} Korean short-form ad for {config.product_name}. "
        f"Product category: {ctx['category_label']}. Duration about {scene['duration_sec']} seconds. "
        f"Creative direction: {VARIANT_DIRECTIONS[variant]}. Scene purpose: {scene['role']}. "
        f"Action: {scene['visual']} Camera: {scene['camera']}. Environment: {ctx['environment']}. "
        "Realistic product use, consistent packaging, strong first frame, natural human interaction, no fabricated testimonials, "
        "no fake scarcity, no unsupported medical or performance claims."
    )
    suffix = {
        "kling": " Controlled motion, realistic physics, stable identity and packaging, smooth social-ad pacing.",
        "veo": " Cinematic lensing, gentle camera movement, coherent continuity and realistic room ambience.",
        "seedance": " Strong first frame, concise motion, dynamic but stable camera movement, clear product interaction.",
    }.get(model, " Natural motion and continuity.")
    return base + suffix


def format_timestamp(seconds: int) -> str:
    hours, rem = divmod(max(0, int(seconds)), 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},000"


def render_srt(scenes: list[dict[str, Any]]) -> str:
    return "\n\n".join(
        f"{index}\n{format_timestamp(scene['start_sec'])} --> {format_timestamp(scene['end_sec'])}\n{scene['caption']}"
        for index, scene in enumerate(scenes, 1)
    ) + "\n"


def render_script_md(config: ProjectConfig, variant: str, scenes: list[dict[str, Any]], hook: dict[str, Any]) -> str:
    ctx = config_product_context(config)
    lines = [
        f"# {VARIANT_LABELS[variant]} — {config.product_name}", "",
        f"- 카테고리: {ctx['category_label']}",
        f"- 타깃: {config.target_audience}",
        f"- 길이: {config.duration_sec}초",
        f"- 강조 포인트: {ctx['primary_selling_point']}",
        f"- 광고 강도: {config.intensity}/5",
        f"- 방향: {VARIANT_DIRECTIONS[variant]}",
        f"- Hook score: {hook.get('score', 0)}", "",
    ]
    for scene in scenes:
        lines += [
            f"## {scene['start_sec']}~{scene['end_sec']}초 · {scene['role']}",
            f"- 대사: {scene['spoken']}",
            f"- 자막: {scene['caption']}",
            f"- 화면: {scene['visual']}", "",
        ]
    return "\n".join(lines)


def render_storyboard_md(config: ProjectConfig, variant: str, scenes: list[dict[str, Any]]) -> str:
    lines = [f"# Storyboard — {VARIANT_LABELS[variant]} — {config.product_name}", ""]
    for scene in scenes:
        lines += [
            f"## Scene {scene['scene_no']} · {scene['start_sec']}~{scene['end_sec']}초",
            f"- 목적: {scene['role']}", f"- 화면: {scene['visual']}", f"- 카메라: {scene['camera']}",
            f"- 내레이션: {scene['spoken']}", f"- 자막: {scene['caption']}", f"- 전환: {scene['transition']}", "",
        ]
    return "\n".join(lines)


def render_strategy_md(config: ProjectConfig, legacy_data: dict[str, Any], variants: dict[str, Any]) -> str:
    ctx = config_product_context(config)
    db = legacy_data.get("db_integration", {})
    lines = [
        f"# 광고 전략 — {config.product_name}", "",
        "## 프로젝트",
        f"- Project ID: `{config.project_id}`", f"- 카테고리: {ctx['category_label']}", f"- 타깃: {config.target_audience}",
        f"- 광고 길이: {config.duration_sec}초", f"- 광고 강도: {config.intensity}/5",
        f"- 제품 설명: {config.product_description or '미입력'}", f"- 반드시 강조: {ctx['primary_selling_point']}",
        f"- Pain Point: {ctx['pain_point']}", "",
        "## DB 근거", f"- DB 연결: **{'YES' if db.get('connected') else 'NO'}**",
        f"- DB counts: `{json.dumps(db.get('counts', {}), ensure_ascii=False)}`", "",
        "## 크리에이티브 3종",
    ]
    for variant in VARIANTS:
        item = variants[variant]
        lines += [f"### {VARIANT_LABELS[variant]}", f"- 방향: {VARIANT_DIRECTIONS[variant]}", f"- 선택 Hook: {item['hook']['text']}", ""]
    lines += [
        "## 운영 원칙",
        "- 카테고리에 맞는 실제 사용 환경을 사용하고, 뷰티가 아닌 상품에 피부·제형·도포 표현을 강제로 넣지 않습니다.",
        "- 사용자가 입력한 수치·성능·효능은 집행 전에 공식 상세페이지 또는 제조사 자료로 사실 확인합니다.",
        "- 허위 후기, 가짜 희소성, 근거 없는 1위·최고·100% 표현을 사용하지 않습니다.",
    ]
    return "\n".join(lines)


def claim_hits(text: str) -> list[str]:
    lowered = (text or "").lower()
    return sorted({term for term in BANNED_CLAIMS if term.lower() in lowered})


def score_variant(hook: dict[str, Any], scenes: list[dict[str, Any]]) -> dict[str, Any]:
    hook_strength = round(min(100.0, float(hook.get("score") or 0)), 1)
    all_text = " ".join(s.get("spoken", "") + " " + s.get("caption", "") for s in scenes)
    risk_hits = claim_hits(all_text)
    scroll_stop = 92.0 if scenes and len(scenes[0].get("spoken", "")) <= 85 else 84.0
    curiosity = 90.0 if "?" in (scenes[0].get("spoken", "") if scenes else "") else 86.0
    purchase = 92.0 if any("핵심" in s.get("caption", "") or "가격" in s.get("caption", "") for s in scenes) else 84.0
    clarity = round(sum(bool(s.get("caption") and s.get("spoken")) for s in scenes) / max(1, len(scenes)) * 100, 1)
    credibility = 94.0 if not risk_hits else 60.0
    total = round(hook_strength * .30 + scroll_stop * .20 + curiosity * .15 + purchase * .15 + clarity * .10 + credibility * .10, 1)
    return {
        "hook_strength": hook_strength, "scroll_stop_power": scroll_stop, "curiosity_gap": curiosity,
        "purchase_desire": purchase, "clarity": clarity, "credibility": credibility, "total": total, "risk_hits": risk_hits,
    }


def build_compliance_report(variants: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {"status": "PASS", "banned_claims": list(BANNED_CLAIMS), "variants": {}}
    for name, item in variants.items():
        combined = " ".join(s["spoken"] + " " + s["caption"] + " " + s["visual"] for s in item["scenes"])
        hits = claim_hits(combined)
        status = "PASS" if not hits else "BLOCK"
        if hits:
            report["status"] = "BLOCK"
        report["variants"][name] = {"status": status, "hits": hits}
    return report


def generate_package(config: ProjectConfig, outdir: Path, require_db: bool = False) -> Path:
    log_status("[1/9] Content DB + Script Generator V2.4 연결 확인")
    legacy_data = call_legacy(config)
    db_connected = bool(legacy_data.get("db_integration", {}).get("connected"))
    if require_db and not db_connected:
        raise RuntimeError("Content DB is not connected or empty")

    top3 = legacy_data.get("top3") or []
    project_dir = outdir / config.project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    log_status("[2/9] project.json 생성")
    project_payload = asdict(config)
    project_payload["ad_variants"] = list(config.ad_variants)
    project_payload["created_at_kst"] = now_kst().isoformat(timespec="seconds")
    project_payload["product_analysis"] = config_product_context(config)
    project_payload["db_integration"] = legacy_data.get("db_integration", {})
    write_json(project_dir / "project.json", project_payload)

    variants: dict[str, Any] = {}
    log_status("[3/9] UGC / Product Demo / Cinematic 카테고리 중립 스크립트 생성")
    for idx, variant in enumerate(VARIANTS):
        hook = safe_hook(top3, idx, config.product_name)
        scenes = build_variant_beats(config, variant, hook, legacy_data)
        variants[variant] = {"hook": hook, "scenes": scenes}

    log_status("[4/9] strategy.md + storyboard 생성")
    write_text(project_dir / "strategy.md", render_strategy_md(config, legacy_data, variants))

    log_status("[5/9] shot_list.json 생성")
    for variant, item in variants.items():
        variant_dir = project_dir / variant
        scenes = item["scenes"]
        write_text(variant_dir / "script.md", render_script_md(config, variant, scenes, item["hook"]))
        write_text(variant_dir / "storyboard.md", render_storyboard_md(config, variant, scenes))
        write_json(variant_dir / "shot_list.json", scenes)

    log_status("[6/9] image_prompts.json + video_prompts.json 생성")
    for variant, item in variants.items():
        variant_dir = project_dir / variant
        scenes = item["scenes"]
        write_json(variant_dir / "image_prompts.json", [{"scene_no": s["scene_no"], "prompt": image_prompt(config, variant, s)} for s in scenes])
        write_json(variant_dir / "video_prompts.json", {
            model: [{"scene_no": s["scene_no"], "prompt": video_prompt(config, variant, s, model)} for s in scenes]
            for model in ("kling", "veo", "seedance")
        })

    log_status("[7/9] voiceover.txt + subtitles.srt 생성")
    for variant, item in variants.items():
        variant_dir = project_dir / variant
        scenes = item["scenes"]
        write_text(variant_dir / "voiceover.txt", "\n".join(s["spoken"] for s in scenes))
        write_text(variant_dir / "subtitles.srt", render_srt(scenes))

    log_status("[8/9] Creative Score + Compliance 검사")
    scores = {variant: score_variant(item["hook"], item["scenes"]) for variant, item in variants.items()}
    scores["recommended_variant"] = max(VARIANTS, key=lambda name: scores[name]["total"])
    compliance = build_compliance_report(variants)
    write_json(project_dir / "creative_scores.json", scores)
    write_json(project_dir / "compliance_report.json", compliance)
    if compliance["status"] != "PASS":
        raise RuntimeError(f"Compliance BLOCK: {compliance}")

    log_status("[9/9] manifest.json 생성 및 패키지 검증")
    expected = ["project.json", "strategy.md", "creative_scores.json", "compliance_report.json"]
    for variant in VARIANTS:
        expected.extend([
            f"{variant}/script.md", f"{variant}/storyboard.md", f"{variant}/shot_list.json",
            f"{variant}/image_prompts.json", f"{variant}/video_prompts.json", f"{variant}/voiceover.txt", f"{variant}/subtitles.srt",
        ])
    missing = [rel for rel in expected if not (project_dir / rel).exists()]
    manifest = {
        "milestone": "CREATIVE_PACKAGE_V1_CATEGORY_NEUTRAL",
        "status": "PASS" if not missing else "FAIL",
        "project_id": config.project_id,
        "generated_files": expected,
        "missing_files": missing,
        "recommended_variant": scores["recommended_variant"],
        "compliance_status": compliance["status"],
    }
    write_json(project_dir / "manifest.json", manifest)
    if missing:
        raise RuntimeError(f"Package validation failed; missing={missing}")
    log_status(f"CREATIVE_PACKAGE PASS: {project_dir}")
    return project_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate category-neutral Creative Package from Content DB")
    parser.add_argument("product", nargs="?", help="상품명")
    parser.add_argument("--description", default="", help="상품 설명")
    parser.add_argument("--target", default="일반 소비자", help="타깃 고객")
    parser.add_argument("--duration", type=int, choices=(15, 30, 45, 60), default=30, help="광고 길이")
    parser.add_argument("--category", default="", help="카테고리 직접 지정")
    parser.add_argument("--must-emphasize", default="", help="반드시 강조할 Selling Point")
    parser.add_argument("--features", default="", help="추가 특징")
    parser.add_argument("--pain-point", default="", help="고객 Pain Point")
    parser.add_argument("--intensity", type=int, choices=(1, 2, 3, 4, 5), default=4, help="광고 강도")
    parser.add_argument("--url", default="", help="상품 URL")
    parser.add_argument("--image", default="", help="상품 이미지 경로")
    parser.add_argument("--project-file", type=Path, help="기존 project.json으로 재생성")
    parser.add_argument("--project-id", default=None)
    parser.add_argument("--outdir", type=Path, default=ROOT / "outputs_creative")
    parser.add_argument("--require-db", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.project_file:
            config = load_project_config(args.project_file)
        else:
            if not args.product:
                raise ValueError("product is required unless --project-file is used")
            config = build_project_config(
                product_name=args.product, product_description=args.description, target_audience=args.target,
                duration_sec=args.duration, product_url=args.url, product_image=args.image, project_id=args.project_id,
                category=args.category, must_emphasize=args.must_emphasize, features=args.features,
                pain_point=args.pain_point, intensity=args.intensity,
            )
        project_dir = generate_package(config, args.outdir, require_db=args.require_db)
        print("OUTPUT_DIR=", project_dir)
        return 0
    except Exception as exc:
        tb = traceback.format_exc()
        print("ERROR:", exc)
        print(tb)
        LOGGER.error("Creative Package failed: %s\n%s", exc, tb)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
