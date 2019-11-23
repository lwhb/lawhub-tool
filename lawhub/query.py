import re
from enum import Enum
from logging import getLogger

from lawhub.constants import NUMBER_KANJI

LOGGER = getLogger(__name__)


class LawDivision(str, Enum):
    JOU = 'jou'
    KOU = 'kou'
    GOU = 'gou'


class Query:
    def __init__(self, text):
        self.text = text
        self.jou = ''
        self.kou = ''
        self.gou = ''

        for law_div in LawDivision:
            val = extract_law_division(text, law_div)
            if val != '':
                self.set(law_div, val)

    def __repr__(self):
        return f'<Query text={self.text} jou={self.jou} kou={self.kou} gou={self.gou}>'

    def __eq__(self, other):
        if not (isinstance(other, Query)):
            return False
        return self.text == other.text and self.jou == other.jou and self.kou == other.kou and self.gou == other.gou

    def get(self, law_div):
        if law_div == LawDivision.JOU:
            return self.jou
        elif law_div == LawDivision.KOU:
            return self.kou
        elif law_div == LawDivision.GOU:
            return self.gou
        else:
            msg = f'invalid law division: {law_div}'
            raise ValueError(msg)

    def set(self, law_div, val):
        if law_div == LawDivision.JOU:
            self.jou = val
        elif law_div == LawDivision.KOU:
            self.kou = val
        elif law_div == LawDivision.GOU:
            self.gou = val
        else:
            msg = f'invalid law division: {law_div}'
            raise ValueError(msg)
        return True

    def has(self, law_div, include_placeholder=False):
        val = self.get(law_div)
        if include_placeholder:
            return len(val) > 0
        else:
            return len(val) > 0 and val[0] != '同'  # ignore '同条', '同項', '同号'

    def clear(self, law_div):
        return self.set(law_div, '')

    def to_dict(self):
        return {'text': self.text, 'jou': self.jou, 'kou': self.kou, 'gou': self.gou}


class QueryCompensator:
    def __init__(self):
        self.context = dict()

    def compensate(self, query):
        do_compensate = False
        for law_div in (LawDivision.GOU, LawDivision.KOU, LawDivision.JOU):  # bottom-up order for do_compensate
            if query.has(law_div):
                self.context[law_div] = query.get(law_div)
                do_compensate = True
            elif query.has(law_div, include_placeholder=True):
                if not(law_div in self.context):
                    msg = f'failed to compensate {law_div.name} for {query.text} from {self.context}'
                    raise ValueError(msg)
                query.set(law_div, self.context[law_div])
                do_compensate = True
            elif do_compensate and law_div in self.context:
                query.set(law_div, self.context[law_div])
        return query


def extract_law_division(string, law_div):
    if law_div == LawDivision.JOU:
        pattern = r'第[{0}]+条(の[{0}]+)?|同条'.format(NUMBER_KANJI)
    elif law_div == LawDivision.KOU:
        pattern = r'第[{0}]+項|同項'.format(NUMBER_KANJI)
    elif law_div == LawDivision.GOU:
        pattern = r'第[{0}]+号|同号'.format(NUMBER_KANJI)
    else:
        msg = f'invalid law division: {law_div}'
        raise ValueError(msg)

    m = re.search(pattern, string)
    if m:
        return m.group()
    else:
        return ''
