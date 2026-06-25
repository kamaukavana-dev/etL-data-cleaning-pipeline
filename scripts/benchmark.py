from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.core.config import load_config
from src.services.pipeline_runner import build_runner

def generate_dirty_data(num_rows: int, file_path: Path) -> None:
    """Generates a large dirty CSV for benchmarking."""
    print(f"Generating {num_rows} rows of dirty data at {file_path}...")
    
    # Base data
    data = {
        "id": range(1, num_rows + 1),
        "name": [f"User_{i}" for i in range(num_rows)],
        "email": [f"user{i}@example.com" if i % 10 != 0 else f"bad_email_{i}" for i in range(num_rows)],
        "phone": [f"+254700000{i % 1000:03d}" if i % 15 != 0 else f"invalid_{i}" for i in range(num_rows)],
        "salary": [float(i * 10) if i % 20 != 0 else -500.0 for i in range(num_rows)],
        "date_joined": [pd.Timestamp("2023-01-01") + pd.Timedelta(days=i % 365) if i % 25 != 0 else "not-a-date" for i in range(num_rows)],
        "department": (["IT", "Sales", "HR", "Finance", "Legal"] * (num_rows // 5 + 1))[:num_rows],
        "notes": ["N/A"] * num_rows
    }
    
    df = pd.DataFrame(data)
    
    # Force some nulls using numpy for speed
    mask_email = np.random.choice([True, False], size=num_rows, p=[0.05, 0.95])
    df.loc[mask_email, "email"] = np.nan
    
    mask_phone = np.random.choice([True, False], size=num_rows, p=[0.05, 0.95])
    df.loc[mask_phone, "phone"] = None
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False)
    print(f"Benchmark file created: {file_path} ({file_path.stat().st_size / 1024 / 1024:.2f} MB)")

def run_benchmark(num_rows: int, use_streaming: bool = False):
    bench_file = PROJECT_ROOT / "data" / "raw" / f"bench_{'stream' if use_streaming else 'memory'}_{num_rows}.csv"
    generate_dirty_data(num_rows, bench_file)
    
    # Configure environment for benchmark
    os.environ["DATA_FILE"] = str(bench_file)
    os.environ["DRY_RUN"] = "true"
    os.environ["ENABLE_STREAMING_FOR_CSV"] = "true" if use_streaming else "false"
    if use_streaming:
        os.environ["STREAM_FILE_SIZE_MB_THRESHOLD"] = "0" # Force streaming
    
    config, _ = load_config()
    runner = build_runner(config)
    
    print(f"\nStarting benchmark ({'STREAMING' if use_streaming else 'IN-MEMORY'}) on {num_rows} rows...")
    start_time = time.perf_counter()
    
    result = runner.run()
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    rows_per_sec = num_rows / total_time
    
    print("\n" + "="*50)
    print(f" BENCHMARK RESULTS ({'STREAMING' if use_streaming else 'IN-MEMORY'})")
    print("="*50)
    print(f"Total Rows:      {num_rows}")
    print(f"Processed Rows:  {result.get('rows_loaded', 0)}")
    print(f"Cleaned Rows:    {result.get('rows_cleaned', 0)}")
    print(f"Total Time:      {total_time:.2f} seconds")
    print(f"Throughput:      {rows_per_sec:.2f} rows/second")
    print(f"Report Path:     {result.get('report_path')}")
    print("="*50 + "\n")
    
    return total_time

if __name__ == "__main__":
    rows = 100000 # Default 100k rows
    if len(sys.argv) > 1:
        rows = int(sys.argv[1])
        
    t_mem = run_benchmark(rows, use_streaming=False)
    t_stream = run_benchmark(rows, use_streaming=True)
    
    print(f"Speedup/Diff: {t_mem/t_stream:.2f}x")
