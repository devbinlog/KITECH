# n8n + 커스텀 시나리오 노드 이미지
FROM n8nio/n8n:latest

USER root

# ── 1단계: TypeScript 빌드 ────────────────────────────────────
WORKDIR /tmp/custom-build

COPY custom-nodes/n8n-nodes-scenario/package.json ./
COPY custom-nodes/n8n-nodes-scenario/tsconfig.json ./
COPY custom-nodes/n8n-nodes-scenario/index.ts ./
COPY custom-nodes/n8n-nodes-scenario/nodes ./nodes/

# NODE_ENV=production 환경에서도 devDependencies(typescript) 설치
RUN npm install --include=dev --ignore-scripts && npm run build

# ── 2단계: 빌드 결과물을 볼륨 밖 고정 경로에 보관 ─────────────
# /custom-nodes-src 는 docker-compose 볼륨(/home/node/.n8n) 밖이므로
# 볼륨이 마운트되어도 사라지지 않는다.
RUN mkdir -p /custom-nodes-src && \
    cp -r /tmp/custom-build /custom-nodes-src/n8n-nodes-scenario && \
    chown -R node:node /custom-nodes-src

# ── 3단계: 컨테이너 시작 시 실행할 entrypoint 스크립트 등록 ───
COPY docker-entrypoint.sh /usr/local/bin/custom-entrypoint.sh
RUN chmod +x /usr/local/bin/custom-entrypoint.sh

USER node

WORKDIR /home/node

# 볼륨 마운트 이후 시점에 ~/.n8n/nodes/ 에 패키지를 설치하고 n8n 실행
ENTRYPOINT ["/usr/local/bin/custom-entrypoint.sh"]

EXPOSE 5678
