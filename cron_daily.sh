#!/bin/bash --login

# configure daily cron job with `crontab -e` like this:
# 0 0 * * * /home/ec2-user/lawhub/lawhub-tool/cron_daily.sh &> /home/ec2-user/lawhub/data/log/cron_daily.log

set -ue

current_date=$(date +%Y-%m-%d)
echo "start daily cron job on $current_date"

export PIPENV_PIPFILE=$LAWHUB_ROOT/lawhub-dev/Pipfile
cd $LAWHUB_ROOT/lawhub-dev && git checkout master && git pull && ./init.sh
logrotate $LAWHUB_ROOT/lawhub-tool/logrotate.conf -s /tmp/logrotate.state

# crawl e-Gov data
cd $LAWHUB_ROOT/lawhub-spider && pipenv run scrapy crawl egov
cd $LAWHUB_DATA/egov && rm -rf ./*/ && unzip "*.zip" &>/dev/null

# update lawhub-xml
cd $LAWHUB_ROOT/lawhub-tool && pipenv run python update_lawhub_xml.py
cd $LAWHUB_ROOT/lawhub-xml && git add -A && git commit -m "$current_date" && git tag "$current_date" && git push && git push --tags

# update lawhub
latest_tag=$(cd $LAWHUB_ROOT/lawhub-xml && git describe --tags)
if [ $latest_tag = $current_date ]; then
  cd $LAWHUB_ROOT/lawhub-tool && pipenv run python update_lawhub.py
  cd $LAWHUB_ROOT/lawhub && git add -A && git commit -m "$current_date" && git tag "$current_date" && git push && git push --tags
else
  echo "skipped updating lawhub repo as lawhub-xml is last updated at $latest_tag"
fi

# run gian pipeline
cd $LAWHUB_ROOT/lawhub-spider && pipenv run scrapy crawl gian
cd $LAWHUB_ROOT/lawhub-tool && pipenv run python pipeline.py

echo "finished daily cron job on $current_date successfully"
