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


BATCH_SIZE = 5

BATCH_PROMPT_TMPL = """以下の複数論文を分析し、必ず JSON オブジェクトのみで回答してください。コードブロック不要。
キーは論文 ID、値は次の形式です。

{{
  "<paper_id>": {{
    "abstractJa": "アブストラクト全文の自然な日本語訳",
    "task": "タスク分類（例: TTS / ASR / 音源分離 / 異音検知 / 音楽生成 など、1〜2語）",
    "proposedMethod": "提案手法の固有名詞・略称（ない場合は null）",
    "datasets": ["使用データセット名1", "使用データセット名2"]
  }}
}}

datasets は最大5件。すべて日本語で記述してください。

{papers}
"""


def build_batch_prompt(papers: list[dict]) -> str:
    blocks = []
    for p in papers:
        blocks.append(f"ID: {p['id'].split('v')[0]}\nタイトル: {p['title']}\nアブストラクト: {p.get('abstract', '')}")
    return BATCH_PROMPT_TMPL.format(papers="\n\n---\n\n".join(blocks))


def fetch_ai_fields_batch(client: OpenAI, papers: list[dict]) -> dict[str, dict]:
    cfg = SETTINGS["github_models"]
    prompt = build_batch_prompt(papers)
    paper_ids = [p["id"].split("v")[0] for p in papers]
    fallback = {pid: {"abstractJa": "", "task": None, "proposedMethod": None, "datasets": []} for pid in paper_ids}

    for attempt in range(cfg["retry_max"]):
        try:
            resp = client.chat.completions.create(
                model=cfg["model"],
                messages=[
                    {"role": "system", "content": "JSONのみで返答してください。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=800 * len(papers),
                temperature=0.3,
            )
            raw = (resp.choices[0].message.content or "").strip()
            raw = raw.lstrip("```json").lstrip("```").rstrip("```").strip()
            result = json.loads(raw)
            if isinstance(result, dict):
                return result
        except Exception as e:
            print(f"  [warn] AI error (attempt {attempt + 1}): {e}")
            time.sleep(cfg["retry_interval"] * (2 ** attempt))
    return fallback


def enrich_file(path: Path, ai_client: OpenAI | None, ai_results: dict) -> bool:
    data = json.loads(path.read_text())
    changed = False

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

            # AI フィールド（バッチ処理済みの結果を適用）
            if arxiv_id in ai_results:
                result = ai_results[arxiv_id]
                for k, v in result.items():
                    if k not in paper:
                        paper[k] = v
                        paper_changed = True

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
        print("[enrich] GPT-4o によるAIフィールド補完を有効化（バッチ処理）")
    else:
        print("[enrich] GITHUB_TOKEN 未設定: AIフィールドをスキップ")

    # 全週次ファイルから AI フィールドが不足している論文を収集
    ai_results: dict[str, dict] = {}
    if ai_client:
        papers_needing_ai = []
        for path in weekly_files:
            data = json.loads(path.read_text())
            for cat in data.get("categories", []):
                for paper in cat.get("papers", []):
                    if any(f not in paper for f in AI_FIELDS) and paper.get("abstract"):
                        papers_needing_ai.append(paper)

        print(f"[enrich] AI補完が必要な論文: {len(papers_needing_ai)} 件")

        # バッチ処理
        for i in range(0, len(papers_needing_ai), BATCH_SIZE):
            batch = papers_needing_ai[i:i + BATCH_SIZE]
            ids = [p["id"].split("v")[0] for p in batch]
            print(f"[enrich] AI batch ({i // BATCH_SIZE + 1}/{(len(papers_needing_ai) + BATCH_SIZE - 1) // BATCH_SIZE}) ids={', '.join(ids)}")
            result = fetch_ai_fields_batch(ai_client, batch)
            ai_results.update(result)
            if i + BATCH_SIZE < len(papers_needing_ai):
                time.sleep(3.0)

    # 各ファイルにメタデータを書き込み
    for path in weekly_files:
        print(f"\n[enrich] --- {path.name} ---")
        enrich_file(path, ai_client, ai_results)

    print("\n[enrich] 完了。")


if __name__ == "__main__":
    main()
