from __future__ import annotations
import argparse, json, shutil, sys
from collections import Counter
from pathlib import Path

# Reuse the collector's clone/update logic so behavior stays consistent.
from collect_and_index import clone_or_update


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def select_repos(manifest: dict, *, priority: int, include_tooling: bool, include_candidates: bool,
                 verified_only: bool, media: str | None, model: str | None,
                 min_repo_quality: int) -> list[dict]:
    repos = []
    for r in manifest.get('repos', []):
        if int(r.get('priority', 2)) > priority:
            continue
        is_candidate = (r.get('origin_status') in {'candidate', 'duplicate_excluded'} or not bool(r.get('active', True)))
        if is_candidate and not include_candidates:
            continue
        if r.get('source_kind') == 'tooling' and not include_tooling:
            continue
        if r.get('source_kind') == 'watchlist' and not include_candidates:
            continue
        if verified_only and r.get('origin_status') != 'verified_original':
            continue
        if media and r.get('media_type') != media:
            continue
        if model and model.lower() not in str(r.get('model_family', '')).lower():
            continue
        if int(float(r.get('repo_quality_score', 0) or 0)) < min_repo_quality:
            continue
        repos.append(r)
    return repos


def main() -> int:
    ap = argparse.ArgumentParser(description='Download/update AI prompt repositories only (no indexing).')
    ap.add_argument('--root', default='AI_PROMPT_LIBRARY')
    ap.add_argument('--manifest', default=str(Path(__file__).with_name('repos_manifest.json')))
    ap.add_argument('--priority', type=int, default=3, choices=[1, 2, 3])
    ap.add_argument('--include-tooling', action='store_true', help='Include prompt generators/enhancers/skills.')
    ap.add_argument('--include-candidates', action='store_true', help='Also include watchlist/candidate repositories.')
    ap.add_argument('--verified-only', action='store_true', help='Only repositories explicitly verified as fork=false originals.')
    ap.add_argument('--media', choices=['image', 'video'])
    ap.add_argument('--model', help='Substring filter for model_family, e.g. qwen, ltx, seedance.')
    ap.add_argument('--min-repo-quality', type=int, default=0)
    ap.add_argument('--retries', type=int, default=4)
    ap.add_argument('--retry-delay', type=int, default=5)
    ap.add_argument('--clone-timeout', type=int, default=1200)
    ap.add_argument('--no-pull', action='store_true', help='Reuse already-downloaded repositories without git pull.')
    ap.add_argument('--text-only-clone', action='store_true', help='Sparse-checkout only prompt-friendly text files; skips heavy image/video assets.')
    args = ap.parse_args()

    if not shutil.which('git'):
        print('ERROR: Git is not installed or not on PATH.', file=sys.stderr)
        return 2

    root = Path(args.root).resolve()
    (root / 'repos').mkdir(parents=True, exist_ok=True)
    (root / 'logs').mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(Path(args.manifest))

    repos = select_repos(
        manifest,
        priority=args.priority,
        include_tooling=args.include_tooling,
        include_candidates=args.include_candidates,
        verified_only=args.verified_only,
        media=args.media,
        model=args.model,
        min_repo_quality=args.min_repo_quality,
    )

    print(f'Selected repositories: {len(repos)}')
    print('By source kind:', dict(Counter(r.get('source_kind', 'corpus') for r in repos)))
    print('By media type:', dict(Counter(r.get('media_type', 'unknown') for r in repos)))

    statuses = []
    status_path = root / 'logs' / 'clone_status_download_only.json'
    for n, r in enumerate(repos, 1):
        print(f'[{n}/{len(repos)}] {r["repo"]} [{r.get("source_kind", "corpus")}]')
        st = clone_or_update(
            r,
            root,
            full=True,
            retries=args.retries,
            retry_delay=args.retry_delay,
            clone_timeout=args.clone_timeout,
            no_pull=args.no_pull,
            text_only=args.text_only_clone,
        )
        statuses.append(st)
        print(' ', st.get('status', 'unknown'), 'attempts=', st.get('attempts', 0))
        status_path.write_text(json.dumps(statuses, ensure_ascii=False, indent=2), encoding='utf-8')

    summary = {
        'version': '6.0-download-only',
        'repos_selected': len(repos),
        'repos_ok': sum(1 for s in statuses if s.get('status') in {'cloned', 'updated', 'ok', 'exists', 'unchanged'}),
        'repos_failed': sum(1 for s in statuses if s.get('status') not in {'cloned', 'updated', 'ok', 'exists', 'unchanged'}),
        'include_tooling': bool(args.include_tooling),
        'include_candidates': bool(args.include_candidates),
        'verified_only': bool(args.verified_only),
        'media_filter': args.media,
        'model_filter': args.model,
        'min_repo_quality': args.min_repo_quality,
        'text_only_clone': bool(args.text_only_clone),
        'source_kind_counts': dict(Counter(r.get('source_kind', 'corpus') for r in repos)),
        'media_counts': dict(Counter(r.get('media_type', 'unknown') for r in repos)),
    }
    summary_path = root / 'logs' / 'download_only_summary.json'
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f'\nSaved status: {status_path}')
    print(f'Saved summary: {summary_path}')
    return 0 if summary['repos_failed'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
