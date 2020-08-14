import vk_api
import configparser
import argparse
from utils import two_factor_handler
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool
from parse_user import parse

keys = []
with open("keys") as file:
    for key in file:
        keys.append(key.strip())

print(keys)

users = [f"id{600000000 + x}" for x in range(1000000)]
ids = []
i = 0
while i + 753 < len(users):
    ids.append(','.join(users[i:i+750]))
    i += 750

# ids = []
# with open("/home/viliar/Documents/datasets/vk/real.txt") as file:
#     for line in file:
#         ids.append(line.strip())

rows = []

i = 0

size = 3

with Pool(size) as pool:
    for i in tqdm(range(0, len(ids) - size, size)):
        args = [(keys[k], ids[i+k]) for k in range(size)]
        results = pool.map(parse, args)

        for res in results:
            for row in res:
                rows.append(row)

df = pd.DataFrame(rows)

df.to_csv("/home/viliar/Documents/datasets/vk/test.csv", index=False)
