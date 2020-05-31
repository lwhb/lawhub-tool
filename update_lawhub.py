#!/usr/bin/env python3

"""
lawhub-xmlを元にlawhubを更新する
"""

import glob
import logging
from pathlib import Path

from tqdm import tqdm

from lawhub.constants import LAWHUB_ROOT
from lawhub.law import parse_xml_fp, save_law_tree, extract_law_meta

LOGGER = logging.getLogger('update_lawhub')


class FileManager:
    source_directory = LAWHUB_ROOT / 'lawhub-xml'
    target_directory = LAWHUB_ROOT / 'lawhub'
    source_pattern = f'{source_directory}/*/*.xml'
    target_pattern = f'{target_directory}/*/*.txt'

    def __init__(self):
        self.source_fps = set([Path(fp) for fp in glob.glob(self.source_pattern)])
        LOGGER.info(f'found {len(self.source_fps)} source xml files under {self.source_directory}')
        self.target_fps = set([Path(fp) for fp in glob.glob(self.target_pattern)])
        LOGGER.info(f'found {len(self.target_fps)} target xml files under {self.target_directory}')

    def stot(self, sfp):
        """
        build target path from source path
        """

        return self.target_directory / sfp.relative_to(self.source_directory).with_suffix('.txt')

    def remove_target_files(self):
        """
        remove all target files
        """

        LOGGER.info(f'start removing target files')
        count = 0
        for tfp in tqdm(list(self.target_fps)):
            tfp.unlink()
            self.target_fps.remove(tfp)
            count += 1
        LOGGER.info(f'removed total {count} target files, now total {len(self.target_fps)} target files exist')

    def copy_source_files(self):
        """
        Copy source files to target directory
        """

        LOGGER.info(f'start copying source files')
        count = 0
        for sfp in tqdm(sorted(self.source_fps)):
            try:
                meta = extract_law_meta(sfp)
                nodes = parse_xml_fp(sfp)
                tfp = self.stot(sfp)
                tfp.parent.mkdir(parents=True, exist_ok=True)
                save_law_tree(meta['LawTitle'], nodes, tfp)
            except Exception as e:
                LOGGER.error(f'failed to copy {sfp}: {e}')
                continue
            self.target_fps.add(tfp)
            LOGGER.debug(f'copied {sfp} to {tfp}')
            count += 1
        LOGGER.info(f'copied total {count} source files, now total {len(self.target_fps)} target files exist')


def main():
    file_manager = FileManager()
    file_manager.remove_target_files()
    file_manager.copy_source_files()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main()
