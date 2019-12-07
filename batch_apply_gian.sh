#!/bin/bash
set -u

# 1. 議案JSONLinesから対象法案を取得
# 2. （取得できた場合）議案を適用したBefore, Afterを保存する

dataset=./data/jsonl.list
stat=./data/apply_gian.stat
[ -e ${stat} ] && rm ${stat}

IFS=$'\t'
while read -r gian; do
  law=${gian%.*}.xml
  bef=${gian%.*}.bef
  aft=${gian%.*}.aft

  ./get_law.py -g ${gian} -l ${law}
  if test -f "${law}"; then
    ./apply_gian.py -l ${law} -o ${bef}
    ./apply_gian.py -l ${law} -g ${gian} -o ${aft} -s ${stat}
  fi
done <${dataset}
