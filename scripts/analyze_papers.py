#!/usr/bin/env python3
"""
analyze_papers.py
GitHub Models (Claude) を使って各論文を 6 観点で日本語解析する
"""

import json
import os
import time
from pathlib import Path

import yaml
from openai import APIError, OpenAI

from model_utils import build_chat_kwargs

ROOT = Path(__file__).parent.parent
SETTINGS = yaml.safe_load((ROOT / "config/settings.yaml").read_text())
KEYWORDS = yaml.safe_load((ROOT / "config/keywords.yaml").read_text())

SYSTEM_PROMPT = """あなたは音声・音響 AI 分野の論文アナリストです。
与えられた論文情報（タイトル・アブストラクト）を分析し、必ず以下の JSON 形式のみで回答してください。
前置きや説明文、コードブロック記号（```json など）は一切含めないでください。

{
  "titleJa": "論文タイトルの日本語訳（自然な日本語で）",
  "org": "著者の主要所属機関（大学名・企業名を簡潔に、例: MIT / Google）",
  "what": "① どんなもの？（1〜2文で研究の全体像）",
  "novel": "② 先行研究と比べてすごい点（1〜2文で新規性・貢献）",
  "method": "③ 技術・手法のキモ（1〜2文でアーキテクチャや学習の核心）",
  "validation": "④ 有効性の検証（データセット・指標・比較実験を1〜2文で）",
  "discussion": "⑤ 議論・限界（残課題・制約を1〜2文で）",
  "nextReads": [
    {"label": "関連論文名 (年)", "id": "arXiv ID（例: 2310.13289）または null"}
  ]
}

nextReads は 3〜4 件。arXiv ID が不明な場合は null としてください。
すべての説明は日本語で記述してください。"""


def get_client() -> OpenAI:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN が設定されていません")
    cfg = SETTINGS["github_models"]
    return OpenAI(base_url=cfg["endpoint"], api_key=token)


def sanitize_json_text(raw: str) -> str:
    return raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()


def wait_for_next_request(last_request_at: float | None, min_interval: float):
    if last_request_at is None:
        return
    elapsed = time.monotonic() - last_request_at
    remaining = min_interval - elapsed
    if remaining > 0:
        print(f"[analyze] waiting {remaining:.1f}s to respect model rate limit ...")
        time.sleep(remaining)


def build_batch_prompt(papers: list[dict]) -> str:
    paper_blocks = []
    for paper in papers:
        paper_blocks.append(
            f"""ID: {paper["id"]}
タイトル: {paper["title"]}
著者: {", ".join(paper.get("authors", [])[:3])}
カテゴリ: {", ".join(paper.get("categories", []))}
投稿日: {paper.get("date", "")}

アブストラクト:
{paper["abstract"]}"""
        )

    joined = "\n\n---\n\n".join(paper_blocks)
    return f"""以下の複数論文を分析してください。
各論文の ID ごとに結果を返し、必ず JSON オブジェクトのみで回答してください。
キーは論文 ID、値は次の形式です。

{{
  "<paper_id>": {{
    "titleJa": "論文タイトルの日本語訳（自然な日本語で）",
    "org": "著者の主要所属機関（大学名・企業名を簡潔に、例: MIT / Google）",
    "what": "① どんなもの？（1〜2文で研究の全体像）",
    "novel": "② 先行研究と比べてすごい点（1〜2文で新規性・貢献）",
    "method": "③ 技術・手法のキモ（1〜2文でアーキテクチャや学習の核心）",
    "validation": "④ 有効性の検証（データセット・指標・比較実験を1〜2文で）",
    "discussion": "⑤ 議論・限界（残課題・制約を1〜2文で）",
    "nextReads": [
      {{"label": "関連論文名 (年)", "id": "arXiv ID または null"}}
    ]
  }}
}}

nextReads は各論文 3〜4 件、arXiv ID が不明な場合は null としてください。
すべての説明は日本語で記述してください。

{joined}"""


