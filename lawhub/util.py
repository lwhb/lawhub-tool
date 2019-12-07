import pandas as pd


class StatsFactory:
    def __init__(self, columns):
        self.columns = columns
        self.records = []

    def add(self, record):
        self.records.append(record)

    def get(self, index):
        return self.records[index]

    def get_last(self):
        return self.get(index=-1)

    def commit(self, fp):
        df = pd.DataFrame(self.records, columns=self.columns)
        df.to_csv(fp, mode='a', index=False, header=False, sep='\t')
