FROM python:3.13-slim

WORKDIR /app/dashboard

RUN apt-get update && apt-get install -y poppler-utils

COPY dashboard/requirements.txt /app/requirements.txt
COPY core /app/core
COPY dashboard /app/dashboard

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8030"]