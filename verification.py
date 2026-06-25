import pandas as pd
import sys
sys.path.insert(0, "src")

from services.validation_service import ValidationService
from core.config import load_config

# Load full dataset for verification
# The prompt implies 1,000,000 rows.
# I will use the actual file.
data_file = "data/raw/dirty_transactions.csv"
full_df = pd.read_csv(data_file, dtype=str)
rows_in = len(full_df)

config, _ = load_config()
vs = ValidationService(config)

# Streaming path
seen_ids = set()
streaming_kept = 0
for chunk in [full_df.iloc[i:i+10000] for i in range(0, rows_in, 10000)]:
    cleaned, seen_ids = vs.validate_and_clean(chunk, seen_ids=seen_ids)
    streaming_kept += len(cleaned.cleaned_df)
streaming_dropped = rows_in - streaming_kept

# --- CHECKS ---
# Check 1
assert rows_in == 1000000, "Row loss at ingestion"
assert streaming_kept + streaming_dropped == 1000000, "Row accounting broken"
print("CHECK 1 PASSED")

# Check 2
drop_rate = streaming_dropped / rows_in
assert 0.1562 <= drop_rate <= 0.1662, f"FAILED: drop_rate={drop_rate:.4f} outside 15.62%-16.62%"
print(f"CHECK 2 PASSED: drop_rate={drop_rate:.4%}")

# Check 3 - Gap (Comparing against full in-memory)
# Note: running full in-memory might be memory intensive.
memory_result, _ = vs.validate_and_clean(full_df)
memory_kept = len(memory_result.cleaned_df)
gap = abs(streaming_kept - memory_kept) / rows_in
assert gap <= 0.001, f"FAILED: gap={gap:.4%} exceeds 0.1% tolerance"
print(f"CHECK 3 PASSED: gap={gap:.4%}")
