#!/usr/bin/env python3

"""
処理結果を元にlawhubレポジトリにpull requestを作成する
"""

import argparse
import filecmp
import json
import logging
import shutil

import pandas as pd
from git import Repo
from github import Github

from lawhub.constants import LAWHUB_ROOT, LAWHUB_GITHUB_TOKEN
from lawhub.fileutil import GianDirectory

LOGGER = logging.getLogger('create_pull_request')


def find_closest_tag(repo, tag):
    tags = sorted(list(map(str, repo.tags)))
    for t in reversed(tags):
        if t <= tag:
            return t
    return tags[0]


def init_feature_branch(repo, gian_id):
    # delete branch if exists
    if gian_id in repo.branches:
        repo.git.branch('-D', gian_id)
        LOGGER.debug(f'deleted existing branch {gian_id}')

    # select starting tag
    metas = GianDirectory(gian_id).read_xml_metas()
    if metas:
        raw_tag = metas[0]['tag']  # use first xml.meta to get tag
        tag = find_closest_tag(repo, raw_tag)
        LOGGER.debug(f'selected {tag} as tag, which is the closest to {raw_tag}')
    else:
        tag = repo.tags[-1]  # use latest tag (default)
        LOGGER.debug(f'selected {tag} as default tag, which is the latest')

    repo.git.branch(gian_id, tag)
    LOGGER.info(f'created {gian_id} branch from {tag}')
    return True


def update_feature_branch(repo, gian_id):
    repo.git.checkout(gian_id)

    for jsonl_fp in GianDirectory(gian_id).glob_fps('*.jsonl'):
        LOGGER.debug(f'checking {jsonl_fp.with_suffix(".*")}')
        meta_fp = jsonl_fp.with_suffix('.xml.meta')
        before_fp = jsonl_fp.with_suffix('.before')
        after_fp = jsonl_fp.with_suffix('.after')
        if meta_fp.exists() and before_fp.exists() and after_fp.exists():
            LOGGER.debug(f'found apply result for {jsonl_fp}')
            with open(meta_fp, 'r') as f:
                meta = json.load(f)
            lawhub_fp = meta['fp'].replace('lawhub-xml', 'lawhub').replace('.xml', '.txt')  # convert lawhub-xml file path to lawhub file path ToDo: use FileManager in update_lawhub.py
            if filecmp.cmp(before_fp, lawhub_fp):
                shutil.copy(str(after_fp), str(lawhub_fp))
                LOGGER.debug(f'copied {after_fp} to {lawhub_fp}')
            else:
                LOGGER.debug(f'skip copying {after_fp} as {before_fp} and {lawhub_fp} is different')

    if repo.is_dirty():
        repo.git.add(update=True)
        repo.git.commit(m=gian_id)
        LOGGER.info(f'created commit = {gian_id}')
        updated = True
    else:
        LOGGER.debug(f'skip committing as no file is updated')
        updated = False

    repo.git.checkout('master')
    return updated


def push_feature_branch(repo, gian_id):
    repo.git.push('--set-upstream', 'origin', gian_id, force=True)
    LOGGER.info(f'feature branch {gian_id} was pushed to remote')
    return True


def process_feature_branch(gian_id):
    """
    create gian_id feature branch and push it to remote if updated
    """

    repo = Repo(LAWHUB_ROOT / 'lawhub')
    if repo.active_branch.name != 'master' or repo.is_dirty():
        raise RuntimeError(f'skip processing as {repo.working_dir} is not on clean master')

    initailized = init_feature_branch(repo, gian_id)
    updated = update_feature_branch(repo, gian_id)
    pushed = push_feature_branch(repo, gian_id) if updated else False
    return pushed


def build_pull_request_content(gian_id):
    def build_title():
        gian_name = '{0}第{1}回第{2}号'.format(keika['議案種類'], keika['議案提出回次'], keika['議案番号'])
        return '{0}:{1}'.format(gian_name, houan['title'])

    def build_table():
        records = []
        for key, val in keika.items():
            val = val.replace('\n', '')
            if val and val != '／':
                records.append({'項目': key, '内容': val})
        df = pd.DataFrame(records, columns=['項目', '内容'])
        return df.to_markdown(showindex=False)

    def build_body():
        return '\n'.join([
            '## 理由',
            houan['reason'],
            '',
            '## 経過',
            build_table(),
            '',
            '## リンク',
            '* [本文]({})'.format(meta['honbun']),
            '* [経過]({})'.format(meta['keika'])
        ])

    gian_directory = GianDirectory(gian_id)
    keika = gian_directory.read_keika_json()
    houan = gian_directory.read_houan_json()
    meta = gian_directory.read_index_meta()

    return build_title(), build_body()


def process_pull_request(gian_id):
    github = Github(LAWHUB_GITHUB_TOKEN)
    repo = github.get_repo("lwhb/lawhub")
    title, body = build_pull_request_content(gian_id)

    for pr in repo.get_pulls():
        if pr.head.ref == gian_id:
            LOGGER.debug(f'found pull request for {gian_id}')
            if pr.title != title or pr.body != body:
                pr.edit(title=title, body=body)
                LOGGER.debug(f'updated {gian_id} pull request with new title and body')
            return
    pr = repo.create_pull(title=title, body=body, head=gian_id, base="master")
    LOGGER.info(f'created a new {gian_id} pull request: {pr}')


def main(gian_id):
    pushed = process_feature_branch(gian_id)
    if pushed:
        process_pull_request(gian_id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='議案IDのpull requestを作成する')
    parser.add_argument('-g', '--gian', help='議案ID')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    main(args.gian)
