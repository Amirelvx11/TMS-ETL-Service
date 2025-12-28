FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System dependencies + Iran timezone
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    tzdata \
    cron \
    unixodbc \
    unixodbc-dev \
    build-essential \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    libmariadb-dev-compat \
    mariadb-client \
 && ln -fs /usr/share/zoneinfo/Asia/Tehran /etc/localtime \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

# MS SQL ODBC driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg \
 && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && python -m pip install --no-cache-dir -r requirements.txt

COPY . .

# Permissions + log files
RUN chmod +x /app/run_if_allowed.sh \
 && touch /var/log/etl.log \
 && touch /var/log/etl_scheduler.log \
 && chmod 0666 /var/log/etl.log \
 && chmod 0666 /var/log/etl_scheduler.log

# Cron job (runs every 3 hours — gate inside the script)
RUN echo "0 */3 * * * root /app/run_if_allowed.sh >> /var/log/etl_scheduler.log 2>&1" \
    > /etc/cron.d/tms_cron \
 && chmod 0644 /etc/cron.d/tms_cron

# Startup: immediately run ETL once, then run cron forever
CMD sh -c "/app/run_if_allowed.sh && cron -f"
