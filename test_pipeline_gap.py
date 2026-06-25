from src.core.config import load_config
from src.services.pipeline_runner import PipelineRunner
from src.services.ingestion_service import IngestionResult
import os
os.environ["STREAM_FILE_SIZE_MB_THRESHOLD"] = "9999"
config, _ = load_config()
runner = PipelineRunner(config)
# Run Memory
m_res = runner.ingestion_service.load()
m_res = IngestionResult(source_path=m_res.source_path, effective_path=m_res.effective_path, dataframe=runner.ingestion_service._load_csv(m_res.effective_path), source_type=m_res.source_type, rows_read=1000000, is_streaming=False)
_, _, m_stats = runner._run_in_memory(m_res)
print(f"Memory Drops: orig={m_stats.original_rows}, final={m_stats.final_rows}, drop={(m_stats.original_rows - m_stats.final_rows)}")
# Run Streaming
s_res = runner.ingestion_service.load()
stream_res = IngestionResult(source_path=s_res.source_path, effective_path=s_res.effective_path, dataframe=None, source_type=s_res.source_type, rows_read=0, is_streaming=True)
_, _, s_stats = runner._run_streaming(stream_res)
print(f"Stream Drops: orig={s_stats.original_rows}, final={s_stats.final_rows}, drop={(s_stats.original_rows - s_stats.final_rows)}")
