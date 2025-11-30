FROM python:3.12-slim

# Install system dependencies for pyodbc, cron, and the MS ODBC driver
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-setuptools \
    python3-dev \
    curl \
    gnupg \
    unixodbc \
    unixodbc-dev \
    cron \
    libpng-dev \
    libpq-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*
    
# Install Microsoft ODBC Driver 18 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc && \
    curl https://packages.microsoft.com/config/debian/12/prod.list \
        -o /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files into the container
COPY . .

# Setup cron job to run every 12 hours
RUN echo "0 */12 * * * python /app/main.py >> /var/log/etl.log 2>&1" > /etc/cron.d/tms_cron && \
    chmod 0644 /etc/cron.d/tms_cron && \
    crontab /etc/cron.d/tms_cron

# Command to start cron and tail logs
CMD cron && tail -f /var/log/etl.log
