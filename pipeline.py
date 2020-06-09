#!/usr/bin/env python3
import argparse
import logging
import subprocess

import pandas as pd
from tqdm import tqdm

from lawhub.constants import LAWHUB_ROOT, LAWHUB_DATA
from lawhub.fileutil import GianDirectory

LOGGER = logging.getLogger(__name__)
SCRIPT_ROOT = LAWHUB_ROOT / 'lawhub-tool'
STAT_ROOT = LAWHUB_DATA / 'stat'
LOG_ROOT = LAWHUB_DATA / 'log'


class BashTaskTemplate:
    """
    Template to run bash commands and report command log
    """

    def __init__(self, verbose=False):
        self.commands = []
        self.results = []
        self.verbose = verbose

    def collect(self):
        """
        collect commands to execute and set to self.commands
        """
        raise NotImplementedError

    def run(self, collect_command=True, save_log=True):
        if collect_command:
            self.collect()
        LOGGER.info('{} started (#cmd:{})'.format(
            self.__class__.__name__,
            len(self.commands))
        )

        try:
            for command in tqdm(self.commands):
                if self.verbose:
                    command += ' -v'
                LOGGER.debug(command)
                result = subprocess.run(command, capture_output=True, shell=True)
                self.results.append(result)
            LOGGER.info('{} finished (success:{} fail:{})'.format(
                self.__class__.__name__,
                sum(map(lambda x: x.returncode == 0, self.results)),
                sum(map(lambda x: x.returncode != 0, self.results))
            ))
        except KeyboardInterrupt:
            LOGGER.debug('received keyboard interrupt')

        if save_log:
            self.log()

    def log(self):
        log_fp = (LOG_ROOT / self.__class__.__name__).with_suffix('.log')
        with open(log_fp, 'w') as f:
            for results in (filter(lambda x: x.returncode == 0, self.results),
                            filter(lambda x: x.returncode != 0, self.results)):
                for result in results:
                    f.write(result.args + '\n')
                    f.write(result.stderr.decode('utf-8'))
                f.write('\n')
        LOGGER.debug(f'saved log in {log_fp}')


class ParseGianTask(BashTaskTemplate):
    def __init__(self, gian_id_list, verbose=False):
        super().__init__(verbose)
        self.gian_id_list = gian_id_list

    def collect(self):
        stat_fp = STAT_ROOT / 'parse_gian.stat'
        if stat_fp.exists():
            stat_fp.unlink()
        for gian_id in self.gian_id_list:
            json_fp = GianDirectory(gian_id).houan_json_fp
            if json_fp.exists():
                cmd = f'cd {SCRIPT_ROOT} && ./parse_gian.py -g {json_fp} -s {stat_fp}'
                self.commands.append(cmd)


class FetchLawTask(BashTaskTemplate):
    def __init__(self, gian_id_list, verbose=False):
        super().__init__(verbose)
        self.gian_id_list = gian_id_list

    def collect(self):
        for gian_id in self.gian_id_list:
            for jsonl_fp in GianDirectory(gian_id).glob_fps('*.jsonl'):
                law_fp = jsonl_fp.with_suffix('.xml')
                cmd = f'cd {SCRIPT_ROOT} && ./fetch_law.py -g {jsonl_fp} -o {law_fp}'
                self.commands.append(cmd)


class CopyLawTask(BashTaskTemplate):
    def __init__(self, gian_id_list, verbose=False):
        super().__init__(verbose)
        self.gian_id_list = gian_id_list

    def collect(self):
        for gian_id in self.gian_id_list:
            for jsonl_fp in GianDirectory(gian_id).glob_fps('*.jsonl'):
                out_fp = jsonl_fp.with_suffix('.xml')
                cmd = f'cd {SCRIPT_ROOT} && ./copy_law.py -g {jsonl_fp} -o {out_fp}'
                self.commands.append(cmd)


