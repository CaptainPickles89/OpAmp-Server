# Stage 1: Build React application
FROM node:20-alpine AS build
WORKDIR /app

# Copy package files first for layer caching
COPY package.json package-lock.json ./
RUN npm ci --prefer-offline

# Copy source and build
COPY . .
RUN npm run build

# Verify the build output exists
RUN test -f dist/index.html || (echo "Build failed: dist/index.html not found" && exit 1)

# Stage 2: Serve with nginx
FROM nginx:1.27-alpine AS runtime
LABEL maintainer="opamp-server"

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config (overwrite default)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# nginx runs in foreground
CMD ["nginx", "-g", "daemon off;"]
