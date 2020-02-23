import re
import xml.etree.ElementTree as ET
from enum import Enum
from logging import getLogger

from lawhub.constants import NUMBER_KANJI, NUMBER_SUJI, NUMBER_ROMAN, IROHA
from lawhub.kanzize import int2kanji
from lawhub.serializable import Serializable

LOGGER = getLogger(__name__)
SPACE = ' '
INDENT = SPACE * 4


class LawHierarchy(str, Enum):
    """
    e-gov法令APIのXMLにおける階層名の一覧
    """

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


def extract_law_hierarchy(string, hrchy):
    if hrchy not in LawHierarchy:
        msg = f'invalid law division: {hrchy}'
        raise ValueError(msg)
    elif hrchy == LawHierarchy.ARTICLE:
        pattern = r'第[{0}]+条(の[{0}]+)*|同条'.format(NUMBER_KANJI)
    elif hrchy == LawHierarchy.SUBITEM1:
        pattern = r'[{0}]'.format(IROHA)
    elif hrchy == LawHierarchy.SUBITEM2:
        pattern = r'（[{0}]+）'.format(NUMBER_SUJI)
    elif hrchy == LawHierarchy.SUBITEM3:
        pattern = r'（[{0}]+）'.format(NUMBER_ROMAN)
    else:
        pattern = r'第[{0}]+{1}|同{1}'.format(NUMBER_KANJI, hrchy.value)

    m = re.search(pattern, string)
    if m:
        return m.group()
    else:
        return ''


def extract_text_from_sentence(node):
    text = ET.tostring(node, encoding="unicode")
    text = text.replace('\n', '')
    text = re.sub(r'<Ruby>([^<>]*)<Rt>([^<>]*)</Rt></Ruby>', r'\1', text)  # replace <Ruby>
    text = re.sub(r'<[^<>]*>', '', text)  # replace all tags, such as <Sentence>
    return text.strip()


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
    elif node.tag == 'TableStruct':
        return BaseLawClass(title='<表略>')
    elif node.tag == 'List':
        return BaseLawClass(title='<一覧略>')
    else:
        msg = f'Unknown Element {node.tag}: {node}'
        raise NotImplementedError(msg)


def sort_law_tree(node):
    for child in node.children:
        sort_law_tree(child)
    for sortable_class in [Article, Paragraph]:
        if all(map(lambda x: isinstance(x, sortable_class), node.children)):
            node.children.sort()
            break


class BaseLawClass(Serializable):
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
            body += '\n' + self.__str_children__()
        return body + '\n'

    def __eq__(self, other):
        if not isinstance(other, Article):
            raise NotImplementedError(f'can not compare \"{type(other)}\" with Article')
        return self.number == other.number

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
        title = '第{}項'.format(int2kanji(int(number)))
        sentence = ''.join(map(lambda n: extract_text_from_sentence(n), node[1].findall('.//Sentence')))
        children = [parse_xml(child) for child in node[2:]]
        return cls(title=title, number=number, sentence=sentence, children=children)

    def __str__(self):
        body = str(self.number) + SPACE + self.sentence
        if self.children:
            body += '\n' + self.__str_children__()
        return body

    def __eq__(self, other):
        if not isinstance(other, Paragraph):
            raise NotImplementedError(f'can not compare \"{type(other)}\" with Paragraph')
        return self.number == other.number

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


class LawTreeBuilder:
    """
    Build LawTree bottom-up
    """

    def __init__(self):
        self.hrchy2nodes = dict()
        for hrchy in LawHierarchy:
            self.hrchy2nodes[hrchy] = list()

    def add(self, node):
        try:
            children = self._get_children(parent_hrchy=node.hierarchy, flush=True)
        except ValueError as e:
            msg = 'failed to add new node as there are active child nodes at multiple hierarchy'
            raise ValueError(msg) from e
        if children:
            node.children = children
        self.hrchy2nodes[node.hierarchy].append(node)

    def build(self):
        try:
            return self._get_children(parent_hrchy=None, flush=False)
        except ValueError as e:
            msg = 'failed to build LawTree as there are active nodes at multiple hierarchy'
            raise ValueError(msg) from e

    def _get_children(self, parent_hrchy, flush):
        child_hrchy_list = list()
        flag = True if parent_hrchy is None else False
        for hrchy in LawHierarchy:
            if hrchy == parent_hrchy:
                flag = True
            elif flag and self.hrchy2nodes[hrchy]:
                child_hrchy_list.append(hrchy)

        if len(child_hrchy_list) == 0:
            return list()
        elif len(child_hrchy_list) == 1:
            child_hrchy = child_hrchy_list[0]
            children = self.hrchy2nodes[child_hrchy][::-1]
            if flush:
                self.hrchy2nodes[child_hrchy] = list()
            return children
        else:
            msg = 'found multiple child hierarchy under {0} ({1})'.format(
                parent_hrchy.value,
                ','.join(map(lambda x: x.value, child_hrchy_list))
            )
            raise ValueError(msg)


def title_to_hierarchy(text):
    hrchy2pattern = {
        LawHierarchy.PART: r'第[{0}]+編'.format(NUMBER_KANJI),
        LawHierarchy.CHAPTER: r'第[{0}]+章'.format(NUMBER_KANJI),
        LawHierarchy.SECTION: r'第[{0}]+節'.format(NUMBER_KANJI),
        LawHierarchy.SUBSECTION: r'第[{0}]+款'.format(NUMBER_KANJI),
        LawHierarchy.DIVISION: r'第[{0}]+目'.format(NUMBER_KANJI),
        LawHierarchy.ARTICLE: r'第[{0}]+条(の[{0}]+)*'.format(NUMBER_KANJI),
        LawHierarchy.PARAGRAPH: r'[{0}]+|[{1}]+'.format(NUMBER_SUJI, '0-9'),
        LawHierarchy.ITEM: r'[{0}]+'.format(NUMBER_KANJI),
        LawHierarchy.SUBITEM1: r'[{0}]'.format(IROHA),
        LawHierarchy.SUBITEM2: r'（[{0}]+）'.format(NUMBER_SUJI),
        LawHierarchy.SUBITEM3: r'（[{0}]+）'.format(NUMBER_ROMAN)
    }
    for hrchy, pattern in hrchy2pattern.items():
        m = re.fullmatch(pattern, text)
        if m:
            return hrchy
    return None


def line_to_node(text):
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
        return Article(title=maybe_title)
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
    return None


def build_law_tree(text):
    lines = [line for line in text.split('\n') if line.strip() != '']
    law_tree_builder = LawTreeBuilder()

    idx = len(lines) - 1
    while idx >= 0:
        line = lines[idx]
        idx -= 1
        maybe_node = line_to_node(line)
        if maybe_node is None:
            LOGGER.warning(f'failed to process {line} @ {idx + 2}')  # +2 for 1-origin
            continue
        if maybe_node.hierarchy == LawHierarchy.ARTICLE:
            # set paragraph in the line if exists
            chunks = line.strip().split()
            if len(chunks) > 1:
                paragraph = Paragraph(title='第一項', number=1, sentence=' '.join(chunks[1:]))
                law_tree_builder.add(paragraph)

            # set caption in the previous line if exists
            m = re.fullmatch(r'（.+）', lines[idx].strip())
            if m:
                maybe_node.caption = m.group()
                idx -= 1
        law_tree_builder.add(maybe_node)

    return law_tree_builder.build()
