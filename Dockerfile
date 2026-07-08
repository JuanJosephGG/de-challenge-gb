# 1. Base Image: Use the official lightweight Python 3.13 image to match local dev
FROM python:3.13-slim

# 2. Environment Variables: Optimize Python behavior inside containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Ensure uv creates the virtual environment inside the project directory
    UV_PROJECT_ENVIRONMENT=/app/.venv

# 3. Install 'uv' using the multi-stage copy pattern directly from Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 4. Set the working directory
WORKDIR /app

# 5. Security: Create a non-root user and group
RUN addgroup --system appgroup && adduser --system --group appuser

# 6. Cache Layer: Copy only dependency files first
COPY pyproject.toml uv.lock* ./

# 7. Install dependencies
RUN uv sync --no-dev --no-install-project

# 8. Application Code Layer: Copy the actual source code
COPY src/ ./src/

# 9. Permissions: Transfer ownership of the app directory to the non-root user
RUN chown -R appuser:appgroup /app

# 10. Switch context to the secure non-root user
USER appuser

# 11. Expose the API port
EXPOSE 8000

# 12. Entrypoint: Start the application using uv to run uvicorn
CMD ["/app/.venv/bin/uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
