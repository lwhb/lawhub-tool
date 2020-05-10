import copy
from enum import Enum
from logging import getLogger

from lawhub.law import LawHierarchy
from lawhub.serializable import Serializable

LOGGER = getLogger(__name__)


class QueryType(str, Enum):
    AT = 'at'
    AFTER = 'after'
    BEFORE = 'before'


class Query(Serializable):
    """
    法令内の位置を表現するクラス
    """

    def __init__(self, text, query_type, hierarchy_map=None):
        self.text = text
        self.query_type = query_type
        if hierarchy_map:
            self.hierarchy_map = hierarchy_map
        else:
            self.hierarchy_map = dict()
            for hrchy in LawHierarchy:
                maybe_hrchy_text = hrchy.extract(text)
                if maybe_hrchy_text:
                    self.set(hrchy, hrchy.extract(text))

    @classmethod
    def from_text(cls, text):
        text = text if text else ''
        if text.endswith('の次'):
            return cls(text=text, query_type=QueryType.AFTER)
        elif text.endswith('の前'):
            return cls(text=text, query_type=QueryType.BEFORE)
        else:
            return cls(text=text, query_type=QueryType.AT)

    def __eq__(self, other):
        if not (isinstance(other, Query)):
            return False
        for hrchy in LawHierarchy:
            if self.get(hrchy) != other.get(hrchy):
                return False
        return True

    def __hash__(self):
        return hash(';'.join(map(lambda x: f'{x[0]}:{x[1]}', self.hierarchy_map.items())))

    def __repr__(self):
        return '<Query text={0} {1}>'.format(self.text, ';'.join(map(lambda x: f'{x[0]}:{x[1]}', self.hierarchy_map.items())))

    def get(self, hrchy):
        return self.hierarchy_map[hrchy.name] if hrchy.name in self.hierarchy_map else ''

    def set(self, hrchy, val):
        self.hierarchy_map[hrchy.name] = val
        return True

    def has(self, hrchy, include_placeholder=False):
        val = self.get(hrchy)
        if include_placeholder:
            return len(val) > 0
        else:
            return len(val) > 0 and val[0] != '同'  # ignore '同条', '同項', '同号'

    def clear(self, hrchy):
        if hrchy.name in self.hierarchy_map:
            del self.hierarchy_map[hrchy.name]
        return True

    def is_empty(self):
        return not self.hierarchy_map


class QueryCompensator:
    """
    文脈を元にQueryを補完するクラス。Actionを独立して適用できるよう「同項」といった自然言語の省略表現を冗長に書き下す必要がある
    """

    # list of LawHierarchy that needs to be compensated if child hierarchy exists
    target_hierarchies = set(LawHierarchy.ARTICLE.children(include_self=True))

    def __init__(self):
        self.context = Query.from_text('')

    def compensate(self, query):
        # if query.text is omitted
        if query.text == '':
            ret = copy.deepcopy(self.context)
            ret.text = query.text
            return ret

        # if query.text is invalid
        if query.is_empty():
            return query

        has_child = False
        for hrchy in list(LawHierarchy)[::-1]:  # bottom-up order for has_child
            if query.has(hrchy, include_placeholder=True):
                has_child = True
                if not (query.has(hrchy, include_placeholder=False)):  # compensate if placeholder
                    if not self.context.has(hrchy):
                        msg = f'failed to compensate {hrchy.name} for {query.text} from {self.context}'
                        raise ValueError(msg)
                    query.set(hrchy, self.context.get(hrchy))
            elif hrchy in self.target_hierarchies:
                if has_child and self.context.has(hrchy):  # compensate target hierarchies if possible
                    query.set(hrchy, self.context.get(hrchy))
        self.context = copy.deepcopy(query)
        return query
