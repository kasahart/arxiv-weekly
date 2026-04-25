#!/bin/bash
set -e

echo "🔧 DevContainer セットアップ開始..."

# Python 仮想環境
if [ ! -d "/venv" ]; then
  python -m venv /venv
fi
/venv/bin/pip install --quiet -r requirements.txt
echo "✅ Python 依存パッケージをインストールしました"

# Node.js 依存パッケージ
cd web && npm install --silent
echo "✅ Node.js 依存パッケージをインストールしました"
cd ..

# GitHub CLI 認証状態確認
echo "🔍 GitHub CLI 認証状態:"
gh auth status 2>&1 || echo "⚠️  gh auth login を実行して認証してください"

echo ""
echo "✅ DevContainer の準備が完了しました！"
echo ""
echo "利用可能なコマンド:"
echo "  python scripts/test_connection.py   # GitHub Models 疎通確認"
echo "  python scripts/fetch_papers.py --dry-run  # arXiv 取得テスト"
echo "  cd web && npm run dev               # フロントエンド開発サーバー"
