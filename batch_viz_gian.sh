#!/bin/bash
set -u

dataset=./data/json.list
IFS=$'\t'
while read -r gian; do
  out=${gian%/*}/applied.html
  ./viz_gian.py -g ${gian} -o ${out}
done <${dataset}
