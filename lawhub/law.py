import re
import xml.etree.ElementTree as ET
from collections import deque
from enum import Enum
from logging import getLogger

from lawhub.constants import NUMBER, NUMBER_KANJI, NUMBER_SUJI, NUMBER_ROMAN, IROHA, PATTERN_LAW_NUMBER
from lawhub.kanzize import int2kanji
from lawhub.serializable import Serializable

LOGGER = getLogger(__name__)
SPACE = ' '
INDENT = SPACE * 4


class LawHierarchy(Enum):
    """
    e-gov法令APIのXMLにおける階層名の一覧（階層順）
    """

    CONTENTS = '目次'
    SUPPLEMENT = '附則'
    PART = '編'
    CHAPTER = '章'
    SECTION = '節'
    SUBSECTION = '款'
    DIVISION = '目'
    ARTICLE = '条'
    PARAGRAPH = '項'
    ITEM = '号'
    SUBITEM1 = 'イ'
    SUBITEM2 = '（１）'
    SUBITEM3 = '（ｉ）'
    SUBITEM4 = '（イ）'
    TABLE = '表'

    def extract(self, string, allow_placeholder=True, allow_partial_match=True):
        """
        文字列から対象の文字列を検出する

        :param allow_placeholder: '同条'という表現を許可する
        :param allow_partial_match: 部分一致を許可する
        """
        if self == LawHierarchy.SUBITEM1:
            pattern = r'[{0}]'.format(IROHA)
        elif self == LawHierarchy.SUBITEM2:
            pattern = r'\([{0}]+\)|（[{1}]+）'.format(NUMBER, NUMBER_SUJI)
        elif self == LawHierarchy.SUBITEM3:
            pattern = r'\([{0}]+\)|（[{0}]+）'.format(NUMBER_ROMAN)
        elif self == LawHierarchy.SUBITEM4:
            pattern = r'\([{0}]+\)|（[{0}]+）'.format(IROHA)
        elif self in [LawHierarchy.SUPPLEMENT, LawHierarchy.CONTENTS, LawHierarchy.TABLE]:
            pattern = self.value
        else:
            pattern = r'第[{0}]+{1}(の[{0}]+)*'.format(NUMBER_KANJI, self.value)
            if allow_placeholder:
                pattern += '|同{0}'.format(self.value)

        if allow_partial_match:
            m = re.search(pattern, string)
        else:
            m = re.fullmatch(pattern, string)
        if m:
            return m.group()
        else:
            return ''

    def children(self, include_self=False):
        flag = False
        children = []
        for hrchy in LawHierarchy:
            if flag:
                children.append(hrchy)
            else:
                if hrchy == self:
                    flag = True
                    if include_self:
                        children.append(hrchy)
        return children

    @staticmethod
    def from_text(text):
        for hrchy in LawHierarchy:
            if hrchy.value == text:
                return hrchy
        raise ValueError(f'failed to instantiate LawHierarchy from "{text}"')

    @staticmethod
    def first():
        return list(LawHierarchy)[0]

    @staticmethod
    def last():
        return list(LawHierarchy)[-1]


def extract_text_from_sentence(node):
    text = ET.tostring(node, encoding="unicode")
    text = text.replace('\n', '')
    text = re.sub(r'<Ruby>([^<>]*)<Rt>([^<>]*)</Rt></Ruby>', r'\1', text)  # replace <Ruby>
    text = re.sub(r'<[^<>]*>', '', text)  # replace all tags, such as <Sentence>
    return text.strip()


def extract_law_meta(xml_fp):
    """
    LawのXMLファイルからメタデータを抽出する
    """

    tree = ET.parse(xml_fp)
    assert tree.getroot().tag == 'Law'
    meta = {'LawNum': tree.find('LawNum').text,
            'LawTitle': tree.find('LawBody').find('LawTitle').text}
    meta.update(tree.getroot().attrib)
    return meta


