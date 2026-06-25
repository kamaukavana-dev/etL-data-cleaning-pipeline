import pandas as pd
import sys
sys.path.insert(0, "src")

from services.validation_service import ValidationService
from core.config import load_config

# Load full dataset for verification
data_file = "data/raw/dirty_transactions.csv"
full_df = pd.read_csv(data_file, dtype=str)
rows_in = len(full_df)

config, _ = load_config()
vs = ValidationService(config)

# --- IN-MEMORY PATH ---
memory_result, _ = vs.validate_and_clean(full_df.copy())
memory_stats = memory_result.stats
memory_dropped = memory_stats.original_rows - memory_stats.final_rows

# --- STREAMING PATH ---
seen_ids = set()
streaming_kept = 0
agg_stats = {
    "dedupe": 0,
    "email": 0,
    "phone": 0,
    "salary": 0,
    "date": 0
}

# Process in chunks of 100k to match streaming
chunk_size = 100000
for i in range(0, rows_in, chunk_size):
    chunk = full_df.iloc[i:i+chunk_size].copy()
    cleaned, seen_ids = vs.validate_and_clean(chunk, seen_ids=seen_ids)
    
    streaming_kept += len(cleaned.cleaned_df)
    
    # Extract stats
    s = cleaned.stats
    agg_stats["dedupe"] += s.duplicates_dropped
    agg_stats["email"] += s.invalid_emails_dropped
    agg_stats["phone"] += s.invalid_phones_dropped
    agg_stats["salary"] += s.invalid_numbers_dropped
    agg_stats["date"] += s.invalid_dates_dropped

streaming_dropped = rows_in - streaming_kept

print(f"IN-MEMORY  total_dropped={memory_dropped}")
print(f"  Dedupe: {memory_stats.duplicates_dropped}")
print(f"  Email:  {memory_stats.invalid_emails_dropped}")
print(f"  Phone:  {memory_stats.invalid_phones_dropped}")
print(f"  Salary: {memory_stats.invalid_numbers_dropped}")
print(f"  Date:   {memory_stats.invalid_dates_dropped}")

print(f"\nSTREAMING total_dropped={streaming_dropped}")
print(f"  Dedupe: {agg_stats['dedupe']}")
print(f"  Email:  {agg_stats['email']}")
print(f"  Phone:  {agg_stats['phone']}")
print(f"  Salary: {agg_stats['salary']}")
print(f"  Date:   {agg_stats['date']}")

gap_abs = abs(streaming_dropped - memory_dropped)
print(f"\nGAP: {gap_abs} rows")
