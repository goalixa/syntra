FROM python:3.11-slim

WORKDIR /app

# Set HOME to writable directory and create .local for CrewAI
ENV HOME=/app
ENV XDG_DATA_HOME=/app/.local
RUN mkdir -p /app/.local/share && \
    chmod -R 777 /app/.local

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