def extract_target_law_meta(text):
    """
    改正文から対象の法律のメタデータを抽出する
    """

    pattern = r'([^"（）]*)(?:（({})）)?の一部を次のように改正する'.format(PATTERN_LAW_NUMBER)
    m = re.search(pattern, text)
    if not m:
        raise ValueError('does not contain law info')
    meta = {'LawTitle': m.group(1)}
    if m.group(2):
        meta['LawNum'] = m.group(2)
    return meta


def parse_xml_fp(xml_fp):
    """
    Lawのxmlファイルの本文をBaseLawClassに変換した結果を返す
    """
    tree = ET.parse(xml_fp)
    assert tree.getroot().tag == 'Law'
    main = tree.find('LawBody').find('MainProvision')
    return [parse_xml(node) for node in main]


def parse_xml(node):
    """
    XMLのnodeを与えられて、再帰的に子ノードまでBaseLawClassに変換した結果を返す

    :param node: node in XML tree
    :return: node in BaseLawClass tree
    """
    if node.tag == 'Part':
        return Part.from_xml(node)
    elif node.tag == 'Chapter':
        return Chapter.from_xml(node)
    elif node.tag == 'Section':
        return Section.from_xml(node)
    elif node.tag == 'Subsection':
        return Subsection.from_xml(node)
    elif node.tag == 'Division':
        return Division.from_xml(node)
    elif node.tag == 'Article':
        return Article.from_xml(node)
    elif node.tag == 'Paragraph':
        return Paragraph.from_xml(node)
    elif node.tag == 'Item':
        return Item.from_xml(node)
    elif node.tag == 'Subitem1':
        return Subitem1.from_xml(node)
    elif node.tag == 'Subitem2':
        return Subitem2.from_xml(node)
    elif node.tag == 'Subitem3':
        return Subitem3.from_xml(node)
    elif node.tag == 'Subitem4':
        return Subitem4.from_xml(node)
    elif node.tag == 'TableStruct':
        return BaseLawClass(title='<表略>')
    elif node.tag == 'List':
        return BaseLawClass(title='<一覧略>')
    elif node.tag == 'FigStruct':
        return BaseLawClass(title='<図略>')
    elif node.tag == 'AmendProvision':
        return BaseLawClass(title='<修正略>')
    elif node.tag == 'SupplNote':
        return BaseLawClass(title='<注釈略>')
    else:
        LOGGER.debug(f'Unknown Element {node.tag}: {node}')
        return BaseLawClass(title='<{node.tag}略>')


def save_law_tree(law_title, nodes, fp):
    with open(fp, 'w') as f:
        f.write(f'{law_title}\n\n')
        for node in nodes:
            f.write(f'{node}\n')


def sort_law_tree(node):
    for child in node.children:
        sort_law_tree(child)
    for sortable_class in [Article, Paragraph]:
        if all(map(lambda x: isinstance(x, sortable_class), node.children)):
            node.children.sort()
            break


class BaseLawClass(Serializable):
    hierarchy = None

    def __init__(self, title=None, children=None):
        self.title = title if title else ''
        self.children = children if children else list()

    def __str__(self):
        body = self.title
        if self.children:
            body += '\n' + self.__str_children__()
        return body

    def __str_children__(self):
        return '\n'.join(map(lambda x: x.__str__(), self.children))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.title}>'

    def __eq__(self, other):
        return isinstance(other, BaseLawClass) and self.title == other.title


class BaseSectionClass(BaseLawClass):
    @classmethod
    def from_xml(cls, node):
        title = node[0].text
        children = [parse_xml(child) for child in node[1:]]
        return cls(title=title, children=children)

    def __str__(self):
        return super().__str__() + '\n'


class Part(BaseSectionClass):
    hierarchy = LawHierarchy.PART

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Part'
        assert node[0].tag == 'PartTitle'
        return super().from_xml(node)


class Chapter(BaseSectionClass):
    hierarchy = LawHierarchy.CHAPTER

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Chapter'
        assert node[0].tag == 'ChapterTitle'
        return super().from_xml(node)


