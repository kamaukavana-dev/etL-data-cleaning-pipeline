import pandas as pd
from src.services.validation_service import ValidationService
from src.services.pipeline_runner import PipelineRunner
from src.core.config import load_config
from src.services.ingestion_service import IngestionService

# Set up config and services
config, _ = load_config()
vs = ValidationService(config)

# Helper to run in-memory on sample
def run_in_memory_validation(df):
    result, _ = vs.validate_and_clean(df)
    return result

# Load sample
sample = pd.read_csv("data/raw/dirty_transactions.csv", nrows=50000)

# In-memory path
result_memory = run_in_memory_validation(sample.copy())
stats_mem = result_memory.stats
print(f"In-memory dropped: {stats_mem.dropped_rows}")
print(f"In-memory breakdown: {stats_mem.validation_error_counts}, Duplicates: {stats_mem.duplicates_dropped}")

# Streaming path — simulate 5 chunks of 10,000
seen_ids = set()
aggregated_rows_in = 0
aggregated_rows_kept = 0
agg_error_counts = {}
total_dupes = 0

for i in range(5):
    chunk = sample.iloc[i*10000:(i+1)*10000].copy()
    cleaned, seen_ids = vs.validate_and_clean(chunk, seen_ids=seen_ids)
    
    # Aggregation logic
    aggregated_rows_in += len(chunk)
    aggregated_rows_kept += len(cleaned.cleaned_df)
    total_dupes += cleaned.stats.duplicates_dropped
    
    for k, v in cleaned.stats.validation_error_counts.items():
        agg_error_counts[k] = agg_error_counts.get(k, 0) + v

print(f"Streaming dropped: {aggregated_rows_in - aggregated_rows_kept}")
print(f"Streaming breakdown: {agg_error_counts}, Duplicates: {total_dupes}")
