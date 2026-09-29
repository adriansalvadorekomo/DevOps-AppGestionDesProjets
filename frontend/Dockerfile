# ---- Build stage: Node Alpine (Angular 22 needs Node 18+; npm 11 needs Node 20+) ----
FROM node:22-alpine AS build
WORKDIR /app

# Leverage layer caching: install deps first
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- Runtime stage: minimal nginx Alpine serving static files ----
FROM nginx:alpine
# SPA routing fallback (Angular Router needs index.html for unknown paths)
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Angular application builder output (verified: dist/frontend/browser)
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