class Section(BaseSectionClass):
    hierarchy = LawHierarchy.SECTION

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Section'
        assert node[0].tag == 'SectionTitle'
        return super().from_xml(node)


class Subsection(BaseSectionClass):
    hierarchy = LawHierarchy.SUBSECTION

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Subsection'
        assert node[0].tag == 'SubsectionTitle'
        return super().from_xml(node)


class Division(BaseSectionClass):
    hierarchy = LawHierarchy.DIVISION

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Division'
        assert node[0].tag == 'DivisionTitle'
        return super().from_xml(node)


class Article(BaseLawClass):
    hierarchy = LawHierarchy.ARTICLE

    def __init__(self, title=None, caption=None, number=None, children=None):
        super().__init__(title, children)
        self.caption = caption if caption else ''
        self.number = number if number else '1'

    def is_caption_only(self):
        return self.title == '' and self.caption != ''

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Article'
        assert 'Num' in node.attrib
        number = node.attrib['Num']
        if node[0].tag == 'ArticleCaption' and node[1].tag == 'ArticleTitle':
            caption = node[0].text
            title = node[1].text
            children = [parse_xml(child) for child in node[2:]]
        elif node[0].tag == 'ArticleTitle':
            caption = None
            title = node[0].text
            children = [parse_xml(child) for child in node[1:]]
        else:
            assert False
        return cls(title=title, caption=caption, number=number, children=children)

    def __str__(self):
        body = self.caption + '\n' + self.title if self.caption else self.title
        if self.children:
            body += SPACE + self.__str_children__()
        return body + '\n'

    def __eq__(self, other):
        return isinstance(other, Article) and self.title == other.title and self.caption == other.caption and self.number == other.number

    def __lt__(self, other):
        def clean(number):
            return re.sub(r'[^0-9]', '_', number)  # adhoc fix to handle '226:227' in 昭和二十五年法律第二百三十九号

        if not isinstance(other, Article):
            raise NotImplementedError(f'can not compare \"{type(other)}\" with Article')

        for i, j in zip(map(lambda x: int(x), clean(self.number).split('_')),
                        map(lambda x: int(x), clean(other.number).split('_'))):
            if i < j:
                return True
            elif i > j:
                return False
        return len(self.number) < len(other.number)


class Paragraph(BaseLawClass):
    hierarchy = LawHierarchy.PARAGRAPH

    def __init__(self, title=None, number=None, sentence=None, children=None):
        if (not title) and number:
            title = '第{}項'.format(int2kanji(int(number)))
        super().__init__(title, children)
        self.number = number if number else 1
        self.sentence = sentence if sentence else ''

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Paragraph'
        assert node[0].tag == 'ParagraphNum'
        assert node[1].tag == 'ParagraphSentence'
        assert 'Num' in node.attrib
        number = int(node.attrib['Num'])
        sentence = ''.join(map(lambda n: extract_text_from_sentence(n), node[1].findall('.//Sentence')))
        children = [parse_xml(child) for child in node[2:]]
        return cls(number=number, sentence=sentence, children=children)

    def __str__(self):
        if self.number == 1:
            body = self.sentence
        else:
            body = str(self.number) + SPACE + self.sentence
        if self.children:
            body += '\n' + self.__str_children__()
        return body

    def __eq__(self, other):
        return isinstance(other, Paragraph) and self.title == other.title and self.number == other.number and self.sentence == other.sentence

    def __lt__(self, other):
        if not isinstance(other, Paragraph):
            raise NotImplementedError(f'can not compare \"{type(other)}" with Paragraph')
        return self.number < other.number


class BaseItemClass(BaseLawClass):
    def __init__(self, title=None, sentence=None, children=None):
        super().__init__(title, children)
        self.sentence = sentence if sentence else ''

    @classmethod
    def from_xml(cls, node):
        title = node[0].text
        sentence = INDENT.join(map(lambda n: extract_text_from_sentence(n), node[1].findall('.//Sentence')))
        children = [parse_xml(child) for child in node[2:]]
        return cls(title=title, sentence=sentence, children=children)

    def __str__(self):
        body = self.title + SPACE + self.sentence
        if self.children:
            body += '\n' + self.__str_children__()
        return body

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.title} {self.sentence}>'

    def __eq__(self, other):
        return isinstance(other, BaseItemClass) and self.title == other.title and self.sentence == other.sentence


