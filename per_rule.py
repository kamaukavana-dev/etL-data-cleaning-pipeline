import pandas as pd
from src.core.config import load_config
from src.services.validation_service import ValidationService
from src.services.ingestion_service import IngestionService
config, _ = load_config()
val_service = ValidationService(config)
df_mem = pd.read_csv("data/raw/audit_memory_50000.csv")
df_str = pd.read_csv("data/raw/audit_streaming_50000.csv")
# Use normalize
df_mem = IngestionService.normalize_columns(df_mem)
df_str = IngestionService.normalize_columns(df_str)
res_mem, _ = val_service.validate_and_clean(df_mem)
res_str, _ = val_service.validate_and_clean(df_str)
print("MEM: ", res_mem.stats.validation_error_counts)
print("STR: ", res_str.stats.validation_error_counts)
