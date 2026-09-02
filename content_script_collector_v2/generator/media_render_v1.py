from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import traceback
from pathlib import Path
from typing import Any

VARIANTS = ("ugc", "product_demo", "cinematic")


def configure_logging(root: Path) -> logging.Logger:
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("media_render_v1")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(fh)
    return logger


def log_status(logger: logging.Logger, message: str) -> None:
    print(message)
    logger.info(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def resolve_variant(project_dir: Path, requested: str) -> str:
    if requested != "recommended":
        if requested not in VARIANTS:
            raise ValueError(f"unsupported variant: {requested}")
        return requested
    scores_path = project_dir / "creative_scores.json"
    if not scores_path.exists():
        return "ugc"
    scores = load_json(scores_path)
    variant = scores.get("recommended_variant", "ugc")
    return variant if variant in VARIANTS else "ugc"


def load_package(project_dir: Path, requested_variant: str = "recommended") -> dict[str, Any]:
    project_dir = project_dir.resolve()
    required = [project_dir / "project.json", project_dir / "manifest.json"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"creative package missing files: {missing}")

    manifest = load_json(project_dir / "manifest.json")
    if manifest.get("status") != "PASS":
        raise RuntimeError(f"creative package manifest is not PASS: {manifest.get('status')}")

    variant = resolve_variant(project_dir, requested_variant)
    variant_dir = project_dir / variant
    variant_required = [
        variant_dir / "shot_list.json",
        variant_dir / "image_prompts.json",
        variant_dir / "video_prompts.json",
        variant_dir / "voiceover.txt",
        variant_dir / "subtitles.srt",
    ]
    missing = [str(p) for p in variant_required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"variant package missing files: {missing}")

    return {
        "project_dir": project_dir,
        "project": load_json(project_dir / "project.json"),
        "manifest": manifest,
        "variant": variant,
        "shots": load_json(variant_dir / "shot_list.json"),
        "image_prompts": load_json(variant_dir / "image_prompts.json"),
        "video_prompts": load_json(variant_dir / "video_prompts.json"),
        "voiceover_text": (variant_dir / "voiceover.txt").read_text(encoding="utf-8"),
        "subtitles": variant_dir / "subtitles.srt",
    }


def build_render_plan(package: dict[str, Any], video_model: str = "kling") -> dict[str, Any]:
    project_dir: Path = package["project_dir"]
    variant = package["variant"]
    project = package["project"]
    duration = int(project.get("duration_sec", 30))
    assets_dir = project_dir / "media_assets" / variant
    request_dir = project_dir / "media_requests" / variant
    final_dir = project_dir / "final"
    work_dir = project_dir / "render_work" / variant

    model_prompts = package["video_prompts"].get(video_model)
    if not model_prompts:
        available = sorted(package["video_prompts"].keys())
        raise ValueError(f"video model '{video_model}' unavailable; choose from {available}")
    counts = (len(package["shots"]), len(package["image_prompts"]), len(model_prompts))
    if len(set(counts)) != 1:
        raise ValueError(f"scene/prompt count mismatch: shots={counts[0]} images={counts[1]} videos={counts[2]}")

    scenes = []
    for shot, image_req, video_req in zip(package["shots"], package["image_prompts"], model_prompts):
        scene_no = int(shot["scene_no"])
        scenes.append({
            "scene_no": scene_no,
            "duration_sec": int(shot.get("duration_sec", shot["end_sec"] - shot["start_sec"])),
            "image_prompt": image_req["prompt"],
            "video_prompt": video_req["prompt"],
            "image_output": str((assets_dir / f"scene_{scene_no:02d}.png").relative_to(project_dir)),
            "video_output": str((assets_dir / f"scene_{scene_no:02d}.mp4").relative_to(project_dir)),
        })

    return {
        "milestone": "MEDIA_RENDER_V1",
        "project_id": project.get("project_id", project_dir.name),
        "product_name": project.get("product_name", ""),
        "variant": variant,
        "duration_sec": duration,
        "video_model": video_model,
        "paths": {
            "project_dir": str(project_dir),
            "assets_dir": str(assets_dir.relative_to(project_dir)),
            "request_dir": str(request_dir.relative_to(project_dir)),
            "work_dir": str(work_dir.relative_to(project_dir)),
            "voiceover_audio": str((assets_dir / "voiceover.mp3").relative_to(project_dir)),
            "optional_bgm": str((project_dir / "media_assets" / "bgm.mp3").relative_to(project_dir)),
            "optional_logo": str((project_dir / "media_assets" / "logo.png").relative_to(project_dir)),
            "subtitles": str(package["subtitles"].relative_to(project_dir)),
            "final_output": str((final_dir / f"{variant}_ad_{duration}s.mp4").relative_to(project_dir)),
        },
        "scenes": scenes,
    }


def export_provider_requests(project_dir: Path, plan: dict[str, Any], package: dict[str, Any]) -> list[Path]:
    request_dir = project_dir / plan["paths"]["request_dir"]
    request_dir.mkdir(parents=True, exist_ok=True)

    image_requests = [
        {
            "scene_no": s["scene_no"],
            "prompt": s["image_prompt"],
            "output": s["image_output"],
            "aspect_ratio": package["project"].get("aspect_ratio", "9:16"),
        }
        for s in plan["scenes"]
    ]
    video_requests = [
        {
            "scene_no": s["scene_no"],
            "model": plan["video_model"],
            "prompt": s["video_prompt"],
            "duration_sec": s["duration_sec"],
            "input_image": s["image_output"],
            "output": s["video_output"],
        }
        for s in plan["scenes"]
    ]
    tts_request = {
        "language": package["project"].get("language", "ko-KR"),
        "text": package["voiceover_text"].strip(),
        "output": plan["paths"]["voiceover_audio"],
    }

    paths = [
        request_dir / "image_requests.json",
        request_dir / "video_requests.json",
        request_dir / "tts_request.json",
    ]
    write_json(paths[0], image_requests)
    write_json(paths[1], video_requests)
    write_json(paths[2], tts_request)
    return paths


def export_asset_readme(project_dir: Path, plan: dict[str, Any]) -> Path:
    assets_dir = project_dir / plan["paths"]["assets_dir"]
    lines = [
        "# MEDIA_RENDER_V1 자산 배치 규칙",
        "",
        "외부 이미지/영상/TTS Provider에서 생성한 파일을 아래 이름으로 저장합니다.",
        "",
    ]
    for scene in plan["scenes"]:
        lines.append(f"- Scene {scene['scene_no']:02d}: `{scene['video_output']}` (이미지 선택: `{scene['image_output']}`)")
    lines += [
        f"- Voiceover: `{plan['paths']['voiceover_audio']}`",
        f"- BGM(선택): `{plan['paths']['optional_bgm']}`",
        f"- Logo(선택): `{plan['paths']['optional_logo']}`",
        "",
        "필수 영상 Scene과 voiceover.mp3가 준비되면 `--execute`로 FFmpeg 합성을 실행할 수 있습니다.",
    ]
    path = assets_dir / "README_KO.md"
    write_text(path, "\n".join(lines))
    return path


def build_readiness(project_dir: Path, plan: dict[str, Any], ffmpeg_bin: str = "ffmpeg") -> dict[str, Any]:
    ffmpeg_path = shutil.which(ffmpeg_bin)
    scene_files = [project_dir / s["video_output"] for s in plan["scenes"]]
    voice = project_dir / plan["paths"]["voiceover_audio"]
    subtitles = project_dir / plan["paths"]["subtitles"]
    missing_scenes = [str(p.relative_to(project_dir)) for p in scene_files if not p.exists()]
    return {
        "ffmpeg": ffmpeg_path,
        "ffmpeg_ready": bool(ffmpeg_path),
        "missing_scene_videos": missing_scenes,
        "voiceover_ready": voice.exists(),
        "subtitles_ready": subtitles.exists(),
        "bgm_ready": (project_dir / plan["paths"]["optional_bgm"]).exists(),
        "logo_ready": (project_dir / plan["paths"]["optional_logo"]).exists(),
        "ready_to_render": bool(ffmpeg_path) and not missing_scenes and voice.exists() and subtitles.exists(),
    }


def quote_concat_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "'\\''")


