import re
from logging import getLogger

from lawhub.action import line_to_action_nodes
from lawhub.law import line_to_law_node, LawTreeBuilder, LawHierarchy

LOGGER = getLogger('parser')


class GianParser:
    def __init__(self):
        self.process_count = 0
        self.success_count = 0

    def parse(self, lines):
        """
        Convert lines to LawNodes and ActionNodes.

        Lines that are not converted will be returned as String
        ToDo: split to sub functions and remove duplicated try-except
        """

        lines = [line for line in lines if line]  # ignore empty lines, この際metaのlineがずれるので、なくす？
        lines_and_nodes = []
        builder = LawTreeBuilder()

        idx = len(lines) - 1
        idx_flushed = idx + 1
        while idx >= 0:
            self.process_count += 1
            line = lines[idx]
            maybe_law_node = line_to_law_node(line)
            if maybe_law_node:
                law_node = maybe_law_node
                if law_node.hierarchy == LawHierarchy.ARTICLE:
                    # ToDo: Improve LawTreeBuilder to natively handle ArticleCaption in the previous line
                    match = re.fullmatch(r'（.+）', lines[idx - 1].strip())
                    if match:
                        law_node.caption = match.group()
                        self.process_count += 1
                        idx -= 1
                try:
                    builder.add(law_node)
                except ValueError as e:
                    LOGGER.debug(f'failed to add LawNodes at {idx} (line={line})', e)
                    LOGGER.debug(f'flush {idx_flushed - idx} lines')
                    lines_and_nodes += reversed(lines[idx:idx_flushed])
                    idx_flushed = idx
            else:
                try:
                    lines_and_nodes += reversed(builder.build())
                except ValueError as e:
                    LOGGER.debug('failed to build LawNodes at {idx} (line={line})', e)
                    LOGGER.debug(f'flush {idx_flushed - (idx + 1)} lines')
                    lines_and_nodes += reversed(lines[idx + 1:idx_flushed])
                else:
                    self.success_count += idx_flushed - (idx + 1)
                    idx_flushed = idx + 1
                builder = LawTreeBuilder()

                action_nodes, pc, sc = line_to_action_nodes(line, meta={'line': idx})
                lines_and_nodes += reversed(action_nodes)
                if pc == sc:
                    self.success_count += 1
                else:
                    LOGGER.debug(f'failed to parse {pc - sc}/{pc} ActionNodes at {idx} (line={line})')
                    lines_and_nodes.append(line)
                idx_flushed = idx
            idx -= 1
        try:
            lines_and_nodes += reversed(builder.build())
        except ValueError as e:
            LOGGER.debug('failed to build LawNodes at {idx} (line={line})', e)
            LOGGER.debug(f'flush {idx_flushed - (idx)} lines')
            lines_and_nodes += reversed(lines[idx:idx_flushed])
        return lines_and_nodes[::-1]
