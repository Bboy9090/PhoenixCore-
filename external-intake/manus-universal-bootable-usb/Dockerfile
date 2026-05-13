# Bobby's PhoenixDrive Backend - Production Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Clone PhoenixCore if not already present
RUN if [ ! -d "PhoenixCore-" ]; then \
    git clone https://github.com/Bboy9090/PhoenixCore-.git; \
    fi

# Create necessary directories
RUN mkdir -p /tmp/phoenix-builds /var/log/phoenix-drive

# Set environment variables
ENV FLASK_APP=server.api:app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/v1/health')"

# Run application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "server.api:app"]
