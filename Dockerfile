FROM python:3.12-slim

# Minimal, predictable runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps: cron, ODBC, build tools for mysqlclient
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
    
# Microsoft repo + ODBC Driver 17 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg \
 && curl https://packages.microsoft.com/config/debian/12/prod.list -o /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (Cached layer)
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && python -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create log file & permissions
RUN touch /var/log/etl.log && chmod 0666 /var/log/etl.log

# Configure Cron (User 'root' + Absolute path)
RUN echo "0 */12 * * * root /usr/local/bin/python /app/main.py >> /var/log/etl.log 2>&1" > /etc/cron.d/tms_cron \
 && chmod 0644 /etc/cron.d/tms_cron

# Run Cron in Foreground
CMD ["cron", "-f"]
