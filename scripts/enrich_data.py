#!/usr/bin/env python3
"""
enrich_data.py
既存の週次 JSON に不足フィールドをすべて追加する
"""
import json
import os
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml
from openai import OpenAI

ROOT = Path(__file__).parent.parent
WEEKLY_DIR = ROOT / "data" / "weekly"
SETTINGS = yaml.safe_load((ROOT / "config/settings.yaml").read_text())

NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

AI_FIELDS = ("abstractJa", "task", "proposedMethod", "datasets")


def fetch_arxiv_meta(arxiv_id: str) -> dict:
    clean_id = arxiv_id.split("v")[0]
    url = f"https://export.arxiv.org/api/query?id_list={clean_id}&max_results=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "arxiv-weekly/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            tree = ET.fromstring(r.read())
        entry = tree.find("atom:entry", NS)
        if entry is None:
            return {}
        return {
            "abstract": (entry.findtext("atom:summary", "", NS) or "").strip().replace("\n", " "),
            "comment": (entry.findtext("arxiv:comment", "", NS) or "").strip().replace("\n", " ") or None,
            "journalRef": (entry.findtext("arxiv:journal_ref", "", NS) or "").strip() or None,
            "categories": [t.get("term", "") for t in entry.findall("atom:category", NS)],
        }
    except Exception as e:
        print(f"  [warn] arXiv error {arxiv_id}: {e}")
        return {}


def fetch_hf_meta(arxiv_id: str) -> dict:
    clean_id = arxiv_id.split("v")[0]
    try:
        url = f"https://huggingface.co/api/papers/{clean_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "arxiv-weekly/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return {
            "githubRepo": data.get("githubRepo") or None,
            "upvotes": data.get("upvotes"),
            "projectPage": data.get("projectPage") or None,
        }
    except Exception:
        return {}


def fetch_citation_count(arxiv_id: str) -> int | None:
    clean_id = arxiv_id.split("v")[0]
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{clean_id}?fields=citationCount"
        req = urllib.request.Request(url, headers={"User-Agent": "arxiv-weekly/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return data.get("citationCount")
    except Exception:
        return None


AI_PROMPT = """以下の論文を分析し、必ず JSON 形式のみで回答してください。コードブロック不要。

{{
  "abstractJa": "アブストラクト全文の自然な日本語訳",
  "task": "タスク分類（例: TTS / ASR / 音源分離 / 異音検知 / 音楽生成 など、1〜2語）",
  "proposedMethod": "提案手法の固有名詞・略称（ない場合は null）",
  "datasets": ["使用データセット名1", "使用データセット名2"]
}}

datasets は最大5件。すべて日本語で記述してください。

タイトル: {title}
アブストラクト: {abstract}
"""


def fetch_ai_fields(client: OpenAI, paper: dict) -> dict:
    cfg = SETTINGS["github_models"]
    prompt = AI_PROMPT.format(
        title=paper.get("title", ""),
        abstract=paper.get("abstract", ""),
    )
    for attempt in range(cfg["retry_max"]):
        try:
            resp = client.chat.completions.create(
                model=cfg["model"],
                messages=[
                    {"role": "system", "content": "JSONのみで返答してください。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800,
                temperature=0.3,
            )
            raw = (resp.choices[0].message.content or "").strip()
            raw = raw.lstrip("```json").lstrip("```").rstrip("```").strip()
            result = json.loads(raw)
            return {
                "abstractJa": result.get("abstractJa", ""),
                "task": result.get("task"),
                "proposedMethod": result.get("proposedMethod"),
                "datasets": result.get("datasets", []),
            }
        except Exception as e:
            print(f"  [warn] AI error (attempt {attempt + 1}): {e}")
            time.sleep(cfg["retry_interval"] * (2 ** attempt))
    return {"abstractJa": "", "task": None, "proposedMethod": None, "datasets": []}


def enrich_file(path: Path, ai_client: OpenAI | None) -> bool:
    data = json.loads(path.read_text())
    changed = False
    last_ai_call = 0.0
    AI_INTERVAL = 3.0

    for cat in data.get("categories", []):
        for paper in cat.get("papers", []):
            arxiv_id = paper["id"].split("v")[0]
            paper_changed = False

            # arXiv メタデータ
            if "abstract" not in paper or "categories" not in paper:
                meta = fetch_arxiv_meta(arxiv_id)
                for k, v in meta.items():
                    if k not in paper:
                        paper[k] = v
                        paper_changed = True
                time.sleep(0.5)

            # HuggingFace メタデータ
            if "upvotes" not in paper or "projectPage" not in paper:
                meta = fetch_hf_meta(arxiv_id)
                for k, v in meta.items():
                    if k not in paper:
                        paper[k] = v
                        paper_changed = True
                time.sleep(0.3)

            # 被引用数
            if "citationCount" not in paper:
                paper["citationCount"] = fetch_citation_count(arxiv_id)
                paper_changed = True
                time.sleep(0.3)

            # AI フィールド
            if ai_client and any(f not in paper for f in AI_FIELDS):
                if paper.get("abstract"):
                    elapsed = time.monotonic() - last_ai_call
                    if elapsed < AI_INTERVAL:
                        time.sleep(AI_INTERVAL - elapsed)
                    result = fetch_ai_fields(ai_client, paper)
                    for k, v in result.items():
                        if k not in paper:
                            paper[k] = v
                            paper_changed = True
                    last_ai_call = time.monotonic()

            if paper_changed:
                changed = True
                print(f"  [enrich] {arxiv_id} updated")

    if changed:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"[enrich] Saved -> {path.name}")
    else:
        print(f"[enrich] No changes -> {path.name}")

    return changed


def main():
    weekly_files = sorted(WEEKLY_DIR.glob("*.json"))
    print(f"[enrich] {len(weekly_files)} 週次ファイルを処理します")

    token = os.environ.get("GITHUB_TOKEN")
    ai_client = None
    if token:
        cfg = SETTINGS["github_models"]
        ai_client = OpenAI(base_url=cfg["endpoint"], api_key=token)
        print("[enrich] GPT-4o によるAIフィールド補完を有効化")
    else:
        print("[enrich] GITHUB_TOKEN 未設定: AIフィールドをスキップ")

    for path in weekly_files:
        print(f"\n[enrich] --- {path.name} ---")
        enrich_file(path, ai_client)

    print("\n[enrich] 完了。")


if __name__ == "__main__":
    main()
