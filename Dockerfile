FROM python:3.13-slim

WORKDIR /app

# Run system package updates and install necessary dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY . .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

EXPOSE 8000

# Setup for the web server; this isn't ideal since assets
# don't load correctly in this setup.
CMD ["uvicorn", "overload_web.main:app", "--host", "0.0.0.0", "--port", "8000"]
