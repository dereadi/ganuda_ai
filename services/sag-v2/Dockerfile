# SAG v2 — Multi-stage build
# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY app.py llm_router.py prompts.py ./
COPY mcp_servers/ ./mcp_servers/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Default port
ENV SAG_V2_PORT=4100
EXPOSE 4100

CMD ["python", "app.py"]