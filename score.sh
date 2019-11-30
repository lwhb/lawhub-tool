#!/bin/bash
set -u

# 議案一覧のTSVを入力として受け取り、議案を実際に適用するパイプライン
# ToDo: 複数の法令を改正する議案に対応するため、TSVのフォーマットが変更される可能性がある（ISSUE-3）

dataset="./score/single.txt.head"

IFS=$'\t'
while read -r dir law
do
    gian_json=${dir}/houan.json
    gian_jsonl=${dir}/houan.jsonl
    law_xml=${dir}/law.xml
    law_txt_bef=${dir}/law.txt.bef
    law_txt_aft=${dir}/law.txt.aft

    ./parse_gian.py "${gian_json}" "${gian_jsonl}"

    if test -f "${law_xml}"; then
        echo "${law_xml} already exists"
    else
        ./get_law.py "${law}" "${law_xml}"
        sleep 1
    fi

    ./apply_gian.py "${law_xml}" /dev/null "${law_txt_bef}"
    ./apply_gian.py "${law_xml}" "${gian_jsonl}" "${law_txt_aft}"
done < ${dataset}
