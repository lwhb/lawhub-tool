#!/bin/bash
set -u

# 議案JSONに対しparse_gian.pyを適用する

dataset=./data/json.list

IFS=$'\t'
while read -r fp; do
  ./parse_gian.py "$fp"
done <${dataset}
