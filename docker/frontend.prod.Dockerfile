FROM node:20-alpine

WORKDIR /workspace

# 先安装依赖，提升 Docker 层缓存命中率
COPY apps/frontend_web/package.json apps/frontend_web/package-lock.json ./apps/frontend_web/
RUN cd apps/frontend_web && npm ci

# 拷贝前端代码与其依赖的 workspace 库
COPY apps/frontend_web ./apps/frontend_web
COPY libs/frontend_api_client ./libs/frontend_api_client
COPY libs/ui_design_system ./libs/ui_design_system
COPY libs/ui_app_shell ./libs/ui_app_shell

# Vite 环境变量在构建阶段注入
ARG VITE_BACKEND_ORIGIN=http://localhost:8000
ENV VITE_BACKEND_ORIGIN=${VITE_BACKEND_ORIGIN}

RUN cd apps/frontend_web && npm run build

WORKDIR /workspace/apps/frontend_web

ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --retries=5 --start-period=20s \
  CMD wget -q -O - http://127.0.0.1:3000/ >/dev/null || exit 1

CMD ["npm", "run", "start", "--", "--host", "0.0.0.0", "--port", "3000"]
