import pandas as pd
from src.core.config import load_config
from src.services.validation_service import ValidationService
from src.services.ingestion_service import IngestionService
import time
config, _ = load_config()
print("Loading XLSX directly via ingestion...")
ingestion = IngestionService(config)
# Temporarily force it not to stream to get in-memory mode 
class FakeConfig:
    def __getattr__(self, name):
        if name == 'enable_streaming_for_csv': return False
        return getattr(config, name)
config_mem = FakeConfig()
ingestion_mem = IngestionService(config_mem)
res_ingest = ingestion_mem.load()
vs_mem = ValidationService(config_mem)
res_mem, _ = vs_mem.validate_and_clean(res_ingest.dataframe)
mem_drop = len(res_ingest.dataframe) - len(res_mem.cleaned_df)
print(f"XLSX In-memory drops: {mem_drop} ({mem_drop / len(res_ingest.dataframe):.2%})")
