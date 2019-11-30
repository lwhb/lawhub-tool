from logging import getLogger

from lawhub.law import LawHierarchy, extract_law_hierarchy

LOGGER = getLogger(__name__)


class Query:
    """
    法令内の位置を表現するクラス

    ToDo: 現状LawHierarchyの粒度でしか位置を表現できない、複数の位置を表現できないという問題がある(ISSUE-2)
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
            self.text = data['text']
            self.hierarchy = data['hierarchy']  # ToDo: wrap with defaultdict
        except KeyError as e:
            msg = f'Failed to instantiate Query from {data}'
            raise ValueError(msg)

    def __init_by_str__(self, text):
        self.text = text
        self.hierarchy = dict()
        for hrchy in Query.law_hierarchy_lst:
            self.set(hrchy, extract_law_hierarchy(text, hrchy))  # default ''

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
        return {'text': self.text, 'hierarchy': self.hierarchy}


class QueryCompensator:
    """
    文脈を元にQueryを補完するクラス。Actionを独立して適用できるよう「同項」といった自然言語の省略表現を冗長に書き下す必要がある
    """

    def __init__(self):
        self.context = dict()

    def compensate(self, query):
        do_compensate = False
        for hrchy in (LawHierarchy.ITEM, LawHierarchy.PARAGRAPH, LawHierarchy.ARTICLE):  # bottom-up order for do_compensate
            if query.has(hrchy):
                self.context[hrchy] = query.get(hrchy)
                do_compensate = True
            elif query.has(hrchy, include_placeholder=True):
                if not (hrchy in self.context):
                    msg = f'failed to compensate {hrchy.name} for {query.text} from {self.context}'
                    raise ValueError(msg)
                query.set(hrchy, self.context[hrchy])
                do_compensate = True
            elif do_compensate and hrchy in self.context:
                query.set(hrchy, self.context[hrchy])
        if do_compensate and not (query.has(LawHierarchy.PARAGRAPH)):
            query.set(LawHierarchy.PARAGRAPH, '第一項')
        return query
