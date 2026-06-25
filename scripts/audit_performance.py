import asyncio
import time
import os
import sys
import statistics
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from scripts.benchmark import generate_dirty_data
from src.core.config import load_config
from src.services.pipeline_runner import build_runner

async def audit_performance(num_rows: int, iterations: int = 5):
    """
    Rigorously audit performance claims using multiple iterations.
    Measures Mean, Median, Variance, and Throughput.
    """
    print(f"--- PERFORMANCE AUDIT: {num_rows} rows, {iterations} iterations ---")
    
    results = {"memory": [], "streaming": []}
    
    for mode in ["memory", "streaming"]:
        use_stream = (mode == "streaming")
        bench_file = PROJECT_ROOT / "data" / "raw" / f"audit_{mode}_{num_rows}.csv"
        generate_dirty_data(num_rows, bench_file)
        
        # Override env
        os.environ["DATA_FILE"] = str(bench_file)
        os.environ["DRY_RUN"] = "true"
        os.environ["ENABLE_STREAMING_FOR_CSV"] = "true" if use_stream else "false"
        if use_stream:
            os.environ["STREAM_FILE_SIZE_MB_THRESHOLD"] = "0"
            
        for i in range(iterations):
            config, _ = load_config()
            runner = build_runner(config)
            
            start = time.perf_counter()
            await asyncio.to_thread(runner.run)
            end = time.perf_counter()
            
            duration = end - start
            results[mode].append(duration)
            print(f"Iteration {i+1} ({mode}): {duration:.4f}s")

    # Statistical Analysis
    stats_report = {}
    for mode in ["memory", "streaming"]:
        data = results[mode]
        stats_report[mode] = {
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "stdev": statistics.stdev(data) if len(data) > 1 else 0,
            "throughput_mean": num_rows / statistics.mean(data)
        }

    speedup = stats_report["memory"]["mean"] / stats_report["streaming"]["mean"]
    
    print("\n=== AUDIT RESULTS ===")
    print(f"In-Memory Mean:  {stats_report['memory']['mean']:.4f}s (Throughput: {stats_report['memory']['throughput_mean']:.2f} r/s)")
    print(f"Streaming Mean:  {stats_report['streaming']['mean']:.4f}s (Throughput: {stats_report['streaming']['throughput_mean']:.2f} r/s)")
    print(f"Verified Speedup: {speedup:.2f}x")
    print("=====================\n")
    
    return stats_report

if __name__ == "__main__":
    asyncio.run(audit_performance(50000, 3))
