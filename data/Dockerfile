FROM python:3.13-slim

WORKDIR /app/data

COPY ../requirements.txt /app/requirements.txt
COPY ../core /app/core
COPY ../modelAi /app/modelAi
COPY . /app

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]