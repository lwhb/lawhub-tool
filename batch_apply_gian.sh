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
  before=${gian%.*}.before
  after=${gian%.*}.after
  applied=${gian%.*}.applied
  failed=${gian%.*}.failed

  ./get_law.py -g ${gian} -l ${law}
  if test -f "${law}"; then
    ./apply_gian.py -l ${law} -o ${before}
    ./apply_gian.py -l ${law} -g ${gian} -o ${after} -s ${stat} -a ${applied} -f ${failed}
  fi
done <${dataset}
