#!/usr/bin/env python3

import os
import glob
from pathlib import Path


LAWHUB_DATA = Path(os.environ['LAWHUB_DATA']) if 'LAWHUB_DATA' in os.environ else Path('/var/tmp/data')

pattern = f'{LAWHUB_DATA}/gian/*/*/*/houan.json'
with open('pipeline.arg', 'w') as f:
    for fp in sorted(glob.glob(pattern)):
        gian_id = '-'.join(fp.split('/')[-4:-1])
        f.write(gian_id + '\n')
