from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import pandas as pd
import json

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.core.config import load_config
from src.services.pipeline_runner import build_runner

def run_mode(label: str, streaming: bool):
    print(f"\n>>> RUNNING MODE: {label} (Streaming: {streaming})")
    os.environ["ENABLE_STREAMING_FOR_CSV"] = "true" if streaming else "false"
    if streaming:
        os.environ["STREAM_FILE_SIZE_MB_THRESHOLD"] = "0" 
    else:
        os.environ["STREAM_FILE_SIZE_MB_THRESHOLD"] = "1000"
    
    os.environ["MAX_REPORT_ROWS"] = "2000000"
        
    config, _ = load_config()
    runner = build_runner(config)
    
    start = time.perf_counter()
    result = runner.run()
    duration = time.perf_counter() - start
    
    # Extract stats from the runner's last run (this is a bit hacky but works for debug)
    # We can inspect the metrics built at the end
    # Instead, let's just parse the last report's summary if possible
    # Or just use the returned result which has rows_loaded and rows_cleaned
    
    print(f"DONE in {duration:.2f}s | Loaded: {result.get('rows_loaded')} | Cleaned: {result.get('rows_cleaned')}")
    
    # Load report to get granular stats
    report_path = Path(result.get('report_path'))
    df_summary = pd.read_excel(report_path, sheet_name="Pipeline Summary")
    stats = df_summary.set_index('Metric')['Value'].to_dict()
    
    print(f"Stats: {json.dumps(stats, indent=2)}")
    
    return stats

if __name__ == "__main__":
    data_file = "data/raw/dirty_transactions.csv"
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found.")
        sys.exit(1)
        
    os.environ["DATA_FILE"] = data_file
    os.environ["DRY_RUN"] = "true"

    stats_mem = run_mode("IN-MEMORY", False)
    stats_stream = run_mode("STREAMING", True)
    
    dr_mem = float(stats_mem['Drop Rate'].strip('%'))
    dr_stream = float(stats_stream['Drop Rate'].strip('%'))
    
    diff = abs(dr_mem - dr_stream)
    print(f"\nDiscrepancy in Drop Rate: {diff:.4f}%")
    
    # Compare row counts
    loaded_match = stats_mem['Rows Loaded'] == stats_stream['Rows Loaded']
    cleaned_match = stats_mem['Rows Cleaned'] == stats_stream['Rows Cleaned']
    
    print(f"Rows Loaded Match: {loaded_match}")
    print(f"Rows Cleaned Match: {cleaned_match}")
    
    if diff <= 0.5:
        print("VERIFIED: Discrepancy is within 0.5% tolerance.")
    else:
        print("FAILED: Discrepancy exceeds 0.5% tolerance.")
        sys.exit(1)
