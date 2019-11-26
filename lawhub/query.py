from collections import defaultdict
from logging import getLogger

from lawhub.law import LawHierarchy, extract_law_hierarchy

LOGGER = getLogger(__name__)


class Query:
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
        self.hierarchy = defaultdict(lambda: '')

        for law_hrchy in LawHierarchy:
            val = extract_law_hierarchy(text, law_hrchy)
            if val != '':
                self.set(law_hrchy, val)

    def __eq__(self, other):
        if not (isinstance(other, Query)):
            return False
        return self.hierarchy == other.hierarchy

    def __hash__(self):
        return hash(self.hierarchy)

    def get(self, law_hrchy):
        return self.hierarchy[law_hrchy]

    def set(self, law_hrchy, val):
        self.hierarchy[law_hrchy] = val
        return True

    def has(self, law_hrchy, include_placeholder=False):
        val = self.get(law_hrchy)
        if include_placeholder:
            return len(val) > 0
        else:
            return len(val) > 0 and val[0] != '同'  # ignore '同条', '同項', '同号'

    def clear(self, law_hrchy):
        return self.set(law_hrchy, '')

    def is_empty(self):
        for val in self.hierarchy.values():
            if val != '':
                return False
        return True

    def to_dict(self):
        return {'text': self.text, 'hierarchy': self.hierarchy}


class QueryCompensator:
    def __init__(self):
        self.context = dict()

    def compensate(self, query):
        do_compensate = False
        for law_hrchy in (LawHierarchy.ITEM, LawHierarchy.PARAGRAPH, LawHierarchy.ARTICLE):  # bottom-up order for do_compensate
            if query.has(law_hrchy):
                self.context[law_hrchy] = query.get(law_hrchy)
                do_compensate = True
            elif query.has(law_hrchy, include_placeholder=True):
                if not (law_hrchy in self.context):
                    msg = f'failed to compensate {law_hrchy.name} for {query.text} from {self.context}'
                    raise ValueError(msg)
                query.set(law_hrchy, self.context[law_hrchy])
                do_compensate = True
            elif do_compensate and law_hrchy in self.context:
                query.set(law_hrchy, self.context[law_hrchy])
            # elif do_compensate and law_hrchy == LawHierarchy.PARAGRAPH:  # AdHoc fix for cases like "第四条第二号"
            #     query.set(law_hrchy, '第一項')
        return query
