FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# FastMCP using custom server.py runs via python command
CMD ["python", "server.py"]
