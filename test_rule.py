import pandas as pd
from src.core.config import load_config
from src.services.validation_service import ValidationService
# Load exactly 50000 
df = pd.read_csv('data/raw/dirty_transactions.csv', nrows=50000)
vs_mem = ValidationService(load_config()[0])
mem_res, _ = vs_mem.validate_and_clean(df.copy())
print("MEM:", mem_res.stats.validation_error_counts)
str_res = {}
dupes = 0
for i in range(0, 50000, 1000):  # VERY SMALL CHUNK TO FORCE DIFFERENT INFERENCE?
    chunk = df.iloc[i:i+1000].copy()
    r, _ = vs_mem.validate_and_clean(chunk)
    for k, v in r.stats.validation_error_counts.items():
        str_res[k] = str_res.get(k, 0) + v
print("STR 1k:", str_res)
