from __future__ import annotations

import argparse
import json
import logging
import re
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import script_generator_v2 as legacy

ROOT = Path(__file__).resolve().parents[1]
KST = timezone(timedelta(hours=9))
VARIANTS = ("ugc", "product_demo", "cinematic")
BANNED_CLAIMS = (
    "치료", "완치", "주름 제거", "여드름 치료", "100%", "즉시 효과", "완전히 사라",
)

VARIANT_LABELS = {
    "ugc": "UGC 후기형",
    "product_demo": "Product Demo 제품 시연형",
    "cinematic": "Cinematic 브랜드형",
}

VARIANT_DIRECTIONS = {
    "ugc": "실사용자가 직접 발견한 루틴처럼 자연스럽고 신뢰감 있게",
    "product_demo": "제품 제형·사용법·사용감이 한눈에 이해되도록 명확하게",
    "cinematic": "제품의 질감과 라이프스타일을 프리미엄 브랜드 무드로",
}

CAMERA_BY_VARIANT = {
    "ugc": ["handheld close-up", "mirror medium shot", "POV product reveal", "macro texture", "handheld application", "close-up reaction", "clean end card"],
    "product_demo": ["tight product close-up", "top-down setup", "macro dispenser", "macro texture swipe", "side application close-up", "comparison detail shot", "packshot end card"],
    "cinematic": ["cinematic portrait close-up", "slow dolly detail", "hero product reveal", "extreme macro texture", "slow ritual close-up", "soft lifestyle medium shot", "premium packshot"],
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


def configure_logging() -> logging.Logger:
    log_dir = ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("creative_package_v1")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)
    return logger


LOGGER = configure_logging()


def log_status(message: str) -> None:
    print(message)
    LOGGER.info(message)


def slugify(text: str) -> str:
    value = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", (text or "").strip()).strip("_")
    return value or "project"


def now_kst() -> datetime:
    return datetime.now(KST)


def build_project_config(
    product_name: str,
    product_description: str = "",
    target_audience: str = "일반 소비자",
    duration_sec: int = 30,
    product_url: str = "",
    product_image: str = "",
    project_id: str | None = None,
) -> ProjectConfig:
    product_name = (product_name or "").strip()
    if not product_name:
        raise ValueError("product_name is required")
    if duration_sec not in (15, 30, 60):
        raise ValueError("duration_sec must be one of 15, 30, 60")
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
    weights = [10, 14, 14, 16, 16, 16, 14]
    if count != len(weights):
        weights = [1] * count
    cumulative = 0
    starts = [0]
    for weight in weights[:-1]:
        cumulative += weight
        starts.append(round(duration_sec * cumulative / sum(weights)))
    ends = starts[1:] + [duration_sec]
    timeline = list(zip(starts, ends))
    if timeline[-1][1] != duration_sec:
        raise AssertionError("timeline does not end at requested duration")
    return timeline


def safe_hook(top3: list[dict[str, Any]], index: int, product: str) -> dict[str, Any]:
    if top3:
        return top3[index % len(top3)]
    return {
        "rank": index + 1,
        "text": f"{product}, 사용 전에 이 포인트부터 확인해보세요.",
        "category": "curiosity",
        "score": 80.0,
        "risk": 0,
        "db_source_id": None,
        "db_hook_id": None,
    }


