FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# xgboost ko libgomp chahiye, baaki packages ko compiler
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pehle sirf requirements (taake dobara build tez ho)
COPY Backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY Backend backend
COPY Frontend frontend

WORKDIR /app/backend
EXPOSE 5000