def fallback_result(paper: dict) -> dict:
    return {
        "titleJa": paper["title"],
        "org": paper.get("org", ""),
        "what": "解析に失敗しました。",
        "novel": "",
        "method": "",
        "validation": "",
        "discussion": "",
        "nextReads": [],
    }


def analyze_batch(
    client: OpenAI, papers: list[dict], last_request_at: float | None
) -> tuple[dict[str, dict], float | None]:
    cfg = SETTINGS["github_models"]
    prompt = build_batch_prompt(papers)
    paper_ids = {paper["id"] for paper in papers}

    for attempt in range(cfg["retry_max"]):
        request_started_at = None
        try:
            wait_for_next_request(last_request_at, cfg["min_request_interval"])
            request_started_at = time.monotonic()
            resp = client.chat.completions.create(
                model=cfg["model"],
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                **build_chat_kwargs(
                    cfg["model"], cfg["batch_max_tokens"], temperature=0.3
                ),
            )
            last_request_at = time.monotonic()
            raw = sanitize_json_text(resp.choices[0].message.content or "")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise json.JSONDecodeError(
                    "Batch response is not a JSON object", raw, 0
                )
            missing_ids = sorted(paper_ids - set(result.keys()))
            if missing_ids:
                raise json.JSONDecodeError(
                    f"Missing paper ids: {', '.join(missing_ids)}", raw, 0
                )
            return result, last_request_at
        except json.JSONDecodeError as e:
            if request_started_at is not None:
                last_request_at = request_started_at
            print(f"  [warn] JSON parse error (attempt {attempt + 1}): {e}")
        except APIError as e:
            if request_started_at is not None:
                last_request_at = request_started_at
            print(f"  [warn] API error (attempt {attempt + 1}): {e}")
        time.sleep(cfg["retry_interval"] * (2**attempt))

    return {paper["id"]: fallback_result(paper) for paper in papers}, last_request_at


def chunk_papers(papers: list[dict], batch_size: int) -> list[list[dict]]:
    return [
        papers[index : index + batch_size]
        for index in range(0, len(papers), batch_size)
    ]


def build_next_reads(items: list[dict]) -> list[dict]:
    result = []
    for item in items:
        arxiv_id = item.get("id")
        url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None
        result.append({"label": item.get("label", ""), "url": url})
    return result


def main():
    raw_path = ROOT / "data" / "raw_papers.json"
    if not raw_path.exists():
        raise FileNotFoundError(
            f"{raw_path} が見つかりません。fetch_papers.py を先に実行してください。"
        )

    papers = json.loads(raw_path.read_text())
    print(f"[analyze] {len(papers)} 件の論文を解析します ...")

    client = get_client()
    cfg = SETTINGS["github_models"]
    analyzed = []
    batches = chunk_papers(papers, cfg["batch_size"])
    last_request_at = None

    for batch_index, batch in enumerate(batches, 1):
        batch_ids = ", ".join(paper["id"] for paper in batch)
        print(
            f"[analyze] batch ({batch_index}/{len(batches)}) size={len(batch)} ids={batch_ids}"
        )
        batch_results, last_request_at = analyze_batch(client, batch, last_request_at)

        for paper in batch:
            result = batch_results.get(paper["id"], fallback_result(paper))
            analyzed.append(
                {
                    "id": paper["id"],
                    "date": paper["date"],
                    "title": paper["title"],
                    "titleJa": result.get("titleJa", paper["title"]),
                    "org": result.get("org") or paper.get("org", ""),
                    "url": paper["url"],
                    "category": paper.get("category", "other"),
                    "what": result.get("what", ""),
                    "novel": result.get("novel", ""),
                    "method": result.get("method", ""),
                    "validation": result.get("validation", ""),
                    "discussion": result.get("discussion", ""),
                    "nextReads": build_next_reads(result.get("nextReads", [])),
                }
            )

    out_path = ROOT / "data" / "analyzed_papers.json"
    out_path.write_text(json.dumps(analyzed, ensure_ascii=False, indent=2))
    print(f"[analyze] Saved → {out_path}")


if __name__ == "__main__":
    main()
