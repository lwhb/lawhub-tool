import glob

pattern = '/Users/musui/lawhub/lawhub-spider/data/*/*/*/houan.json'
with open('./data/pipeline.arg', 'w') as f:
    for fp in glob.glob(pattern):
        gian_id = '-'.join(fp.split('/')[-4:-1])
        f.write(gian_id + '\n')
