FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY web_flask/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY web_flask/ .

# Set Python path to include the current directory
ENV PYTHONPATH=/app

# Run the application
CMD ["python", "run.py"]
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]