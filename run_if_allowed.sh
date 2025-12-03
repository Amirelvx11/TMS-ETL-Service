#!/bin/bash

# Current hour (00–23)
HOUR=$(date +%H)

# Allowed window: 08 ≤ hour < 20
if [ "$HOUR" -ge 8 ] && [ "$HOUR" -lt 20 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Running ETL" >> /var/log/etl_scheduler.log
    /usr/local/bin/python /app/main.py >> /var/log/etl.log 2>&1
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Outside allowed hours, ETL skipped" >> /var/log/etl_scheduler.log
fi
