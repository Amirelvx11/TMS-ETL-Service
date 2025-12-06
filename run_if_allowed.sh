#!/bin/bash

HOUR=$(date +%H)

if [ "$HOUR" -ge 8 ] && [ "$HOUR" -lt 20 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ETL Process Started!" >> /var/log/etl_scheduler.log
    /usr/local/bin/python /app/main.py >> /var/log/etl.log 2>&1
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Outside allowed hours, ETL Process skipped" >> /var/log/etl_scheduler.log
fi
