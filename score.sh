#!/bin/bash
set -u

IFS=$'\t'
while read -r dir law
do
    gian_json=${dir}/houan.json
    gian_jsonl=${dir}/houan.jsonl
    law_xml=${dir}/law.xml
    law_txt_bef=${dir}/law.txt.bef
    law_txt_aft=${dir}/law.txt.aft

    if test -f ${gian_jsonl};then
        echo "${gian_jsonl} already exists"
    else
        ./parse_gian.py ${gian_json} ${gian_jsonl}
    fi

    if test -f ${law_xml}; then
        echo "${law_xml} already exists"
    else
        ./get_law.py ${law} ${law_xml}
        sleep 1
    fi

    ./apply_gian.py ${law_xml} /dev/null ${law_txt_bef}
    ./apply_gian.py ${law_xml} ${gian_jsonl} ${law_txt_aft}
done < ./score/dataset.txt.head
