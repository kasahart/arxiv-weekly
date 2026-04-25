#!/usr/bin/env python3
"""
build_data.py
解析済み論文を週次 JSON に整形し、インデックスを更新する
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from openai import OpenAI

ROOT = Path(__file__).parent.parent
SETTINGS = yaml.safe_load((ROOT / "config/settings.yaml").read_text())
KEYWORDS = yaml.safe_load((ROOT / "config/keywords.yaml").read_text())

TREND_PROMPT = """以下の論文リスト（タイトルと要約）をもとに、今週の音声・音響 AI 研究の技術トレンドを
正確に 3 行で日本語にまとめてください。
各行は「①」「②」「③」で始め、具体的な論文名や手法名を挙げながら簡潔にまとめてください。
JSON 配列として返してください（文字列 3 要素）。コードブロック記号は不要です。"""


def generate_trend(client: OpenAI, papers: list[dict]) -> list[str]:
    cfg = SETTINGS["github_models"]
    summaries = "\n".join(
        f"- {p['title']}: {p['what']}" for p in papers[:20]
    )
    for attempt in range(cfg["retry_max"]):
        try:
            resp = client.chat.completions.create(
                model=cfg["model"],
                messages=[
                    {"role": "system", "content": "JSONのみで返答してください。"},
                    {"role": "user", "content": f"{TREND_PROMPT}\n\n{summaries}"},
                ],
                max_tokens=400,
                temperature=0.4,
            )
            raw = (resp.choices[0].message.content or "").strip()
            raw = raw.lstrip("```json").lstrip("```").rstrip("```").strip()
            result = json.loads(raw)
            if isinstance(result, list) and len(result) == 3:
                return result
        except Exception as e:
            print(f"  [warn] trend generation error (attempt {attempt+1}): {e}")
        time.sleep(cfg["retry_interval"] * (2 ** attempt))
    return [
        "① 今週の音声基盤モデル研究のトレンドを解析中です。",
        "② 音源分離・異音検知の最新手法が多数投稿されました。",
        "③ 詳細は各論文をご参照ください。",
    ]


def group_by_category(papers: list[dict]) -> list[dict]:
    ui_cats = KEYWORDS["ui_categories"]
    cat_map = {c["id"]: {"id": c["id"], "label": c["label"], "color": c["color"], "papers": []}
               for c in ui_cats}
    cat_map["other"] = {"id": "other", "label": "その他", "color": "#94a3b8", "papers": []}

    for p in papers:
        cat_id = p.get("category", "other")
        if cat_id not in cat_map:
            cat_id = "other"
        cat_map[cat_id]["papers"].append(p)

    return [v for v in cat_map.values() if v["papers"]]


def load_index() -> dict:
    index_path = ROOT / SETTINGS["data"]["index_file"]
    if index_path.exists():
        return json.loads(index_path.read_text())
    return {"weeks": [], "generated_at": ""}


def save_index(index: dict):
    index_path = ROOT / SETTINGS["data"]["index_file"]
    index["generated_at"] = datetime.now(timezone.utc).isoformat()
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    print(f"[build] Index updated → {index_path}")


def main():
    analyzed_path = ROOT / "data" / "analyzed_papers.json"
    if not analyzed_path.exists():
        raise FileNotFoundError(f"{analyzed_path} が見つかりません。analyze_papers.py を先に実行してください。")

    papers = json.loads(analyzed_path.read_text())
    now = datetime.now(timezone.utc)
    date_key = now.strftime("%Y-%m%d")          # 例: 2026-0425
    filename = f"{date_key}.json"
    weekly_path = ROOT / SETTINGS["data"]["weekly_dir"] / filename

    # 同一日付のファイルが既にある場合はスキップ
    if weekly_path.exists():
        print(f"[build] {weekly_path} は既に存在します。スキップします。")
        return

    # GitHub Models でトレンド生成
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        cfg = SETTINGS["github_models"]
        client = OpenAI(base_url=cfg["endpoint"], api_key=token)
        trend = generate_trend(client, papers)
    else:
        print("[build] GITHUB_TOKEN 未設定のためトレンド生成をスキップします。")
        trend = ["① トレンド情報なし", "② トレンド情報なし", "③ トレンド情報なし"]

    # カテゴリ別に整形
    categories = group_by_category(papers)

    weekly_data = {
        "date": date_key,
        "generated_at": now.isoformat(),
        "total": len(papers),
        "categories": categories,
        "trend": trend,
    }

    # 週次ファイル保存
    weekly_path.parent.mkdir(parents=True, exist_ok=True)
    weekly_path.write_text(json.dumps(weekly_data, ensure_ascii=False, indent=2))
    print(f"[build] Saved weekly → {weekly_path}")

    # latest.json を更新
    latest_path = ROOT / SETTINGS["data"]["latest_file"]
    latest_path.write_text(json.dumps(weekly_data, ensure_ascii=False, indent=2))
    print(f"[build] Updated latest → {latest_path}")

    # index.json を更新
    index = load_index()
    # 同一 date_key のエントリがあれば削除してから先頭に追加
    index["weeks"] = [w for w in index["weeks"] if w["date"] != date_key]
    index["weeks"].insert(0, {
        "date": date_key,
        "file": f"weekly/{filename}",
        "count": len(papers),
        "generated_at": now.isoformat(),
    })
    save_index(index)

    # 中間ファイルを削除
    (ROOT / "data" / "raw_papers.json").unlink(missing_ok=True)
    (ROOT / "data" / "analyzed_papers.json").unlink(missing_ok=True)
    print("[build] Done.")


if __name__ == "__main__":
    main()
