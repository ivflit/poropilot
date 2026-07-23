# Multi-stage: build the Vue app, then serve it with Nginx (static assets +
# reverse proxy to the backend + TLS termination). Build context is the repo root.

# 1) Build the frontend. VITE_API_BASE="" makes the app call same-origin /api,
#    which Nginx proxies to the backend below.
FROM node:20-slim AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_BASE=""
RUN npm run build

# 2) Serve with Nginx.
FROM nginx:1.27-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80 443
