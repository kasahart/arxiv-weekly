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
from openai import OpenAI

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


def analyze_paper(client: OpenAI, paper: dict) -> dict:
    cfg = SETTINGS["github_models"]
    prompt = f"""以下の論文を分析してください。

タイトル: {paper['title']}
著者: {', '.join(paper.get('authors', [])[:3])}
カテゴリ: {', '.join(paper.get('categories', []))}
投稿日: {paper.get('date', '')}

アブストラクト:
{paper['abstract']}"""

    for attempt in range(cfg["retry_max"]):
        try:
            resp = client.chat.completions.create(
                model=cfg["model"],
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=cfg["max_tokens"],
                temperature=0.3,
            )
            raw = resp.choices[0].message.content or ""
            raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"  [warn] JSON parse error (attempt {attempt+1}): {e}")
        except Exception as e:
            print(f"  [warn] API error (attempt {attempt+1}): {e}")
        time.sleep(cfg["retry_interval"] * (2 ** attempt))

    # フォールバック
    return {
        "titleJa": paper["title"],
        "org": paper.get("org", ""),
        "what": "解析に失敗しました。",
        "novel": "", "method": "", "validation": "", "discussion": "",
        "nextReads": [],
    }


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
        raise FileNotFoundError(f"{raw_path} が見つかりません。fetch_papers.py を先に実行してください。")

    papers = json.loads(raw_path.read_text())
    print(f"[analyze] {len(papers)} 件の論文を解析します ...")

    client = get_client()
    cfg = SETTINGS["github_models"]
    analyzed = []

    for i, paper in enumerate(papers, 1):
        print(f"[analyze] ({i}/{len(papers)}) {paper['id']} ...")
        result = analyze_paper(client, paper)

        analyzed.append({
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
        })
        # レート制限対策
        time.sleep(1.5)

    out_path = ROOT / "data" / "analyzed_papers.json"
    out_path.write_text(json.dumps(analyzed, ensure_ascii=False, indent=2))
    print(f"[analyze] Saved → {out_path}")


if __name__ == "__main__":
    main()
