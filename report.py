#!/usr/bin/env python3

import pandas as pd


def read_stat(fp):
    df = pd.read_csv(fp, sep='\t', names=['jsonl', 'process', 'success'])
    df = df[df['process'] > 0]
    df['rate'] = df['success'] / df['process']
    return df


def show_stat(df, title):
    print('{} success: {:.2f} % ({:,}/{:,} for {:,} files)'.format(
        title,
        100 * df['success'].sum() / df['process'].sum(),
        df['success'].sum(),
        df['process'].sum(),
        len(df),
    ))

    df['rate'] = df['success'] / df['process']
    df = df[df['process'] >= 10].sort_values(by=['rate', 'process'], ascending=[True, False])
    for _, row in df[:3].iterrows():
        print('{}: {:.2f} % ({}/{})'.format(row['jsonl'], 100 * row['rate'], row['success'], row['process']))
    print('...')
    for _, row in df[-3:].iterrows():
        print('{}: {:.2f} % ({}/{})'.format(row['jsonl'], 100 * row['rate'], row['success'], row['process']))
    print()


def main(p_fp, a_fp):
    p_df = read_stat(p_fp)
    a_df = read_stat(a_fp)
    pa_df = pd.merge(p_df, a_df, on='jsonl', suffixes=['_p', '_a']) \
        .rename(columns={'process_p': 'process', 'success_a': 'success'})

    show_stat(pa_df, 'TOTAL')
    show_stat(p_df, 'PARSE')
    show_stat(a_df, 'APPLY')


if __name__ == '__main__':
    main('./data/parse_gian.stat', './data/apply_gian.stat')
