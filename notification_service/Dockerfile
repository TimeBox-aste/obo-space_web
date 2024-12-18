FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY notification_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY notification_service/ .

# Run the application
CMD ["python", "run.py"] 