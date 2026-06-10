#!/usr/bin/env python3
import argparse
import shutil
import sys
import zipfile
from pathlib import Path, PurePosixPath


def is_safe_zip_path(name: str) -> bool:
    p = PurePosixPath(name)
    if p.is_absolute():
        return False
    if any(part in ("..", "") for part in p.parts):
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Undo accidental .moved-N suffixes created by the previous recovery script."
    )
    parser.add_argument("zipfile", help="Path to the original .zip file")
    parser.add_argument(
        "--base",
        required=True,
        help="Directory where the files were accidentally renamed, e.g. /data8/jiangzhifeng",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually rename files back. Without this, only preview.",
    )
    parser.add_argument(
        "--max-suffix",
        type=int,
        default=20,
        help="Check suffixes .moved-1 through .moved-N. Default: 20",
    )

    args = parser.parse_args()

    zip_path = Path(args.zipfile).expanduser().resolve()
    base = Path(args.base).expanduser().resolve()

    if not zip_path.exists():
        print(f"ERROR: zip file not found: {zip_path}", file=sys.stderr)
        sys.exit(1)

    if not base.exists():
        print(f"ERROR: base directory not found: {base}", file=sys.stderr)
        sys.exit(1)

    print(f"Zip:  {zip_path}")
    print(f"Base: {base}")
    print()

    restored = 0
    skipped_exists = 0
    missing = 0
    ambiguous = 0

    with zipfile.ZipFile(zip_path) as zf:
        names = [info.filename for info in zf.infolist()]

    # 去重，避免 zip 里重复路径导致重复处理
    seen = set()

    for name in names:
        if name.endswith("/"):
            continue

        if not is_safe_zip_path(name):
            print(f"SKIP unsafe zip path: {name}")
            continue

        rel = PurePosixPath(name)

        if rel in seen:
            continue
        seen.add(rel)

        original = base / Path(*rel.parts)

        # 如果原文件名已经存在，不动，避免覆盖
        if original.exists() or original.is_symlink():
            skipped_exists += 1
            continue

        candidates = []
        for i in range(1, args.max_suffix + 1):
            c = original.with_name(original.name + f".moved-{i}")
            if c.exists() or c.is_symlink():
                candidates.append(c)

        if not candidates:
            missing += 1
            continue

        if len(candidates) > 1:
            ambiguous += 1
            print(f"AMBIGUOUS, not restoring automatically: {original}")
            for c in candidates:
                print(f"  candidate: {c}")
            continue

        src = candidates[0]
        dst = original

        print(f"RESTORE: {src} -> {dst}")

        if args.apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

        restored += 1

    print()
    if args.apply:
        print("Done.")
    else:
        print("Preview only. Nothing was renamed.")
        print("Run again with --apply after checking the RESTORE lines.")

    print()
    print(f"Restored candidates: {restored}")
    print(f"Skipped because original name already exists: {skipped_exists}")
    print(f"Missing moved file: {missing}")
    print(f"Ambiguous: {ambiguous}")


if __name__ == "__main__":
    main()