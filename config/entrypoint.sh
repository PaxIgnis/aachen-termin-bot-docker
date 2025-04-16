#!/bin/bash

# Create the log file if it doesn't exist
touch /app/config/bot.log

# Run the Python script every 5 minutes
while true; do
    python /app/config/bot.py
    sleep 300 # CHANGE THIS TO YOUR DESIRED TIME INTERVAL IN SECONDS
done