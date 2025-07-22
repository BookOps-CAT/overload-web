FROM python:3.13-slim

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y git

RUN adduser -u 5678 --disabled-password --gecos "" appuser

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /app

RUN chown -R appuser /app
USER appuser

CMD ["uvicorn", "overload_web.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]