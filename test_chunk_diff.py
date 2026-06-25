import pandas as pd
from pathlib import Path
from src.core.config import AppConfig
from src.services.ingestion_service import IngestionService
config = AppConfig()
service = IngestionService(config)
path = Path("data/raw/dirty_transactions.csv") # Or we can try xlsx, which converts to .csv
df_in_mem = pd.read_csv(path, low_memory=False, dtype=str) # we can verify exact loads
in_mem_result = service.load(path)
chunk_iter = service.iter_csv_chunks(path)
chunks = list(chunk_iter)
df_stream = pd.concat(chunks, ignore_index=True)
print("In-mem shape:", in_mem_result.dataframe.shape)
print("Stream shape:", df_stream.shape)
# Compare values
diff = in_mem_result.dataframe.compare(df_stream)
print("Differences:")
print(diff.head())
print("Total diff cells:", diff.size)
