import copy
import re
from enum import Enum
from logging import getLogger

from lawhub.law import LawHierarchy, extract_law_hierarchy

LOGGER = getLogger(__name__)


class QueryType(str, Enum):
    AT_HIERARCHY = 'at_hierarchy'
    AFTER_WORD = 'after_word'
    AFTER_HIERARCHY = 'after_hierarchy'


class Query:
    """
    法令内の位置を表現するクラス
    """

    law_hierarchy_lst = [LawHierarchy.ARTICLE, LawHierarchy.PARAGRAPH, LawHierarchy.ITEM, LawHierarchy.SUBITEM1, LawHierarchy.SUBITEM2]

    def __init__(self, obj):
        if isinstance(obj, dict):
            self.__init_by_dict__(obj)
        elif isinstance(obj, str):
            self.__init_by_str__(obj)
        else:
            msg = f'Failed to instantiate Query from {type(obj)}'
            raise NotImplementedError(msg)

    def __init_by_dict__(self, data):
        try:
            self.query_type = QueryType(data['query_type'])
            self.text = data['text']
            self.hierarchy = data['hierarchy']
            if self.query_type == QueryType.AFTER_WORD:
                self.word = data['word']
        except Exception as e:
            msg = f'Failed to instantiate Query from {data}: {e}'
            raise ValueError(msg)

    def __init_by_str__(self, text):
        self.text = text  # ToDo: 複数箇所を指定している場合に対応する

        if self.__init_after_word__(text):
            self.query_type = QueryType.AFTER_WORD
        elif self.__init_after_hierarchy__(text):
            self.query_type = QueryType.AFTER_HIERARCHY
        elif self.__init_at_hierarchy__(text):  # always success
            self.query_type = QueryType.AT_HIERARCHY
        else:
            msg = f'Failed to instantiate Query with text="{text}"'
            raise ValueError(msg)

    def __init_hierarchy__(self, text):
        self.hierarchy = dict()
        for hrchy in Query.law_hierarchy_lst:
            self.set(hrchy, extract_law_hierarchy(text, hrchy))  # default ''

    def __init_at_hierarchy__(self, text):
        self.__init_hierarchy__(text)
        return True

    def __init_after_word__(self, text):
        pattern = r'(.*)中「(.*)」の下'
        match = re.match(pattern, text)
        if match:
            self.__init_hierarchy__(match.group(1))
            self.word = match.group(2)
            return True
        return False

    def __init_after_hierarchy__(self, text):
        pattern = r'(.*)の次'
        match = re.match(pattern, text)
        if match:
            self.__init_hierarchy__(match.group(1))
            return True
        return False

    def __eq__(self, other):
        if not (isinstance(other, Query)):
            return False
        for hrchy in Query.law_hierarchy_lst:
            if self.get(hrchy) != other.get(hrchy):
                return False
        return True

    def __hash__(self):
        return hash(''.join(map(lambda x: self.get(x), Query.law_hierarchy_lst)))

    def __repr__(self):
        return '<Query text={0} {1}>'.format(self.text, ';'.join(map(lambda x: self.get(x), Query.law_hierarchy_lst)))

    def get(self, hrchy):
        return self.hierarchy[hrchy.name]

    def set(self, hrchy, val):
        self.hierarchy[hrchy.name] = val
        return True

    def has(self, hrchy, include_placeholder=False):
        val = self.get(hrchy)
        if include_placeholder:
            return len(val) > 0
        else:
            return len(val) > 0 and val[0] != '同'  # ignore '同条', '同項', '同号'

    def clear(self, hrchy):
        return self.set(hrchy, '')

    def is_empty(self):
        for val in self.hierarchy.values():
            if val != '':
                return False
        return True

    def to_dict(self):
        data = {
            'query_type': self.query_type,
            'text': self.text,
            'hierarchy': self.hierarchy
        }
        if self.query_type == QueryType.AFTER_WORD:
            data['word'] = self.word
        return data


class QueryCompensator:
    """
    文脈を元にQueryを補完するクラス。Actionを独立して適用できるよう「同項」といった自然言語の省略表現を冗長に書き下す必要がある
    """

    def __init__(self):
        self.context = Query('')

    def compensate(self, query):
        if query.text == '':
            return copy.deepcopy(self.context)

        do_compensate = False
        for hrchy in (LawHierarchy.ITEM, LawHierarchy.PARAGRAPH, LawHierarchy.ARTICLE):  # bottom-up order for do_compensate
            if query.has(hrchy):
                do_compensate = True
            elif query.has(hrchy, include_placeholder=True):
                if not self.context.has(hrchy):
                    msg = f'failed to compensate {hrchy.name} for {query.text} from {self.context}'
                    raise ValueError(msg)
                query.set(hrchy, self.context.get(hrchy))
                do_compensate = True
            elif do_compensate and self.context.has(hrchy):
                query.set(hrchy, self.context.get(hrchy))
        if do_compensate and not (query.has(LawHierarchy.PARAGRAPH)):
            query.set(LawHierarchy.PARAGRAPH, '第一項')
        self.context = copy.deepcopy(query)
        return query
