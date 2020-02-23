NUMBER_KANJI = '一二三四五六七八九十百千万'
NUMBER_SUJI = '１２３４５６７８９０'
NUMBER_ROMAN = 'ivx'
IROHA = 'イロハニホヘトチリヌルヲ'
GENGO_LIST = ['明治', '大正', '昭和', '平成', '令和']
PATTERN_LAW_NUMBER = r'(?:{0})[{1}]+年法律第[{1}]+号'.format('|'.join(GENGO_LIST), NUMBER_KANJI)