def prepare_concat_file(project_dir: Path, plan: dict[str, Any]) -> Path:
    work_dir = project_dir / plan["paths"]["work_dir"]
    work_dir.mkdir(parents=True, exist_ok=True)
    concat = work_dir / "scenes.txt"
    lines = [f"file '{quote_concat_path(project_dir / s['video_output'])}'" for s in plan["scenes"]]
    write_text(concat, "\n".join(lines))
    return concat


def run_ffmpeg(command: list[str], cwd: Path, logger: logging.Logger) -> None:
    log_status(logger, "FFMPEG: " + " ".join(command))
    result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.stdout:
        logger.info(result.stdout)
    if result.returncode != 0:
        logger.error(result.stderr)
        raise RuntimeError(f"ffmpeg failed ({result.returncode}): {result.stderr[-2000:]}")


def render_final(project_dir: Path, plan: dict[str, Any], ffmpeg_bin: str = "ffmpeg") -> Path:
    logger = configure_logging(project_dir)
    readiness = build_readiness(project_dir, plan, ffmpeg_bin)
    if not readiness["ready_to_render"]:
        raise RuntimeError(f"not ready to render: {readiness}")

    work_dir = project_dir / plan["paths"]["work_dir"]
    work_dir.mkdir(parents=True, exist_ok=True)
    concat_file = prepare_concat_file(project_dir, plan)
    concat_mp4 = work_dir / "01_concat.mp4"
    audio_mp4 = work_dir / "02_audio.mp4"
    logo_mp4 = work_dir / "03_logo.mp4"
    final_output = project_dir / plan["paths"]["final_output"]
    final_output.parent.mkdir(parents=True, exist_ok=True)

    run_ffmpeg([
        ffmpeg_bin, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-an", str(concat_mp4)
    ], project_dir, logger)

    voice = project_dir / plan["paths"]["voiceover_audio"]
    bgm = project_dir / plan["paths"]["optional_bgm"]
    duration = int(plan["duration_sec"])
    if bgm.exists():
        audio_filter = (
            f"[1:a]apad=pad_dur={duration},atrim=0:{duration},volume=1.0[vo];"
            f"[2:a]atrim=0:{duration},volume=0.12[bg];"
            "[vo][bg]amix=inputs=2:duration=first[a]"
        )
        run_ffmpeg([
            ffmpeg_bin, "-y", "-i", str(concat_mp4), "-i", str(voice), "-stream_loop", "-1", "-i", str(bgm),
            "-filter_complex", audio_filter,
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-t", str(duration), str(audio_mp4)
        ], project_dir, logger)
    else:
        run_ffmpeg([
            ffmpeg_bin, "-y", "-i", str(concat_mp4), "-i", str(voice),
            "-filter_complex", f"[1:a]apad=pad_dur={duration},atrim=0:{duration}[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-t", str(duration), str(audio_mp4)
        ], project_dir, logger)

    video_for_subtitles = audio_mp4
    logo = project_dir / plan["paths"]["optional_logo"]
    if logo.exists():
        run_ffmpeg([
            ffmpeg_bin, "-y", "-i", str(audio_mp4), "-i", str(logo),
            "-filter_complex", "[1:v]scale=-1:120[logo];[0:v][logo]overlay=W-w-24:H-h-24[v]",
            "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-c:a", "copy", "-shortest", str(logo_mp4)
        ], project_dir, logger)
        video_for_subtitles = logo_mp4

    subtitle_rel = Path(plan["paths"]["subtitles"]).as_posix().replace("'", "\\'")
    run_ffmpeg([
        ffmpeg_bin, "-y", "-i", str(video_for_subtitles),
        "-vf", f"subtitles='{subtitle_rel}'", "-c:v", "libx264", "-c:a", "copy", str(final_output)
    ], project_dir, logger)
    return final_output


