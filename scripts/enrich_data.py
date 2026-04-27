#!/usr/bin/env python3
"""
enrich_data.py
既存の週次 JSON に citationCount と githubRepo を追加する
"""
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
WEEKLY_DIR = ROOT / "data" / "weekly"


def fetch_citation_count(arxiv_id: str) -> int | None:
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}?fields=citationCount"
        req = urllib.request.Request(url, headers={"User-Agent": "arxiv-weekly/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return data.get("citationCount")
    except Exception:
        return None


def fetch_github_repo(arxiv_id: str) -> str | None:
    try:
        url = f"https://huggingface.co/api/papers/{arxiv_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "arxiv-weekly/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return data.get("githubRepo") or None
    except Exception:
        return None


def enrich_weekly_file(path: Path) -> bool:
    data = json.loads(path.read_text())
    changed = False

    for cat in data.get("categories", []):
        for paper in cat.get("papers", []):
            arxiv_id = paper["id"].split("v")[0]

            if "citationCount" not in paper:
                count = fetch_citation_count(arxiv_id)
                paper["citationCount"] = count
                changed = True
                time.sleep(0.3)

            if "githubRepo" not in paper:
                repo = fetch_github_repo(arxiv_id)
                paper["githubRepo"] = repo
                changed = True
                time.sleep(0.3)

    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"[enrich] Updated -> {path.name}")
    else:
        print(f"[enrich] Already enriched -> {path.name}")

    return changed


def main():
    weekly_files = sorted(WEEKLY_DIR.glob("*.json"))
    print(f"[enrich] {len(weekly_files)} 週次ファイルを処理します")
    for path in weekly_files:
        enrich_weekly_file(path)
    print("[enrich] 完了。")


if __name__ == "__main__":
    main()
