#!/bin/bash
set -u

# 議案JSONに対しparse_gian.pyを適用する

dataset=./data/json.list
stat=./data/parse_gian.stat
[ -e ${stat} ] && rm ${stat}

IFS=$'\t'
while read -r fp; do
  ./parse_gian.py ${fp} ${stat}
done <${dataset}
