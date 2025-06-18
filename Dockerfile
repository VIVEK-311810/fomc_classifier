# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy frontend requirements and install
COPY frontend/requirements.txt ./frontend/
RUN pip install --no-cache-dir -r ./frontend/requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create directory for data
RUN mkdir -p ./data

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Set environment variables
ENV EXCEL_PATH=/app/data/Sentiment&Attributes_Classification.xlsx
ENV PYTHONPATH=/app

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the startup script
CMD ["./start.sh"]

