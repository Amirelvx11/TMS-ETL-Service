FROM python:3.11-slim

# Install system dependencies for pyodbc + cron
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc \
    unixodbc-dev \
    cron \
    && apt-get clean

# Install Microsoft ODBC Driver 18 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/12/prod.list \
        -o /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cron job every 12 hours
RUN echo "0 */12 * * * python /app/main.py >> /var/log/etl.log 2>&1" > /etc/cron.d/tms_cron
RUN chmod 0644 /etc/cron.d/tms_cron

RUN crontab /etc/cron.d/tms_cron

CMD cron && tail -f /var/log/etl.log
