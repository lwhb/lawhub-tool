#!/bin/bash --login

# configure daily cron job with `crontab -e` like this:
# 0 0 * * * /home/ec2-user/lawhub/lawhub-tool/cron_daily.sh &> /home/ec2-user/lawhub/data/log/cron_daily.log

set -ue

current_date=$(date +%Y-%m-%d)
echo "start daily cron job on $current_date"

export PIPENV_PIPFILE=$LAWHUB_ROOT/lawhub-dev/Pipfile
logrotate $LAWHUB_ROOT/lawhub-tool/logrotate.conf -s /tmp/logrotate.state

cd LAWHUB_ROOT/lawhub-dev && ./init.sh
cd $LAWHUB_ROOT/lawhub-spider && pipenv run scrapy crawl egov
cd $LAWHUB_DATA/egov && unzip "*.zip" &>/dev/null
cd $LAWHUB_ROOT/lawhub-tool && pipenv run python update_lawhub_xml.py
cd $LAWHUB_ROOT/lawhub-xml && git add -A && git commit -m "$current_date" && git tag $current_date && git push && git push --tags

echo "finished daily cron job on $current_date successfully"
