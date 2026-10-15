# Stage 1: build the static files with Node.
FROM node:22-alpine AS build

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY vite.config.js index.html ./
COPY src ./src
RUN npm run build

# Stage 2: serve them with nginx. Node is not in the final image.
FROM nginx:1.27-alpine

# The entrypoint runs envsubst over anything in templates/ and writes the
# result into conf.d/. Only variables that exist in the environment are
# replaced, so nginx variables like $uri survive untouched.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /build/dist /usr/share/nginx/html

ENV BACKEND_HOST=backend:8000

# Run as the unprivileged user the image already ships with. nginx needs to
# own the paths it writes at startup, the pid moves out of /var/run, and the
# port is above 1024 so no root is needed to bind it.
RUN sed -i -E 's!^pid .*!pid /tmp/nginx.pid;!' /etc/nginx/nginx.conf \
    && sed -i '/^user /d' /etc/nginx/nginx.conf \
    && chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /etc/nginx/conf.d

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
