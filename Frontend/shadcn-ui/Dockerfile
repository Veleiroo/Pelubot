FROM node:20-alpine AS build

WORKDIR /app

# Instalar pnpm
RUN corepack enable && corepack prepare pnpm@8.10.0 --activate

# Copiar archivos de proyecto
COPY Frontend/shadcn-ui/package.json Frontend/shadcn-ui/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copiar código fuente (excluyendo node_modules)
COPY Frontend/shadcn-ui/src ./src
COPY Frontend/shadcn-ui/public ./public
COPY Frontend/shadcn-ui/index.html ./
COPY Frontend/shadcn-ui/vite.config.ts ./
COPY Frontend/shadcn-ui/tsconfig.json ./
COPY Frontend/shadcn-ui/tsconfig.app.json ./
COPY Frontend/shadcn-ui/tsconfig.node.json ./
COPY Frontend/shadcn-ui/tailwind.config.ts ./
COPY Frontend/shadcn-ui/postcss.config.js ./
COPY Frontend/shadcn-ui/components.json ./

# Base pública para API (proxy en nginx a /api), API key y flag de debug
ARG API_BASE=/api
ARG VITE_API_KEY
ARG VITE_ENABLE_DEBUG=1
ENV VITE_API_BASE_URL=${API_BASE}
ENV VITE_API_KEY=${VITE_API_KEY}
ENV VITE_ENABLE_DEBUG=${VITE_ENABLE_DEBUG}

RUN pnpm build

FROM nginx:alpine AS runtime

# Config de Nginx con proxy /api -> backend:8776 y SPA fallback
COPY Frontend/shadcn-ui/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
