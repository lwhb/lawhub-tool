import copy
from enum import Enum
from logging import getLogger

from lawhub.law import LawHierarchy
from lawhub.serializable import Serializable

LOGGER = getLogger(__name__)


class QueryType(str, Enum):
    AT_HIERARCHY = 'at_hierarchy'
    AFTER_HIERARCHY = 'after_hierarchy'


class Query(Serializable):
    """
    法令内の位置を表現するクラス
    """

    law_hierarchy_lst = [LawHierarchy.ARTICLE, LawHierarchy.PARAGRAPH, LawHierarchy.ITEM, LawHierarchy.SUBITEM1, LawHierarchy.SUBITEM2]

    def __init__(self, text, hierarchy=None):
        if text is None:
            text = ''
        self.text = text
        if hierarchy:
            self.hierarchy = hierarchy
        else:
            self.hierarchy = dict()
            for hrchy in Query.law_hierarchy_lst:
                self.set(hrchy, hrchy.extract(text))  # default ''

    @classmethod
    def from_text(cls, text):
        return cls(text=text)

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
            if val:
                return False
        return True


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
