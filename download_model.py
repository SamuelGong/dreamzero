#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path


DEFAULT_MIRROR_ENDPOINT = "https://hf-mirror.com"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download a Hugging Face model repo into the local Hugging Face cache and print the snapshot path."
    )
    parser.add_argument(
        "repo_id",
        help="Hugging Face repo id, e.g. GEAR-Dreams/DreamZero-DROID",
    )
    parser.add_argument(
        "--revision",
        default=None,
        help="Branch, tag, or commit hash. Default: Hugging Face default branch.",
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help=(
            "Optional Hugging Face cache directory. "
            "If omitted, uses HF_HOME/HF_HUB_CACHE or the default ~/.cache/huggingface/hub."
        ),
    )
    parser.add_argument(
        "--token",
        default=None,
        help=(
            "Optional Hugging Face token. "
            "If omitted, uses the logged-in token or HF_TOKEN environment variable."
        ),
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Do not download; only resolve from existing local cache.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Number of parallel download workers. Default: 8.",
    )
    parser.add_argument(
        "--use-mirror",
        action="store_true",
        help=f"Use Hugging Face mirror endpoint: {DEFAULT_MIRROR_ENDPOINT}",
    )
    parser.add_argument(
        "--mirror-endpoint",
        default=DEFAULT_MIRROR_ENDPOINT,
        help=f"Mirror endpoint to use when --use-mirror is set. Default: {DEFAULT_MIRROR_ENDPOINT}",
    )

    args = parser.parse_args()

    if args.use_mirror:
        os.environ["HF_ENDPOINT"] = args.mirror_endpoint

    try:
        # Important: import after setting HF_ENDPOINT.
        from huggingface_hub import snapshot_download

        path = snapshot_download(
            repo_id=args.repo_id,
            revision=args.revision,
            cache_dir=args.cache_dir,
            token=args.token,
            local_files_only=args.local_files_only,
            max_workers=args.max_workers,
        )
    except Exception as exc:
        print(f"[ERROR] Failed to download or resolve repo: {args.repo_id}", file=sys.stderr)
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    path = Path(path).resolve()

    print("Download complete.")
    print(f"Repo ID: {args.repo_id}")
    if args.revision:
        print(f"Revision: {args.revision}")
    if args.use_mirror:
        print(f"Mirror endpoint: {args.mirror_endpoint}")
    print(f"Snapshot path: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
