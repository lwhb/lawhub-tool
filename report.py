#!/usr/bin/env python3
import argparse

import pandas as pd


def read_stat(fp):
    df = pd.read_csv(fp, sep='\t', names=['file', 'process', 'success'])
    return df


def show_stat(df, title, verbose=False, file_col='file', process_col='process', success_col='success'):
    print('{} success: {:.2f} % ({:,}/{:,} for {:,} files)'.format(
        title,
        100 * df[success_col].sum() / df[process_col].sum(),
        df[success_col].sum(),
        df[process_col].sum(),
        len(df),
    ))

    if verbose:
        rate_col = 'rate'
        df[rate_col] = df[success_col] / df[process_col]
        df = df[df[process_col] >= 10].sort_values(by=[rate_col, process_col], ascending=[True, False])
        for _, row in df[:3].iterrows():
            print('{}: {:.2f} % ({}/{})'.format(row[file_col], 100 * row[rate_col], row[success_col], row[process_col]))
        print('...')
        for _, row in df[-3:].iterrows():
            print('{}: {:.2f} % ({}/{})'.format(row[file_col], 100 * row[rate_col], row[success_col], row[process_col]))
        print()


def main(parse_fp, apply_fp, args):
    parse_df = read_stat(parse_fp)
    apply_df = read_stat(apply_fp)
    total_df = pd.merge(parse_df, apply_df, on='file', suffixes=['_p', '_a'])

    show_stat(total_df, 'TOTAL', verbose=args.verbose, process_col='process_p', success_col='success_a')
    show_stat(parse_df, 'PARSE', verbose=args.verbose)
    show_stat(apply_df, 'APPLY', verbose=args.verbose)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='.STATファイルから統計情報を出力する')
    parser.add_argument('-v', '--verbose', action='store_true')
    main('./data/parse_gian.stat', './data/apply_gian.stat', parser.parse_args())
