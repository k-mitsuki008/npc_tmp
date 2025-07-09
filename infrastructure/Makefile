.PHONY: help install lint format check clean isort

# ヘルプを表示
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "  install   : 開発用ツール (flake8, black, isort) をインストール"
	@echo "  lint      : flake8 によるコードチェック"
	@echo "  format    : black による自動整形"
	@echo "  isort     : isort によるインポート順序の整形"
	@echo "  check     : format & lint & isort 全てを実行"
	@echo "  clean     : __pycache__ や .pyc を削除"

# 仮想環境にツールをインストール
install:
	pip install flake8 black isort

# コード整形
format:
	black .

# インポート順序の整形
isort:
	isort .

# Lintチェック
lint:
	flake8 .

# 全て実行
check: format isort lint

# 一時ファイル削除
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -name "*.pyc" -delete

# 実行方法
#  make install
#  make format
#  make lint
#  make isort
#  make check
