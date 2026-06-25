import pandas as pd
import sys
import numpy as np
sys.path.insert(0, "src")

from services.validation_service import ValidationService
from core.config import load_config

# Fix script to use correct config loading
config, _ = load_config()
vs = ValidationService(config)

sample = pd.read_csv("data/raw/dirty_transactions.csv", nrows=500000, dtype=str)

# --- IN-MEMORY PATH ---
memory_result, _ = vs.validate_and_clean(sample.copy())
memory_kept = len(memory_result.cleaned_df)
memory_dropped = 500000 - memory_kept

# --- STREAMING PATH ---
seen_ids = set()
streaming_kept = 0
for i in range(50):
    chunk = sample.iloc[i*10000:(i+1)*10000].copy()
    cleaned, seen_ids = vs.validate_and_clean(chunk, seen_ids=seen_ids)
    streaming_kept += len(cleaned.cleaned_df)
streaming_dropped = 500000 - streaming_kept

print(f"IN-MEMORY  kept={memory_kept}  dropped={memory_dropped}")
print(f"STREAMING  kept={streaming_kept}  dropped={streaming_dropped}")
print(f"GAP        extra_surviving={streaming_kept - memory_kept}")
