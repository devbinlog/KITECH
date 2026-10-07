#!/bin/sh
# docker-entrypoint.sh
# n8n 시작 전, 커스텀 노드를 ~/.n8n/nodes/ 에 설치한다.
# 볼륨 마운트 이후에 실행되므로 볼륨 덮어쓰기 문제가 없다.

set -e

echo "[custom-entrypoint] Installing n8n-nodes-scenario..."

mkdir -p /home/node/.n8n/nodes
cd /home/node/.n8n/nodes

# package.json 이 없으면 초기화
if [ ! -f "package.json" ]; then
    npm init -y > /dev/null 2>&1
fi

# 이미지 안에 빌드된 소스(/custom-nodes-src)로부터 설치
npm install /custom-nodes-src/n8n-nodes-scenario --no-audit --no-fund --loglevel=error

echo "[custom-entrypoint] Custom nodes installed. Starting n8n..."

# n8n 원래 동작 유지 (인자 전달)
if [ "$#" -gt 0 ]; then
    exec n8n "$@"
else
    exec n8n
fi
