"""Re-run the wiki response parser against saved chunk artifacts.

Used to diagnose silent content loss in the wiki generation pipeline without
re-spending model tokens. Read the artifacts produced by
`pipeline.kimi.generate_wiki(..., debug_dir=...)` and report what files each
chunk would contribute, what would get merged, and where parsing fails.

Usage:
    python -m scripts.replay_wiki_parse <debug_dir> [--show-tail N] [--show-raw <chunk_idx>]
"""
import argparse
import json
import sys
from pathlib import Path

from pipeline.kimi import _parse_wiki_response_with_meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("debug_dir", help="Directory containing chunk_NN.json artifacts")
    parser.add_argument("--show-tail", type=int, default=200,
                        help="Chars of raw response tail to show on parse failure")
    parser.add_argument("--show-raw", type=int, default=None,
                        help="Print the full raw_response for the given chunk index and exit")
    args = parser.parse_args()

    debug = Path(args.debug_dir)
    if not debug.is_dir():
        sys.exit(f"Not a directory: {debug}")

    artifacts = sorted(debug.glob("chunk_*.json"))
    if not artifacts:
        sys.exit(f"No chunk_*.json artifacts in {debug}")

    if args.show_raw is not None:
        for path in artifacts:
            data = json.loads(path.read_text())
            if data["chunk_idx"] == args.show_raw:
                print(data["raw_response"])
                return
        sys.exit(f"No chunk with idx={args.show_raw}")

    merged: dict[str, list[int]] = {}  # path -> list of chunk indices that produced it
    print(f"Replaying {len(artifacts)} chunk artifact(s) from {debug}\n")

    total_files = 0
    total_failed_chunks = 0
    total_truncated_chunks = 0

    for path in artifacts:
        data = json.loads(path.read_text())
        idx = data["chunk_idx"]
        total = data["total_chunks"]
        raw = data["raw_response"]
        finish = data.get("finish_reason") or "none"
        input_files = data.get("input_files", [])

        files, meta = _parse_wiki_response_with_meta(raw)
        total_files += len(files)
        if meta["extraction_path"] == "failed":
            total_failed_chunks += 1
        if finish == "length":
            total_truncated_chunks += 1

        for vf in files:
            merged.setdefault(vf.path, []).append(idx)

        status = "OK" if meta["extraction_path"] != "failed" else "FAIL"
        print(
            f"chunk {idx:02d}/{total-1:02d} input_files={len(input_files):2d} "
            f"raw_chars={data['raw_chars']:6d} finish={finish:7s} "
            f"parse={meta['extraction_path']:14s} files={len(files):3d} {status}"
        )
        if meta["values_dropped_non_str"]:
            print(f"          ↳ dropped {meta['values_dropped_non_str']} non-string values")
        if meta["error"]:
            print(f"          ↳ error: {meta['error']}")
            tail = raw[-args.show_tail:].replace("\n", "\\n")
            print(f"          ↳ raw tail: ...{tail}")

    duplicates = {p: idxs for p, idxs in merged.items() if len(idxs) > 1}

    print("\n--- summary ---")
    print(f"chunks:               {len(artifacts)}")
    print(f"chunks parse-failed:  {total_failed_chunks}")
    print(f"chunks finish=length: {total_truncated_chunks} (max_tokens truncation)")
    print(f"files produced:       {total_files}")
    print(f"unique merged files:  {len(merged)}")
    print(f"paths from >1 chunk:  {len(duplicates)} (would be concatenated)")

    if duplicates:
        print("\nFragmented paths (count of chunks producing each):")
        for p, idxs in sorted(duplicates.items(), key=lambda kv: -len(kv[1]))[:20]:
            print(f"  [{len(idxs)}x] {p}  (chunks {idxs})")


if __name__ == "__main__":
    main()
