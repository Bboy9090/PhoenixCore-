# PhoenixCore backend - BootForge web server
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY web_server.py .
COPY src/ src/
COPY dist/ dist/ 2>/dev/null || true

ENV FLASK_APP=web_server.py
EXPOSE 5000

CMD ["python", "web_server.py"]
