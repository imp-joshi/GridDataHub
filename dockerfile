# Use Python 3.11 as base image
FROM python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies (including those needed for BeautifulSoup)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port
EXPOSE 10000

# Command to run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}
