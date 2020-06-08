#!/usr/bin/env python3

"""
処理結果を元にlawhubレポジトリにpull requestを作成する
"""

import argparse
import filecmp
import json
import logging
import shutil

from git import Repo
from github import Github

from lawhub.constants import LAWHUB_ROOT, LAWHUB_GITHUB_TOKEN
from pipeline import FileFinder

LOGGER = logging.getLogger('create_pull_request')


def find_closest_tag(repo, tag):
    tags = sorted(list(map(str, repo.tags)))
    for t in reversed(tags):
        if t <= tag:
            return t
    return tags[0]


def create_feature_branch(gian_id, tag=None):
    """
    create feature branch for the given gian and push to remote
    """

    repo = Repo(LAWHUB_ROOT / 'lawhub')

    if repo.active_branch.name != 'master' or repo.is_dirty():
        raise RuntimeError(f'skip processing as {repo.working_dir} is not on clean master')

    if gian_id in repo.branches:
        repo.git.branch('-D', gian_id)
        LOGGER.debug(f'deleted existing branch {gian_id}')

    repo.git.checkout('-b', gian_id)
    LOGGER.debug(f'checked out to a newly created branch {gian_id}')
    repo.git.checkout('-b', 'test', find_closest_tag(repo, '2020-05-11'))

    for jsonl_fp in FileFinder.find_jsonl(gian_id):
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
                LOGGER.info(f'copied {after_fp} to {lawhub_fp}')
            else:
                LOGGER.info(f'skip copying {after_fp} as {before_fp} and {lawhub_fp} is different')
    if repo.is_dirty():
        repo.git.add(update=True)
        repo.git.commit(m=gian_id)
        repo.git.push('--set-upstream', 'origin', gian_id, force=True)
        LOGGER.info(f'feature branch {gian_id} was pushed to remote')
        created = True
    else:
        LOGGER.info('skipped commit because no file is updated')
        created = False

    repo.git.checkout('master')
    LOGGER.debug(f'checked out to master')
    return created


def create_pull_request(gian_id):
    g = Github(LAWHUB_GITHUB_TOKEN)
    repo = g.get_repo("lwhb/lawhub")
    json_fp = FileFinder.find_json(gian_id)
    with open(json_fp, 'r') as f:
        data = json.load(f)
    pr = repo.create_pull(title=data['title'], body=data['reason'], head=gian_id, base="master")
    LOGGER.info(f'created pull request: {pr}')


def main(gian_id):
    created = create_feature_branch(gian_id)
    if created:
        create_pull_request(gian_id)


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
