import os
from pathlib import Path

NUMBER = '0-9'
NUMBER_KANJI = '一二三四五六七八九十百千万'
NUMBER_SUJI = '１２３４５６７８９０'
NUMBER_ROMAN = 'ivx'
IROHA = 'イロハニホヘトチリヌルヲ'
GENGO_LIST = ['明治', '大正', '昭和', '平成', '令和']
PATTERN_LAW_NUMBER = r'(?:{0})[{1}]+年法律第[{2}]+号'.format('|'.join(GENGO_LIST), NUMBER_KANJI + '元', NUMBER_KANJI)
LAWHUB_ROOT = Path(os.environ['LAWHUB_ROOT']) if 'LAWHUB_ROOT' in os.environ else Path('/var/tmp')
LAWHUB_DATA = Path(os.environ['LAWHUB_DATA']) if 'LAWHUB_DATA' in os.environ else Path('/var/tmp/data')
