FROM python:3.13-slim

WORKDIR /app/chat

COPY chat/requirements.txt /app/requirements.txt
COPY core /app/core
COPY response /app/response
COPY chat /app/chat

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8020"]