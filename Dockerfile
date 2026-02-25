FROM python:3.11-slim

# Install Node.js for DOCX builder
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install Node deps for pipeline
COPY pipeline/package.json ./pipeline/
RUN cd pipeline && npm install --production

# Copy source
COPY backend/ ./backend/
COPY pipeline/ ./pipeline/

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
