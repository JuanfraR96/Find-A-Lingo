FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Railway provides the PORT environment variable
# Start uvicorn on that port
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
