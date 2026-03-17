FROM python:3.11-slim
WORKDIR /app
COPY frontend-web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY frontend-web/ .
COPY tools/ tools/
ENV PORT=8080
# Run the FastAPI web/API gateway server
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
