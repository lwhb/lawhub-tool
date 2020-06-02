#!/usr/bin/env python3
import argparse
import logging

import pandas as pd

from lawhub.constants import LAWHUB_DATA

LOGGER = logging.getLogger('report_stat')
STAT_ROOT = LAWHUB_DATA / 'stat'


def read_stat(fp):
    df = pd.read_csv(fp, sep='\t', names=['file', 'process', 'success'])
    return df


def show_stat(df, title, file_col='file', process_col='process', success_col='success'):
    LOGGER.info('{} success: {:.2f} % ({:,}/{:,} for {:,} files)'.format(
        title,
        100 * df[success_col].sum() / df[process_col].sum(),
        df[success_col].sum(),
        df[process_col].sum(),
        len(df),
    ))

    rate_col = 'rate'
    df[rate_col] = df[success_col] / df[process_col]
    df = df[df[process_col] >= 10].sort_values(by=[rate_col, process_col], ascending=[True, False])
    for _, row in df[:3].iterrows():
        LOGGER.debug('{}: {:.2f} % ({}/{})'.format(row[file_col], 100 * row[rate_col], row[success_col], row[process_col]))
    LOGGER.debug('...')
    for _, row in df[-3:].iterrows():
        LOGGER.debug('{}: {:.2f} % ({}/{})'.format(row[file_col], 100 * row[rate_col], row[success_col], row[process_col]))
    LOGGER.debug('')


def main(parse_fp, apply_fp):
    parse_df = read_stat(parse_fp)
    apply_df = read_stat(apply_fp)

    show_stat(parse_df, 'PARSE')
    show_stat(apply_df, 'APPLY')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='.STATファイルから統計情報を出力する')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main(
        STAT_ROOT / 'parse_gian.stat',
        STAT_ROOT / 'apply_gian.stat'
    )