class Item(BaseItemClass):
    hierarchy = LawHierarchy.ITEM

    def __init__(self, title=None, sentence=None, children=None):
        if not (len(title) > 2 and title[0] == '第' and title[-1] == '号'):
            title = f'第{title}号'
        super().__init__(title, sentence, children)

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Item'
        assert node[0].tag == 'ItemTitle'
        assert node[1].tag == 'ItemSentence'
        return super().from_xml(node)

    def __str__(self):
        body = self.title[1:-1] + SPACE + self.sentence if self.title else self.sentence
        if self.children:
            body += '\n' + self.__str_children__()
        return INDENT + body


class Subitem1(BaseItemClass):
    hierarchy = LawHierarchy.SUBITEM1

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Subitem1'
        assert node[0].tag == 'Subitem1Title'
        assert node[1].tag == 'Subitem1Sentence'
        return super().from_xml(node)

    def __str__(self):
        return INDENT * 2 + super().__str__()


class Subitem2(BaseItemClass):
    hierarchy = LawHierarchy.SUBITEM2

    def __init__(self, title=None, sentence=None, children=None):
        super().__init__(title, sentence, children)

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Subitem2'
        assert node[0].tag == 'Subitem2Title'
        assert node[1].tag == 'Subitem2Sentence'
        return super().from_xml(node)

    def __str__(self):
        return INDENT * 3 + super().__str__()


class Subitem3(BaseItemClass):
    hierarchy = LawHierarchy.SUBITEM3

    def __init__(self, title=None, sentence=None, children=None):
        super().__init__(title, sentence, children)

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Subitem3'
        assert node[0].tag == 'Subitem3Title'
        assert node[1].tag == 'Subitem3Sentence'
        return super().from_xml(node)

    def __str__(self):
        return INDENT * 4 + super().__str__()


class Subitem4(BaseItemClass):
    hierarchy = LawHierarchy.SUBITEM4

    def __init__(self, title=None, sentence=None, children=None):
        super().__init__(title, sentence, children)

    @classmethod
    def from_xml(cls, node):
        assert node.tag == 'Subitem4'
        assert node[0].tag == 'Subitem4Title'
        assert node[1].tag == 'Subitem4Sentence'
        return super().from_xml(node)

    def __str__(self):
        return INDENT * 5 + super().__str__()


class LawTreeBuilder:
    """
    Build LawTree bottom-up
    """

    def __init__(self):
        self.hrchy2nodes = dict()
        for hrchy in LawHierarchy:
            self.hrchy2nodes[hrchy] = list()

    def add(self, node):
        assert isinstance(node, BaseLawClass)

        # special case to merge ArticleCaption
        if isinstance(node, Article) and node.is_caption_only():
            if not (self.hrchy2nodes[LawHierarchy.ARTICLE]):
                raise ValueError("ArticleCaption can not be added without previous Article")
            self.hrchy2nodes[LawHierarchy.ARTICLE][-1].caption = node.caption
            return

        while node.children:
            self.add(node.children.pop())
        try:
            node.children = self._get_children(parent_hrchy=node.hierarchy, flush=True)
        except ValueError as e:
            msg = 'failed to add new node as there are active child nodes at multiple hierarchy'
            raise ValueError(msg) from e
        self.hrchy2nodes[node.hierarchy].append(node)

    def build(self):
        try:
            return self._get_children(parent_hrchy=None, flush=False)
        except ValueError as e:
            msg = 'failed to build LawTree as there are active nodes at multiple hierarchy'
            raise ValueError(msg) from e

    def _get_children(self, parent_hrchy, flush):
        child_hrchy_list = parent_hrchy.children() if parent_hrchy is not None else LawHierarchy
        active_child_hrchy_list = []
        for hrchy in child_hrchy_list:
            if self.hrchy2nodes[hrchy]:
                active_child_hrchy_list.append(hrchy)

        if len(active_child_hrchy_list) == 0:
            return list()
        elif len(active_child_hrchy_list) == 1:
            hrchy = active_child_hrchy_list[0]
            children = self.hrchy2nodes[hrchy][::-1]
            if flush:
                self.hrchy2nodes[hrchy] = list()
            return children
        else:
            msg = 'found multiple active child hierarchy under {0} ({1})'.format(
                parent_hrchy.value if parent_hrchy else 'root',
                ','.join(map(lambda x: x.value, active_child_hrchy_list)))
            raise ValueError(msg)


