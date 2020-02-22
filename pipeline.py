#!/usr/bin/env python3
import argparse
import glob
import logging
import subprocess
from pathlib import Path

LOGGER = logging.getLogger(__name__)
SCRIPT_ROOT = Path('/Users/musui/lawhub/lawhub-tool')


class FileFinder:
    DATA_ROOT = Path('/Users/musui/lawhub/lawhub-spider/data')

    @staticmethod
    def _directory(gian_id):
        return FileFinder.DATA_ROOT / gian_id.replace('-', '/')

    @staticmethod
    def find_json(gian_id):
        fp = FileFinder._directory(gian_id) / 'houan.json'
        return fp if fp.exists() else None

    @staticmethod
    def find_jsonl(gian_id):
        return [Path(fp) for fp in glob.glob(str(FileFinder._directory(gian_id) / "*.jsonl"))]


class BashTaskTemplate:
    """
    Template to run bash commands and report command log
    """

    def __init__(self):
        self.commands = []
        self.results = []

    def __repr__(self):
        return self.__class__.__name__

    def collect(self):
        pass

    def run(self, collect_command=True, save_log=True):
        if collect_command:
            self.collect()

        LOGGER.info('{} started (#cmd:{})'.format(
            self.__repr__(),
            len(self.commands))
        )
        for command in self.commands:
            LOGGER.debug(command)
            result = subprocess.run(command, capture_output=True, shell=True)
            self.results.append(result)
        LOGGER.info('{} finished (success:{} fail:{})'.format(
            self.__repr__(),
            sum(map(lambda x: x.returncode == 0, self.results)),
            sum(map(lambda x: x.returncode != 0, self.results))
        ))

        if save_log:
            self.log()

    def log(self):
        with open(f'./log/{self.__class__.__name__}.log', 'w') as f:
            for results in (filter(lambda x: x.returncode == 0, self.results),
                            filter(lambda x: x.returncode != 0, self.results)):
                for result in results:
                    f.write(result.args + '\n')
                    f.write(result.stderr.decode('utf-8'))
                f.write('\n')


class ParseGianTask(BashTaskTemplate):
    def __init__(self, gian_id_list):
        super().__init__()
        self.gian_id_list = gian_id_list

    def collect(self):
        stat_fp = SCRIPT_ROOT / 'log/parse_gian.stat'
        if stat_fp.exists():
            stat_fp.unlink()
        for gian_id in self.gian_id_list:
            json_fp = FileFinder.find_json(gian_id)
            if json_fp:
                cmd = f'cd {SCRIPT_ROOT} && ./parse_gian.py -g {json_fp} -s {stat_fp}'
                self.commands.append(cmd)


class GetLawTask(BashTaskTemplate):
    def __init__(self, gian_id_list):
        super().__init__()
        self.gian_id_list = gian_id_list

    def collect(self):
        for gian_id in self.gian_id_list:
            for jsonl_fp in FileFinder.find_jsonl(gian_id):
                law_fp = jsonl_fp.with_suffix('.xml')
                cmd = f'cd {SCRIPT_ROOT} && ./get_law.py -g {jsonl_fp} -l {law_fp}'
                self.commands.append(cmd)


class ApplyGianTask(BashTaskTemplate):
    def __init__(self, gian_id_list):
        super().__init__()
        self.gian_id_list = gian_id_list

    def collect(self):
        stat_fp = SCRIPT_ROOT / 'log/apply_gian.stat'
        if stat_fp.exists():
            stat_fp.unlink()
        for gian_id in self.gian_id_list:
            for jsonl_fp in FileFinder.find_jsonl(gian_id):
                law_fp = jsonl_fp.with_suffix('.xml')
                before_fp = jsonl_fp.with_suffix('.before')
                after_fp = jsonl_fp.with_suffix('.after')
                applied_fp = jsonl_fp.with_suffix('.applied')
                if law_fp.exists():
                    before_cmd = f'cd {SCRIPT_ROOT} && ./apply_gian.py -l {law_fp} -o {before_fp}'
                    after_cmd = f'cd {SCRIPT_ROOT} && ./apply_gian.py -g {jsonl_fp} -a {applied_fp} -l {law_fp} -o {after_fp} -s {stat_fp}'
                    self.commands.append(before_cmd)
                    self.commands.append(after_cmd)


class VizGianTask(BashTaskTemplate):
    def __init__(self, gian_id_list):
        super().__init__()
        self.gian_id_list = gian_id_list

    def collect(self):
        for gian_id in self.gian_id_list:
            json_fp = FileFinder.find_json(gian_id)
            if json_fp:
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


def main(tasks):
    LOGGER.info(f'Start pipeline {tasks}')
    for task in tasks:
        task.run()


if __name__ == '__main__':
    def initialize_task(task_name):
        if task_name == 'parse':
            return ParseGianTask(gian_id_list)
        elif task_name == 'law':
            return GetLawTask(gian_id_list)
        elif task_name == 'apply':
            return ApplyGianTask(gian_id_list)
        elif task_name == 'viz':
            return VizGianTask(gian_id_list)
        elif task_name == 'report':
            return ReportStatTask()
        else:
            return NotImplemented


    parser = argparse.ArgumentParser(description='指定されたTaskを実行する')
    parser.add_argument('-i', '--input', default='./data/pipeline.arg', help='議案ID(e.g. syu-200-1)のリスト')
    parser.add_argument('-t', '--task', nargs='+',
                        default=['parse', 'law', 'apply', 'viz', 'report'],
                        choices=['parse', 'law', 'apply', 'viz', 'report'])
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        datefmt="%m/%d/%Y %I:%M:%S",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    gian_id_list = [line.strip() for line in open(args.input, 'r') if line.strip()]
    tasks = list(map(initialize_task, args.task))
    main(tasks)
