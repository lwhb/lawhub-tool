#!/usr/bin/env python3

import glob

pattern = '/Users/musui/lawhub/lawhub-spider/data/*/*/*/houan.json'
with open('pipeline.arg', 'w') as f:
    for fp in sorted(glob.glob(pattern)):
        gian_id = '-'.join(fp.split('/')[-4:-1])
        f.write(gian_id + '\n')
