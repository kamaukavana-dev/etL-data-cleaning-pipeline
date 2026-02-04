# ======================================================
# Base image
# ======================================================
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Environment variables (optional, you can override with --env-file)
ENV PYTHONUNBUFFERED=1

# ======================================================
# Default command
# ======================================================
# This runs your pipeline when the container starts
CMD ["python", "-m", "src.main"]