#!/bin/bash
# filepath: /root/Ebay-Gold-Scraper/run_daily.sh

# Set the working directory
cd /root/Ebay-Gold-Scraper/backend

# Activate the virtual environment
source /root/Ebay-Gold-Scraper/production_env/bin/activate

# Run the pipeline with logging
python run.py >> /var/log/gold-scraper.log 2>&1

# Optional: Add timestamp to log
echo "$(date): Daily scraper run completed" >> /var/log/gold-scraper.log


# view recent logs: tail -f /var/log/gold-scraper.log
# test the script manually: /root/Ebay-Gold-Scraper/run_daily.sh
# add to cron: crontab -e
# cron entry: 0 9 * * * /root/Ebay-Gold-Scraper/run_daily.sh