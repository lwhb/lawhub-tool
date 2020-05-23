#!/usr/bin/env python3

"""
クロールしたe-Govの法令データを元にlawhub-xmlを更新する
"""

import glob
import logging
import shutil
from pathlib import Path

import pandas as pd

from lawhub.constants import LAWHUB_DATA, LAWHUB_ROOT

LOGGER = logging.getLogger('copy_xml')


class FileManager:
    source_directory = LAWHUB_DATA / 'egov'
    target_directory = LAWHUB_ROOT / 'lawhub-xml'
    source_pattern = f'{source_directory}/*/*/*.xml'
    target_pattern = f'{target_directory}/*/*.xml'

    def __init__(self):
        self.source_fps = set([Path(fp) for fp in glob.glob(self.source_pattern)])
        LOGGER.info(f'found {len(self.source_fps)} source xml files')
        self.target_fps = set([Path(fp) for fp in glob.glob(self.target_pattern)])
        LOGGER.info(f'found {len(self.target_fps)} target xml files')
        meta_fp = self.source_directory / 'zip.meta'
        meta_df = pd.read_csv(meta_fp, sep='\t', dtype=object)
        self.y2z = dict(zip(meta_df['yid'], meta_df['zid']))
        self.z2y = dict(zip(meta_df['zid'], meta_df['yid']))

    def stot(self, sfp):
        sfp = Path(sfp)
        assert sfp.stem == sfp.parts[-2]
        zid = sfp.parts[-3]
        return self.target_directory / self.z2y[zid] / sfp.parts[-1]

    def ttos(self, tfp):
        tfp = Path(tfp)
        yid = tfp.parts[-2]
        return self.source_directory / self.y2z[yid] / tfp.stem / tfp.parts[-1]

    def copy_source_files(self):
        """
        Force copy all source files to target directory
        """

        count = 0
        for sfp in self.source_fps:
            tfp = self.stot(sfp)
            tfp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(str(sfp), str(tfp))
            LOGGER.debug(f'copied {sfp} to {tfp}')
            count += 1
        LOGGER.info(f'copied total {count} files')

    def remove_target_files(self):
        """
        Remove target files if
        1. source files does not exist
        2. source parent-parent directory exists (=zip file exists)
        """

        count = 0
        for tfp in self.target_fps:
            sfp = self.ttos(tfp)
            if not sfp.exists() and sfp.parent.parent.exists():
                tfp.unlink()
                LOGGER.debug(f'removed {tfp} as {sfp} does not exist')
                count += 1
        LOGGER.info(f'removed total {count} files')


def main():
    file_manager = FileManager()
    file_manager.copy_source_files()
    file_manager.remove_target_files()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main()
