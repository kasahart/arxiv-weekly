#!/usr/bin/env python3
"""
backfill.py
from_date から to_date までの全金曜日を基準に週次データをまとめて生成する
"""
import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_papers
import build_data as build_data_module
import fetch_papers


def fridays_between(from_date: datetime, to_date: datetime) -> list[datetime]:
    """from_date 以降 to_date 以前の全金曜日を返す"""
    dates = []
    # from_date の次の金曜日を探す（from_date が金曜なら from_date 自身）
    days_ahead = (4 - from_date.weekday()) % 7  # 4 = Friday
    first_friday = from_date + timedelta(days=days_ahead)
    d = first_friday
    while d <= to_date:
        dates.append(d)
        d += timedelta(days=7)
    return dates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-date", required=True, help="開始日 YYYY-MM-DD")
    parser.add_argument("--to-date", default="", help="終了日 YYYY-MM-DD（省略時は今日）")
    args = parser.parse_args()

    from_date = datetime.fromisoformat(args.from_date).replace(tzinfo=timezone.utc)
    to_date = (
        datetime.fromisoformat(args.to_date).replace(tzinfo=timezone.utc)
        if args.to_date
        else datetime.now(timezone.utc)
    )

    dates = fridays_between(from_date, to_date)
    print(f"[backfill] {len(dates)} 週分（金曜日）を処理:")
    for d in dates:
        print(f"  {d.strftime('%Y-%m-%d (%a)')}")

    for i, date in enumerate(dates, 1):
        date_str = date.strftime("%Y-%m-%d")
        date_key = date.strftime("%Y-%m%d")
        weekly_path = ROOT / "data" / "weekly" / f"{date_key}.json"

        print(f"\n[backfill] === ({i}/{len(dates)}) {date_str} ===")

        if weekly_path.exists():
            print(f"[backfill] {weekly_path.name} は既に存在します。スキップ。")
            continue

        # 論文取得
        fetch_papers.main(date_str=date_str)

        raw_path = ROOT / "data" / "raw_papers.json"
        if not raw_path.exists():
            print("[backfill] 論文なし。スキップ。")
            continue

        papers = json.loads(raw_path.read_text())
        if not papers:
            print("[backfill] マッチする論文なし。スキップ。")
            raw_path.unlink(missing_ok=True)
            continue

        # 解析
        analyze_papers.main()

        # ビルド
        build_data_module.main(date_str=date_str)

        # レート制限対策: 週間に待機
        if i < len(dates):
            print("[backfill] 次の週まで90秒待機...")
            time.sleep(90)

    print("\n[backfill] 完了。")


if __name__ == "__main__":
    main()
