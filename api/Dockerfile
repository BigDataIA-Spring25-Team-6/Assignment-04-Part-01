FROM python:3.10-slim

WORKDIR /app

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir docling==2.16.0 python-multipart --extra-index-url https://download.pytorch.org/whl/cpu

COPY api /app/api
COPY backend /app/backend
COPY storage /app/storage

 
EXPOSE 8000

CMD ["uvicorn", "api.fastapi_backend:app", "--host", "0.0.0.0", "--port", "8000"]