#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x venv/bin/python ]; then
    python3 -m venv venv
fi
if ! venv/bin/python -c 'import requests' >/dev/null 2>&1; then
    venv/bin/python -m pip install requests==2.32.5
fi
if [ "$#" -gt 0 ]; then
    exec venv/bin/python gui/dashboard.py "$@"
fi
case "$(uname -s)-$(uname -m)" in
    Darwin-arm64) binary=servers/procon-server-darwin-arm64 ;;
    Darwin-x86_64) binary=servers/procon-server-darwin-amd64 ;;
    Linux-x86_64) binary=servers/procon-server-linux-amd64 ;;
    *) echo '対応するサーバーを gui/dashboard.py --server で指定してください。'; exit 1 ;;
esac
if [ ! -f "$binary" ]; then
    echo "サーバーがありません: $binary。--server と --maps で手元のファイルを指定してください。"
    exit 1
fi
chmod u+x "$binary"
echo 'ブラウザーで 127.0.0.1:8765 を開いてください。終了は Ctrl+C。'
shopt -s nullglob
map_files=(maps/*.json)
if [ "${#map_files[@]}" -eq 0 ]; then
    echo 'maps/ にJSONがありません。--server と --maps でファイルを指定してください。'
    exit 1
fi
exec venv/bin/python gui/dashboard.py --server "$binary" --maps "${map_files[@]}" --runs gui-runs
