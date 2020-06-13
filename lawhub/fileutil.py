import glob
import json
from pathlib import Path

import pandas as pd

from lawhub.constants import LAWHUB_DATA


class GianDirectory:
    """
    Provides utility methods to access files stored in gian sub directories
    """

    def __init__(self, gian_id):
        self.gian_id = gian_id
        self.directory = LAWHUB_DATA / 'gian' / gian_id.replace('-', '/')
        self.houan_json_fp = self.directory / 'houan.json'
        self.keika_json_fp = self.directory / 'keika.json'

    def read_houan_json(self):
        return json.load(open(self.houan_json_fp, 'r'))

    def read_keika_json(self):
        return json.load(open(self.keika_json_fp, 'r'))

    def read_xml_metas(self):
        return [json.load(open(fp, 'r')) for fp in self.glob_fps('*.xml.meta')]

    def read_index_meta(self):
        fp = LAWHUB_DATA / 'gian' / 'index.tsv'
        df = pd.read_csv(fp, sep='\t')
        return df[df['gian_id'] == self.gian_id].to_dict(orient='records')[0]

    def glob_fps(self, pattern):
        pattern = str(self.directory / pattern)
        return [Path(fp) for fp in glob.glob(pattern)]
