import pandas as pd


class StatsFactory:
    def __init__(self, columns):
        self.columns = columns
        self.records = []

    def add(self, record):
        self.records.append(record)

    def commit(self, fp):
        df = pd.DataFrame(self.records, columns=self.columns)
        df.to_csv(fp, mode='a', index=False, header=False, sep='\t')
