# =============================================================================
# Multi-stage Dockerfile for ChatBI Monolithic Deployment
# Stage 1: Frontend Build | Stage 2: Backend Setup | Stage 3: Runtime
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build Frontend (Node.js)
# -----------------------------------------------------------------------------
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY web/package.json ./web/

# Install pnpm and dependencies
RUN npm install -g pnpm@8 && \
    pnpm install --frozen-lockfile

# Copy frontend source
COPY web ./web
COPY tsconfig.json tsconfig.build.json ./

# Build frontend
WORKDIR /app/web
RUN pnpm run build

# -----------------------------------------------------------------------------
# Stage 2: Prepare Backend (Python)
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy Python dependency files
COPY pyproject.toml ./
COPY chatbi ./chatbi

# Install Python dependencies
RUN uv sync --no-dev

# -----------------------------------------------------------------------------
# Stage 3: Runtime (Nginx + Python)
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment from builder
COPY --from=backend-builder /app/.venv /app/.venv
COPY --from=backend-builder /app/chatbi /app/chatbi
COPY pyproject.toml alembic.ini ./

# Copy frontend dist from builder
COPY --from=frontend-builder /app/web/dist /app/static

# Copy configuration files
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create necessary directories
RUN mkdir -p /app/runs /var/log/supervisor /var/log/nginx

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000 \
    STATIC_DIR=/app/static

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost/api/health || exit 1

# Expose port
EXPOSE 80

# Start supervisord (manages both Nginx and Uvicorn)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
