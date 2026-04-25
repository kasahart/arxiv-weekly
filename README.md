# 音声研究週報 自動更新システム

arXiv cs.SD / eess.AS カテゴリから毎週金曜日に論文を自動収集・解析し、GitHub Pages で公開するシステムです。

## 対象分野
- 音の基盤モデル（Audio Foundation Model）
- 音源分離（Source Separation）
- 異音検知（Anomalous Sound Detection）

## セットアップ

### 1. リポジトリの設定
```bash
# GitHub Pages を有効化
# Settings → Pages → Source: Deploy from a branch → gh-pages
```

### 2. DevContainer で開発環境を起動
VS Code でリポジトリを開き「Reopen in Container」を選択

### 3. 動作確認
```bash
python scripts/test_connection.py        # GitHub Models 疎通確認
python scripts/fetch_papers.py --dry-run # arXiv 取得テスト
```

### 4. 手動実行
GitHub Actions タブ → Weekly arXiv Update → Run workflow

## キーワードの追加・削除
`config/keywords.yaml` の `include` リストを編集するだけで OK。コードの変更は不要です。

## ファイル構成
```
.devcontainer/     # DevContainer 設定
.github/workflows/ # GitHub Actions ワークフロー
config/
  keywords.yaml    # フィルタリングキーワード（編集可）
  settings.yaml    # システム設定
data/
  index.json       # 全週インデックス
  latest.json      # 最新週データ
  weekly/          # 週次 JSON（YYYY-MMDD.json）
scripts/
  fetch_papers.py  # arXiv 取得
  analyze_papers.py# GitHub Models 解析
  build_data.py    # データ生成・インデックス更新
  test_connection.py # 疎通確認
web/               # React フロントエンド
requirements.txt
```
