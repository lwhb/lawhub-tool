from logging import getLogger

import MeCab

LOGGER = getLogger(__name__)
WAKATI = MeCab.Tagger("-Owakati")
CHASEN = MeCab.Tagger("-Ochasen")


def parse_by_chasen(sentence):
    result = [line.split('\t') for line in CHASEN.parse(sentence).split('\n')]
    eos_idx = len(result) - 2
    assert result[eos_idx][0] == 'EOS'
    for row in result[:eos_idx]:
        assert len(row) == 6
    return result[:eos_idx]


def normalize_last_verb(sentence):
    if not sentence:
        return sentence
    result = parse_by_chasen(sentence)
    ret = ''.join(map(lambda row: row[0], result[:-1]))
    if result[-1][3].startswith('動詞'):
        ret += result[-1][2]
    else:
        ret += result[-1][0]
    return ret


def split_with_escape(sentence):
    parts = list()
    buffer = ''
    escape_count = 0

    for char in sentence.strip():
        if char in ['、', '。'] and escape_count == 0:
            parts.append(buffer)
            buffer = ''
        else:
            if char == '「':
                escape_count += 1
            if char == '」':
                escape_count -= 1
            buffer += char
    if len(buffer) > 0:
        parts.append(buffer)
    return parts


def mask_escape(text):
    escape_pairs = []  # (start, end)
    escape_count = 0
    start = None
    for i, c in enumerate(text):
        if c == '「':
            escape_count += 1
            if escape_count == 1:
                start = i
        elif start and c == '」':
            escape_count -= 1
            if escape_count == 0:
                escape_pairs.append((start, i + 1))

    new_text = ''
    placeholder = 'A'
    placeholder_map = dict()

    prev_end = 0
    for start, end in escape_pairs:
        new_text += text[prev_end:start] + '{' + placeholder + '}'
        placeholder_map[placeholder] = text[start:end]
        placeholder = chr(ord(placeholder) + 1)
        prev_end = end
    new_text += text[prev_end:]

    return new_text, placeholder_map
