# Stage 1: React 빌드
FROM node:20-alpine AS builder
WORKDIR /app

COPY apps/dashboard/package*.json ./
RUN npm ci

COPY apps/dashboard/ .

ARG VITE_API_URL=http://localhost:8000
ARG VITE_MEDIAMTX_URL=http://localhost:8889
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_MEDIAMTX_URL=$VITE_MEDIAMTX_URL

RUN npm run build

# Stage 2: Nginx 서빙 (Node.js 제거)
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY infra/proxy/nginx-spa.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