def build_variant_beats(config: ProjectConfig, variant: str, hook: dict[str, Any], legacy_data: dict[str, Any]) -> list[dict[str, Any]]:
    product = config.product_name
    desc = config.product_description or "제품 특징과 사용감을 확인"
    target = config.target_audience
    cta = legacy_data.get("cta") or "제품 정보와 사용법을 확인해보세요."

    if variant == "ugc":
        content = [
            ("HOOK", hook["text"], hook["text"], f"{target} 사용자가 카메라를 보며 {product}을 들어 보인다."),
            ("PROBLEM", f"저는 {product}를 고를 때 광고 문구보다 제 루틴에 잘 맞는지부터 봅니다.", "내 루틴에 맞는지부터", "거울 앞에서 피부 상태를 확인하는 자연스러운 일상 컷."),
            ("DISCOVERY", f"제가 먼저 본 건 {desc} 같은 제품 특징과 실제 사용 순서였습니다.", "특징 + 사용 순서 확인", f"{product} 패키지를 손에 들고 라벨과 사용법을 확인한다."),
            ("DEMO", "처음에는 손등에 소량 덜어 제형을 확인하고 얼굴에는 나눠 발라봅니다.", "소량 · 제형 · 나눠 바르기", f"{product} 한 방울을 손등에 덜어 제형을 보여준 뒤 볼에 소량 도포."),
            ("EXPERIENCE", "바른 뒤에는 끈적임, 밀림, 당김 같은 사용감을 체크해봅니다.", "끈적임 · 밀림 · 당김 체크", "손끝으로 피부 표면을 가볍게 터치하며 사용감을 확인한다."),
            ("PROOF_SAFE", "한 번의 과장된 변화보다 며칠 동안 내 루틴과 잘 맞는지 기록하며 비교해보세요.", "과장보다 루틴 적합성", "같은 조명과 같은 구도에서 데일리 루틴을 기록하는 화면."),
            ("CTA", cta, "제품 정보·주의사항 확인", f"{product}과 깔끔한 제품 정보 화면으로 마무리."),
        ]
    elif variant == "product_demo":
        content = [
            ("HOOK", hook["text"], hook["text"], f"{product}을 프레임 중앙에 크게 보여준다."),
            ("SETUP", f"{product}에서 먼저 확인할 것은 제품 특징, 제형, 그리고 사용 방법입니다.", "특징 · 제형 · 사용법", "제품과 핵심 체크 포인트를 상단 촬영으로 정리한다."),
            ("DISPENSE", "용기에서 소량을 덜어 실제 토출량을 먼저 보여드릴게요.", "실제 토출량 확인", f"펌프 또는 드로퍼에서 {product}을 정확히 한 번 덜어낸다."),
            ("TEXTURE", f"손등에서 펴 발라 {desc}와 관련된 제형 특성을 과장 없이 보여줍니다.", "제형을 가까이 확인", "매크로 촬영으로 펴 발리는 질감과 잔여감을 보여준다."),
            ("APPLICATION", "얼굴에는 소량씩 나눠 바르고 다른 제품과 함께 쓸 때 밀림도 확인합니다.", "소량씩 나눠 사용", "볼과 이마에 소량씩 점을 찍어 부드럽게 펴 바른다."),
            ("CHECK", "마무리 후에는 광택만 보지 말고 끈적임과 당김 등 실제 사용감을 같이 확인하세요.", "사용감까지 체크", "같은 조명 아래에서 피부 표면과 손끝 반응을 보여준다."),
            ("CTA", cta, "제품 페이지에서 상세 확인", f"{product} 정면 패키지와 간결한 CTA 엔드카드."),
        ]
    elif variant == "cinematic":
        content = [
            ("HOOK", hook["text"], hook["text"], "부드러운 빛 속 인물의 피부와 제품 실루엣을 짧게 교차한다."),
            ("MOOD", f"매일 반복하는 루틴에서 {product}은 복잡함보다 꾸준히 쓰기 좋은 경험을 목표로 합니다.", "매일의 루틴을 더 단순하게", "아침 빛이 들어오는 세면대와 정돈된 스킨케어 장면."),
            ("REVEAL", f"{product}의 디자인과 {desc} 포인트를 차분한 제품 히어로 컷으로 보여줍니다.", "제품의 핵심을 한눈에", f"천천히 회전하는 {product} 패키지와 라벨 디테일."),
            ("TEXTURE", "한 방울의 제형과 퍼지는 움직임을 매크로로 담아 실제 질감을 강조합니다.", "한 방울의 질감", "극근접 촬영으로 제형이 표면에 닿고 퍼지는 순간을 보여준다."),
            ("RITUAL", "얼굴에는 필요한 만큼만 덜어 천천히 흡수시키며 루틴을 이어갑니다.", "필요한 만큼, 차분하게", "슬로우한 손동작으로 볼과 이마에 제품을 펴 바른다."),
            ("LIFESTYLE", "과장된 변신보다 매일 부담 없이 이어갈 수 있는 사용 경험을 보여줍니다.", "매일 이어지는 사용 경험", "자연광 아래 준비를 마친 인물의 편안한 표정과 일상 컷."),
            ("CTA", cta, "제품 정보 확인", f"프리미엄 라이팅의 {product} 팩샷으로 마무리."),
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
    direction = VARIANT_DIRECTIONS[variant]
    return (
        f"Vertical {config.aspect_ratio} Korean beauty advertising still for {config.product_name}. "
        f"Audience: {config.target_audience}. Creative direction: {direction}. "
        f"Scene purpose: {scene['role']}. Visual: {scene['visual']} "
        f"Camera composition: {scene['camera']}. Natural realistic skin texture, premium clean environment, "
        "soft controlled lighting, readable product-focused composition, consistent product packaging, "
        "no medical claim visualization, no exaggerated before-and-after transformation, no text baked into image."
    )


def video_prompt(config: ProjectConfig, variant: str, scene: dict[str, Any], model: str) -> str:
    base = (
        f"Vertical {config.aspect_ratio} Korean beauty short-form ad for {config.product_name}. "
        f"Duration about {scene['duration_sec']} seconds. Creative direction: {VARIANT_DIRECTIONS[variant]}. "
        f"Scene purpose: {scene['role']}. Action: {scene['visual']} Camera: {scene['camera']}. "
        "Natural realistic skin texture, consistent product label, subtle authentic hand motion, premium clean lighting, "
        "no medical claims, no exaggerated transformation."
    )
    suffix = {
        "kling": " Controlled motion, realistic physics, stable identity and packaging, smooth social-ad pacing.",
        "veo": " Cinematic lensing, gentle camera movement, coherent continuity, realistic liquid physics and room ambience.",
        "seedance": " Strong first frame, concise motion, dynamic but stable camera movement, clean product-hand interaction.",
    }.get(model, " Natural motion and continuity.")
    return base + suffix


def format_timestamp(seconds: int) -> str:
    hours, rem = divmod(max(0, int(seconds)), 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},000"


def render_srt(scenes: list[dict[str, Any]]) -> str:
    blocks = []
    for index, scene in enumerate(scenes, 1):
        blocks.append(
            f"{index}\n{format_timestamp(scene['start_sec'])} --> {format_timestamp(scene['end_sec'])}\n{scene['caption']}"
        )
    return "\n\n".join(blocks) + "\n"


def render_script_md(config: ProjectConfig, variant: str, scenes: list[dict[str, Any]], hook: dict[str, Any]) -> str:
    lines = [
        f"# {VARIANT_LABELS[variant]} — {config.product_name}", "",
        f"- 타깃: {config.target_audience}",
        f"- 길이: {config.duration_sec}초",
        f"- 방향: {VARIANT_DIRECTIONS[variant]}",
        f"- Hook score: {hook.get('score', 0)}",
        f"- DB Hook: hook_id={hook.get('db_hook_id')} / source_id={hook.get('db_source_id')}", "",
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
            f"- 목적: {scene['role']}",
            f"- 화면: {scene['visual']}",
            f"- 카메라: {scene['camera']}",
            f"- 내레이션: {scene['spoken']}",
            f"- 자막: {scene['caption']}",
            f"- 전환: {scene['transition']}", "",
        ]
    return "\n".join(lines)


def render_strategy_md(config: ProjectConfig, legacy_data: dict[str, Any], variants: dict[str, Any]) -> str:
    db = legacy_data.get("db_integration", {})
    lines = [
        f"# 광고 전략 — {config.product_name}", "",
        "## 프로젝트",
        f"- Project ID: `{config.project_id}`",
        f"- 타깃: {config.target_audience}",
        f"- 광고 길이: {config.duration_sec}초",
        f"- 제품 설명: {config.product_description or '미입력'}",
        f"- 화면비: {config.aspect_ratio}", "",
        "## DB 근거",
        f"- DB 연결: **{'YES' if db.get('connected') else 'NO'}**",
        f"- DB counts: `{json.dumps(db.get('counts', {}), ensure_ascii=False)}`",
        f"- TOP3 다양성: `{db.get('top3_diversity', {})}`", "",
        "## 크리에이티브 3종",
    ]
    for variant in VARIANTS:
        item = variants[variant]
        lines += [
            f"### {VARIANT_LABELS[variant]}",
            f"- 방향: {VARIANT_DIRECTIONS[variant]}",
            f"- 선택 Hook: {item['hook']['text']}",
            f"- Hook score: {item['hook'].get('score', 0)}", "",
        ]
    lines += [
        "## 운영 원칙",
        "- 치료·완치·확정적 효능 표현은 생성 단계에서 차단 대상으로 검사합니다.",
        "- 전후 비교는 과장된 변신 연출 대신 동일 조건의 사용 경험 비교로 제한합니다.",
        "- 실제 집행 전 제품 상세정보·표시광고 문구·플랫폼 정책을 최종 확인합니다.",
    ]
    return "\n".join(lines)


def claim_hits(text: str) -> list[str]:
    lowered = (text or "").lower()
    return sorted({term for term in BANNED_CLAIMS if term.lower() in lowered})


def score_variant(hook: dict[str, Any], scenes: list[dict[str, Any]]) -> dict[str, Any]:
    hook_strength = round(min(100.0, float(hook.get("score") or 0)), 1)
    cta_text = scenes[-1]["spoken"] if scenes else ""
    cta_clarity = 92.0 if any(x in cta_text for x in ("확인", "저장", "댓글", "제품")) else 78.0
    product_focus = round(sum(1 for s in scenes if s.get("visual")) / max(1, len(scenes)) * 100, 1)
    clarity = round(sum(1 for s in scenes if s.get("caption") and s.get("spoken")) / max(1, len(scenes)) * 100, 1)
    all_text = " ".join(s.get("spoken", "") + " " + s.get("caption", "") for s in scenes)
    risk_hits = claim_hits(all_text)
    safety = 100.0 if not risk_hits else 50.0
    total = round(hook_strength * .30 + cta_clarity * .20 + product_focus * .20 + clarity * .15 + safety * .15, 1)
    return {
        "hook_strength": hook_strength,
        "cta_clarity": cta_clarity,
        "product_focus": product_focus,
        "clarity": clarity,
        "claim_safety": safety,
        "total": total,
        "risk_hits": risk_hits,
    }


def build_compliance_report(variants: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {"status": "PASS", "banned_claims": list(BANNED_CLAIMS), "variants": {}}
    for name, item in variants.items():
        combined = " ".join(
            s["spoken"] + " " + s["caption"] + " " + s["visual"] for s in item["scenes"]
        )
        hits = claim_hits(combined)
        status = "PASS" if not hits else "BLOCK"
        if hits:
            report["status"] = "BLOCK"
        report["variants"][name] = {"status": status, "hits": hits}
    return report


def generate_package(config: ProjectConfig, outdir: Path, require_db: bool = False) -> Path:
    log_status("[1/9] 기존 Content DB + Script Generator 연결 확인")
    legacy_data = legacy.generate(config.product_name)
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
    project_payload["db_integration"] = legacy_data.get("db_integration", {})
    write_json(project_dir / "project.json", project_payload)

    variants: dict[str, Any] = {}
    log_status("[3/9] UGC / Product Demo / Cinematic 3종 스크립트 생성")
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
        image_prompts = [
            {"scene_no": s["scene_no"], "prompt": image_prompt(config, variant, s)} for s in scenes
        ]
        video_prompts = {
            model: [
                {"scene_no": s["scene_no"], "prompt": video_prompt(config, variant, s, model)} for s in scenes
            ]
            for model in ("kling", "veo", "seedance")
        }
        write_json(variant_dir / "image_prompts.json", image_prompts)
        write_json(variant_dir / "video_prompts.json", video_prompts)

    log_status("[7/9] voiceover.txt + subtitles.srt 생성")
    for variant, item in variants.items():
        variant_dir = project_dir / variant
        scenes = item["scenes"]
        voiceover = "\n".join(s["spoken"] for s in scenes)
        write_text(variant_dir / "voiceover.txt", voiceover)
        write_text(variant_dir / "subtitles.srt", render_srt(scenes))

    log_status("[8/9] 광고 점수 + 금지 표현 Compliance 검사")
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
            f"{variant}/image_prompts.json", f"{variant}/video_prompts.json",
            f"{variant}/voiceover.txt", f"{variant}/subtitles.srt",
        ])
    missing = [rel for rel in expected if not (project_dir / rel).exists()]
    manifest = {
        "milestone": "CREATIVE_PACKAGE_V1",
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

    log_status(f"CREATIVE_PACKAGE_V1 PASS: {project_dir}")
    return project_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Creative Package V1 from Content DB")
    parser.add_argument("product", nargs="?", help="상품명")
    parser.add_argument("--description", default="", help="상품 설명")
    parser.add_argument("--target", default="일반 소비자", help="타깃 고객")
    parser.add_argument("--duration", type=int, choices=(15, 30, 60), default=30, help="광고 길이")
    parser.add_argument("--url", default="", help="상품 URL (메타데이터 저장용)")
    parser.add_argument("--image", default="", help="상품 이미지 경로 (메타데이터 저장용)")
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
                product_name=args.product,
                product_description=args.description,
                target_audience=args.target,
                duration_sec=args.duration,
                product_url=args.url,
                product_image=args.image,
                project_id=args.project_id,
            )
        project_dir = generate_package(config, args.outdir, require_db=args.require_db)
        print("OUTPUT_DIR=", project_dir)
        return 0
    except Exception as exc:
        tb = traceback.format_exc()
        print("ERROR:", exc)
        print(tb)
        LOGGER.error("Creative Package V1 failed: %s\n%s", exc, tb)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
