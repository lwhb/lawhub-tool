from logging import getLogger

from lawhub.kanzize import int2kanji

LOGGER = getLogger(__name__)
INDENT = ' ' * 4


def parse(node):
    if node.tag == 'Part':
        return Part(node)
    elif node.tag == 'Chapter':
        return Chapter(node)
    elif node.tag == 'Section':
        return Section(node)
    elif node.tag == 'Subsection':
        return Subsection(node)
    elif node.tag == 'Division':
        return Division(node)
    elif node.tag == 'Article':
        return Article(node)
    elif node.tag == 'Paragraph':
        return Paragraph(node)
    elif node.tag == 'Item':
        return Item(node)
    elif node.tag == 'Subitem1':
        return Subitem1(node)
    elif node.tag == 'Subitem2':
        return Subitem2(node)
    elif node.tag == 'TableStruct':
        return PlaceHolder('<表略>')
    else:
        raise NotImplementedError(node.tag)


class BaseLawClass:
    def __init__(self):
        self.children = []

    def get_title(self):
        return ''


class BaseSectionClass(BaseLawClass):
    def __init__(self, node):
        self.title = node[0].text
        self.children = [parse(child) for child in node[1:]]

    def __str__(self):
        return '\n'.join([self.title] + list(map(lambda x: x.__str__(), self.children)) + [''])

    def get_title(self):
        return self.title


class BaseItemClass(BaseLawClass):
    def __init__(self, node):
        self.title = node[0].text
        self.sentence = INDENT.join(map(lambda n: n.text, node[1].findall('.//Sentence')))
        self.children = [parse(child) for child in node[2:]]

    def __str__(self):
        return '\n'.join([f'{self.title}　{self.sentence}'] + list(map(lambda x: x.__str__(), self.children)))

    def get_title(self):
        return ''


class Part(BaseSectionClass):
    def __init__(self, node):
        assert node.tag == 'Part'
        assert node[0].tag == 'PartTitle'
        super().__init__(node)


class Chapter(BaseSectionClass):
    def __init__(self, node):
        assert node.tag == 'Chapter'
        assert node[0].tag == 'ChapterTitle'
        super().__init__(node)


class Section(BaseSectionClass):
    def __init__(self, node):
        assert node.tag == 'Section'
        assert node[0].tag == 'SectionTitle'
        super().__init__(node)


class Subsection(BaseSectionClass):
    def __init__(self, node):
        assert node.tag == 'Subsection'
        assert node[0].tag == 'SubsectionTitle'
        super().__init__(node)


class Division(BaseSectionClass):
    def __init__(self, node):
        assert node.tag == 'Division'
        assert node[0].tag == 'DivisionTitle'
        super().__init__(node)


class Article(BaseLawClass):
    def __init__(self, node):
        assert node.tag == 'Article'
        if node[0].tag == 'ArticleCaption' and node[1].tag == 'ArticleTitle':
            self.caption = node[0].text
            self.title = node[1].text
            self.children = [parse(child) for child in node[2:]]
        elif node[0].tag == 'ArticleTitle':
            self.caption = None
            self.title = node[0].text
            self.children = [parse(child) for child in node[1:]]
        else:
            assert False

    def __str__(self):
        if self.caption:
            return '\n'.join([self.caption, self.title] + list(map(lambda x: x.__str__(), self.children)) + [''])
        else:
            return '\n'.join([self.title] + list(map(lambda x: x.__str__(), self.children)) + [''])

    def get_title(self):
        return self.title


class Paragraph(BaseLawClass):
    def __init__(self, node):
        assert node.tag == 'Paragraph'
        assert node[0].tag == 'ParagraphNum'
        assert node[1].tag == 'ParagraphSentence'
        self.num = int(node[0].text) if node[0].text else None
        self.sentence = node[1][0].text
        self.children = [parse(child) for child in node[2:]]

    def __str__(self):
        if self.num:
            return '\n'.join([f'{self.num}　{self.sentence}'] + list(map(lambda x: x.__str__(), self.children)))
        else:
            return '\n'.join([f'{self.sentence}'] + list(map(lambda x: x.__str__(), self.children)))

    def get_title(self):
        return '第{}項'.format(int2kanji(self.num) if self.num else '一')


class Item(BaseItemClass):
    def __init__(self, node):
        assert node.tag == 'Item'
        assert node[0].tag == 'ItemTitle'
        assert node[1].tag == 'ItemSentence'
        super().__init__(node)

    def __str__(self):
        return INDENT + super().__str__()

    def get_title(self):
        return '第{}号'.format(self.title if self.title else '一')


class Subitem1(BaseItemClass):
    def __init__(self, node):
        assert node.tag == 'Subitem1'
        assert node[0].tag == 'Subitem1Title'
        assert node[1].tag == 'Subitem1Sentence'
        super().__init__(node)

    def __str__(self):
        return INDENT * 2 + super().__str__()


class Subitem2(BaseItemClass):
    def __init__(self, node):
        assert node.tag == 'Subitem2'
        assert node[0].tag == 'Subitem2Title'
        assert node[1].tag == 'Subitem2Sentence'
        super().__init__(node)

    def __str__(self):
        return INDENT * 3 + super().__str__()


class PlaceHolder(BaseLawClass):
    def __init__(self, string):
        self.string = string
        super().__init__()

    def __str__(self):
        return self.string
