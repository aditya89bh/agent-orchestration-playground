FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY agents ./agents
COPY demos ./demos
COPY memory ./memory
COPY orchestration ./orchestration
COPY run_demo.py ./run_demo.py

RUN python -m pip install --upgrade pip \
    && pip install .

EXPOSE 8000

CMD ["uvicorn", "orchestration.api:app", "--host", "0.0.0.0", "--port", "8000"]