class ApplyGianTask(BashTaskTemplate):
    def __init__(self, gian_id_list, verbose=False):
        super().__init__(verbose)
        self.gian_id_list = gian_id_list

    def collect(self):
        stat_fp = STAT_ROOT / 'apply_gian.stat'
        if stat_fp.exists():
            stat_fp.unlink()
        for gian_id in self.gian_id_list:
            for jsonl_fp in GianDirectory(gian_id).glob_fps('*.jsonl'):
                law_fp = jsonl_fp.with_suffix('.xml')
                before_fp = jsonl_fp.with_suffix('.before')
                after_fp = jsonl_fp.with_suffix('.after')
                applied_fp = jsonl_fp.with_suffix('.applied')
                failed_fp = jsonl_fp.with_suffix('.failed')
                skipped_fp = jsonl_fp.with_suffix('.skipped')

                if law_fp.exists():
                    before_cmd = f'cd {SCRIPT_ROOT} && ./apply_gian.py -l {law_fp} -o {before_fp}'
                    after_cmd = f'cd {SCRIPT_ROOT} && ./apply_gian.py -l {law_fp} -o {after_fp} -g {jsonl_fp} --applied {applied_fp} --failed {failed_fp} --skipped {skipped_fp} -s {stat_fp}'
                    self.commands.append(before_cmd)
                    self.commands.append(after_cmd)


class VizGianTask(BashTaskTemplate):
    def __init__(self, gian_id_list, verbose=False):
        super().__init__(verbose)
        self.gian_id_list = gian_id_list

    def collect(self):
        for gian_id in self.gian_id_list:
            json_fp = GianDirectory(gian_id).houan_json_fp
            if json_fp.exists():
                cmd = 'cd {0} && ./viz_gian.py -g {1} -i {2} -o {3}'.format(
                    SCRIPT_ROOT,
                    json_fp,
                    json_fp.parent / 'houan.html',
                    json_fp.parent / 'applied.html'
                )
                self.commands.append(cmd)


class ReportStatTask(BashTaskTemplate):
    def collect(self):
        cmd = f'cd {SCRIPT_ROOT} && ./report_stat.py'
        self.commands.append(cmd)


class CreatePullRequestTask(BashTaskTemplate):
    def __init__(self, gian_id_list, verbose=False):
        super().__init__(verbose)
        self.gian_id_list = gian_id_list

    def collect(self):
        for gian_id in self.gian_id_list:
            cmd = 'cd {0} && ./create_pull_request.py -g {1}'.format(SCRIPT_ROOT, gian_id)
            self.commands.append(cmd)


def main(tasks):
    LOGGER.info(f'Start pipeline with {len(tasks)} tasks')
    for task in tasks:
        LOGGER.info(f'Start {task.__class__.__name__} task')
        task.run()


if __name__ == '__main__':
    def get_gian_id_list(fp):
        df = pd.read_csv(fp, sep='\t')
        return list(df['gian_id'])


    def initialize_task(task_name, gian_id_list, verbose=False):
        if task_name == 'parse':
            return ParseGianTask(gian_id_list, verbose)
        elif task_name == 'law':
            return CopyLawTask(gian_id_list, verbose)
        elif task_name == 'apply':
            return ApplyGianTask(gian_id_list, verbose)
        elif task_name == 'viz':
            return VizGianTask(gian_id_list, verbose)
        elif task_name == 'report':
            return ReportStatTask()
        elif task_name == 'pr':
            return CreatePullRequestTask(gian_id_list, verbose)
        else:
            return NotImplementedError


    parser = argparse.ArgumentParser(description='指定されたTaskを実行する')
    parser.add_argument('-i', '--input', default=LAWHUB_DATA / 'gian' / 'index.tsv', help='議案ID(e.g. syu-200-1)のリスト')
    parser.add_argument('-t', '--task', nargs='+',
                        default=['parse', 'law', 'apply', 'viz', 'report', 'pr'],
                        choices=['parse', 'law', 'apply', 'viz', 'report', 'pr'])
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    gian_id_list = get_gian_id_list(args.input)
    tasks = list(map(lambda task: initialize_task(task, gian_id_list, args.verbose), args.task))
    main(tasks)