def prepare_media_render(project_dir: Path, variant: str, video_model: str, ffmpeg_bin: str) -> dict[str, Any]:
    logger = configure_logging(project_dir)
    log_status(logger, "[1/5] Creative Package V1 검증")
    package = load_package(project_dir, variant)
    log_status(logger, "[2/5] MEDIA_RENDER_V1 render_plan 생성")
    plan = build_render_plan(package, video_model)
    write_json(project_dir / "render_plan.json", plan)
    log_status(logger, "[3/5] Image / Video / TTS Provider 요청 파일 생성")
    export_provider_requests(project_dir, plan, package)
    export_asset_readme(project_dir, plan)
    log_status(logger, "[4/5] FFmpeg + 미디어 자산 readiness 검사")
    readiness = build_readiness(project_dir, plan, ffmpeg_bin)
    write_json(project_dir / "render_readiness.json", readiness)
    log_status(logger, f"[5/5] MEDIA_RENDER_V1 PREPARED ready_to_render={readiness['ready_to_render']}")
    return {"package": package, "plan": plan, "readiness": readiness}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare/render MEDIA_RENDER_V1 from Creative Package V1")
    parser.add_argument("project_dir", type=Path, help="CREATIVE_PACKAGE_V1 project folder")
    parser.add_argument("--variant", choices=("recommended",) + VARIANTS, default="recommended")
    parser.add_argument("--video-model", default="kling")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--execute", action="store_true", help="Run FFmpeg only when all required assets exist")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project_dir = args.project_dir.resolve()
        result = prepare_media_render(project_dir, args.variant, args.video_model, args.ffmpeg)
        if args.execute:
            output = render_final(project_dir, result["plan"], args.ffmpeg)
            print("FINAL_OUTPUT=", output)
        else:
            print("RENDER_PLAN=", project_dir / "render_plan.json")
            print("READINESS=", project_dir / "render_readiness.json")
        return 0
    except Exception as exc:
        tb = traceback.format_exc()
        print("ERROR:", exc)
        print(tb)
        try:
            logger = configure_logging(args.project_dir.resolve())
            logger.error("MEDIA_RENDER_V1 failed: %s\n%s", exc, tb)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
