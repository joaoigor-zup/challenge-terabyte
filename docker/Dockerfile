FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
COPY .env .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install python-dotenv for loading .env if not already in requirements.txt
RUN pip install --no-cache-dir python-dotenv pydantic-settings==2.8.1

# Copy the application code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Command to run the application with environment variables loaded
CMD ["sh", "-c", "python -m dotenv run -- uvicorn api.main:app --host 0.0.0.0 --port 8000"]
