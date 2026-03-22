FROM python:3.12-slim

# Install ffmpeg for audio/video processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create output directory
RUN mkdir -p /app/output

ENV PYTHONUNBUFFERED=1
ENV CONTENT_OUTPUT_DIR=/app/output

EXPOSE 8080

ENTRYPOINT ["python", "main.py"]
CMD ["schedule"]
