#!/usr/bin/env python3

import argparse
import glob
import logging
import shutil
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from lawhub.constants import LAWHUB_DATA, LAWHUB_ROOT
from lawhub.law import extract_law_meta

LOGGER = logging.getLogger('update_lawhub_xml')


class FileManager:
    source_directory = LAWHUB_DATA / 'egov'
    target_directory = LAWHUB_ROOT / 'lawhub-xml'
    zip_fp = source_directory / 'zip.meta'
    index_fp = target_directory / 'index.tsv'
    source_pattern = f'{source_directory}/*/*/*.xml'  # {zip_id}/{egov_id}/{egov_id}.xml
    target_pattern = f'{target_directory}/*/*.xml'  # {year}/{law_num}.xml

    def __init__(self, disable_tqdm=False):
        self.disable_tqdm = disable_tqdm
        self.source_fps = set([Path(fp) for fp in glob.glob(self.source_pattern)])
        LOGGER.info(f'found {len(self.source_fps)} source xml files under {self.source_directory}')
        self.target_fps = set([Path(fp) for fp in glob.glob(self.target_pattern)])
        LOGGER.info(f'found {len(self.target_fps)} target xml files under {self.target_directory}')
        df = pd.read_csv(self.zip_fp, sep='\t', dtype=object)
        self.z2y = dict(zip(df['zid'], df['yid']))

    def stot(self, sfp, law_num):
        """
        build target path from source path
        Note that the same target path can be built from different source path
        """

        zid = sfp.parts[-3]
        assert sfp.parts[-2] == sfp.stem
        return (self.target_directory / self.z2y[zid] / law_num).with_suffix('.xml')

    def remove_target_files(self):
        """
        remove all target files
        """

        LOGGER.info(f'start removing target files')
        count = 0
        for tfp in tqdm(list(self.target_fps), disable=self.disable_tqdm):
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
        for sfp in tqdm(sorted(self.source_fps), disable=self.disable_tqdm):
            try:
                meta = extract_law_meta(sfp)
                tfp = self.stot(sfp, meta['LawNum'])
                tfp.parent.mkdir(parents=True, exist_ok=True)
                if tfp.exists():
                    LOGGER.warning(f'overwriting {tfp}')
                shutil.copy(str(sfp), str(tfp))
            except Exception as e:
                LOGGER.error(f'failed to copy {sfp}: {e}')
                continue
            self.target_fps.add(tfp)
            LOGGER.debug(f'copied {sfp} to {tfp}')
            count += 1
        LOGGER.info(f'copied total {count} source files, now total {len(self.target_fps)} target files exist')

    def create_index_file(self):
        """
        Create index.tsv, which stores xml meta data in TSV format
        """

        LOGGER.info(f'start creating index file')
        records = []
        for tfp in tqdm(self.target_fps, disable=self.disable_tqdm):
            record = {'fp': Path(tfp).relative_to(self.target_directory)}
            record.update(extract_law_meta(tfp))
            records.append(record)
        df = pd.DataFrame(records, columns=['fp', 'LawNum', 'LawTitle', 'LawType', 'Era', 'Year', 'Num'])
        df = df.sort_values(by=['Era', 'Year', 'Num', 'LawType'])
        df.to_csv(self.index_fp, index=False, sep='\t')
        LOGGER.info(f'created index file with {len(self.target_fps)} files :{self.index_fp}')


def main(disable_tqdm):
    file_manager = FileManager(disable_tqdm)
    file_manager.remove_target_files()
    file_manager.copy_source_files()
    file_manager.create_index_file()


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='クロールしたe-Govの法令データを元にlawhub-xmlを更新する')
    argparser.add_argument('-v', '--verbose', action='store_true')
    argparser.add_argument('--nobar', dest='disable_tqdm', action='store_true', help='プログレスバーを表示しない')
    args = argparser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main(args.disable_tqdm)