def title_to_hierarchy(text):
    # special case for Paragraph
    if text.isdigit():
        return LawHierarchy.PARAGRAPH
    # special case for Item
    m = re.fullmatch(r'[{0}]+(の[{0}]+)*'.format(NUMBER_KANJI), text)
    if m:
        return LawHierarchy.ITEM
    for hrchy in LawHierarchy:
        if hrchy.extract(text, allow_placeholder=False, allow_partial_match=False):
            return hrchy
    return None


def line_to_law_node(text):
    if not text:
        return None
    chunks = text.strip().split()
    maybe_title = chunks[0]
    maybe_sentence = ' '.join(chunks[1:])
    maybe_hrchy = title_to_hierarchy(maybe_title)
    if maybe_hrchy == LawHierarchy.PART:
        return Part(title=maybe_title)
    elif maybe_hrchy == LawHierarchy.CHAPTER:
        return Chapter(title=maybe_title)
    elif maybe_hrchy == LawHierarchy.SECTION:
        return Section(title=maybe_title)
    elif maybe_hrchy == LawHierarchy.SUBSECTION:
        return Subsection(title=maybe_title)
    elif maybe_hrchy == LawHierarchy.DIVISION:
        return Division(title=maybe_title)
    elif maybe_hrchy == LawHierarchy.ARTICLE:
        children = []
        if maybe_sentence:
            children.append(Paragraph(title='第一項', number=1, sentence=maybe_sentence))
        return Article(title=maybe_title, children=children)
    elif maybe_hrchy == LawHierarchy.PARAGRAPH:
        return Paragraph(number=int(maybe_title), sentence=maybe_sentence)
    elif maybe_hrchy == LawHierarchy.ITEM:
        return Item(title=maybe_title, sentence=maybe_sentence)
    elif maybe_hrchy == LawHierarchy.SUBITEM1:
        return Subitem1(title=maybe_title, sentence=maybe_sentence)
    elif maybe_hrchy == LawHierarchy.SUBITEM2:
        return Subitem2(title=maybe_title, sentence=maybe_sentence)
    elif maybe_hrchy == LawHierarchy.SUBITEM3:
        return Subitem3(title=maybe_title, sentence=maybe_sentence)

    # special case for ArticleCaption
    match = re.fullmatch(r'(（.+）)', text)
    if match:
        return Article(caption=match.group(1))
    return None


class LawNodeFinder:
    def __init__(self, nodes):
        self.nodes = nodes

    def _find(self, nodes, query, hierarchy):
        subquery = query.get(hierarchy)
        if subquery == '':  # no need to process this hierarchy
            if hierarchy == LawHierarchy.last():
                return nodes
            else:
                return self._find(nodes, query, hierarchy.children()[0])

        # BFS for node that matches subquery
        q = deque(nodes)
        while q:
            node = q.popleft()
            if node.title.startswith(subquery):  # use startswith as title can also includes caption
                if hierarchy == LawHierarchy.last():
                    return [node]
                else:
                    return self._find([node], query, hierarchy.children()[0])
            q.extend(node.children)
        return list()

    def find(self, query):
        if query.has(LawHierarchy.SUPPLEMENT) or query.has(LawHierarchy.CONTENTS) or query.has(LawHierarchy.TABLE):
            raise NotImplementedError
        return self._find(self.nodes, query, LawHierarchy.first())
