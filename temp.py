#!/usr/bin/env python3
import argparse
import os
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


def unique_dest(path: Path) -> Path:
    if not path.exists():
        return path

    parent = path.parent
    stem = path.name
    i = 1
    while True:
        candidate = parent / f"{stem}.moved-{i}"
        if not candidate.exists():
            return candidate
        i += 1


def main():
    parser = argparse.ArgumentParser(
        description="Recover files accidentally unzipped into HOME by moving zip-listed paths elsewhere."
    )
    parser.add_argument("zipfile", help="Path to the original .zip file")
    parser.add_argument(
        "--base",
        default=str(Path.home()),
        help="Where the zip was accidentally extracted. Default: your HOME directory",
    )
    parser.add_argument(
        "--dest",
        default=str(Path.home() / "unzipped_recovered"),
        help="Directory to move recovered files into",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move files. Without this, only preview actions.",
    )

    args = parser.parse_args()

    zip_path = Path(args.zipfile).expanduser().resolve()
    base = Path(args.base).expanduser().resolve()
    dest = Path(args.dest).expanduser().resolve()

    if not zip_path.exists():
        print(f"ERROR: zip file not found: {zip_path}", file=sys.stderr)
        sys.exit(1)

    if not base.exists():
        print(f"ERROR: base directory not found: {base}", file=sys.stderr)
        sys.exit(1)

    if dest == base or base in dest.parents:
        print(f"Destination: {dest}")
    else:
        print("WARNING: destination is not inside base/HOME. This is okay, but please verify.")

    print(f"Zip:  {zip_path}")
    print(f"Base: {base}")
    print(f"Dest: {dest}")
    print()

    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()

    files = []
    dirs = set()
    skipped = []

    for info in infos:
        name = info.filename

        if not is_safe_zip_path(name):
            skipped.append(name)
            continue

        p = PurePosixPath(name)

        if name.endswith("/"):
            dirs.add(p)
            continue

        files.append(p)

        for parent in p.parents:
            if str(parent) != ".":
                dirs.add(parent)

    moved = 0
    missing = 0
    collisions = 0

    print("Files to move:")
    for rel in files:
        src = base / Path(*rel.parts)
        dst = dest / Path(*rel.parts)

        if not src.exists() and not src.is_symlink():
            print(f"  MISSING: {src}")
            missing += 1
            continue

        final_dst = unique_dest(dst)
        if final_dst != dst:
            collisions += 1

        print(f"  MOVE: {src} -> {final_dst}")

        if args.apply:
            final_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(final_dst))

        moved += 1

    print()
    print("Empty directories to remove after moving files:")
    for rel in sorted(dirs, key=lambda x: len(x.parts), reverse=True):
        d = base / Path(*rel.parts)
        print(f"  RMDIR-IF-EMPTY: {d}")

        if args.apply:
            try:
                d.rmdir()
            except OSError:
                pass

    if skipped:
        print()
        print("Skipped unsafe zip paths:")
        for s in skipped:
            print(f"  {s}")

    print()
    if args.apply:
        print("Done.")
    else:
        print("Preview only. Nothing was moved.")
        print("Run again with --apply after checking the MOVE lines.")

    print()
    print(f"Files listed for moving: {moved}")
    print(f"Missing files: {missing}")
    print(f"Destination name collisions renamed: {collisions}")


if __name__ == "__main__":
    main()