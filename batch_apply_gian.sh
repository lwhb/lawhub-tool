#!/bin/bash
set -u

# 1. 議案JSONLinesから対象法案を取得、
# 2. （取得できた場合）議案を適用したBefore, Afterを保存する

dataset=./data/jsonl.list

IFS=$'\t'
while read -r gian; do
  law=${gian%.*}.xml
  bef=${gian%.*}.bef
  aft=${gian%.*}.aft

  ./get_law.py "${gian}" "${law}"
  if test -f "${law}"; then
    ./apply_gian.py /dev/null "${law}" "${bef}"
    ./apply_gian.py "${gian}" "${law}" "${aft}"
  fi
done <${dataset}
