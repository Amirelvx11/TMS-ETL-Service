FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    cron \
    unixodbc \
    unixodbc-dev \
    build-essential \
    default-libmysqlclient-dev \
 && rm -rf /var/lib/apt/lists/*
    
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg \
 && curl https://packages.microsoft.com/config/debian/12/prod.list -o /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && python -m pip install --no-cache-dir -r requirements.txt

COPY . .

# Permissions
RUN chmod +x /app/run_if_allowed.sh \
 && touch /var/log/etl.log \
 && touch /var/log/etl_scheduler.log \
 && chmod 0666 /var/log/etl.log \
 && chmod 0666 /var/log/etl_scheduler.log

# Cron job every 3 hours → but guarded by time window
RUN echo "0 */3 * * * root /app/run_if_allowed.sh" > /etc/cron.d/tms_cron \
 && chmod 0644 /etc/cron.d/tms_cron

CMD ["cron", "-f"]

