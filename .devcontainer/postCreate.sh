#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🔧 DevContainer セットアップ開始..."

cd "$REPO_ROOT"

# Python 仮想環境
sudo chown -R vscode:vscode /venv
if [ ! -x "/venv/bin/python" ]; then
  python3 -m venv /venv
fi
/venv/bin/python -m pip install --quiet -r requirements.txt
echo "✅ Python 依存パッケージをインストールしました"

# Node.js 依存パッケージ
sudo chown -R vscode:vscode web
cd web && npm install --silent
echo "✅ Node.js 依存パッケージをインストールしました"
cd ..

# Claude CLI
if ! command -v claude &>/dev/null; then
  curl -fsSL https://claude.ai/install.sh | bash || echo "⚠️  Claude CLI のインストールをスキップしました（後で手動でインストールできます）"
fi
if command -v claude &>/dev/null; then
  echo "✅ Claude CLI をインストールしました"
fi

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
