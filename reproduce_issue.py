
import pandas as pd
from src.services.validation_service import ValidationService
from src.core.config import load_config
import pytest

def test_cross_chunk_deduplication():
    # Setup
    config, _ = load_config()
    vs = ValidationService(config)
    
    # Chunk 1
    df1 = pd.DataFrame({"id": ["1", "2"], "name": ["a", "b"]})
    # Chunk 2, with a duplicate (id "1")
    df2 = pd.DataFrame({"id": ["1", "3"], "name": ["a", "c"]})
    
    # Process Chunk 1
    result1, seen_ids = vs.validate_and_clean(df1)
    print(f"Chunk 1: original={result1.stats.original_rows}, final={result1.stats.final_rows}, dupes={result1.stats.duplicates_dropped}")
    
    # Process Chunk 2
    result2, seen_ids = vs.validate_and_clean(df2, seen_ids=seen_ids)
    print(f"Chunk 2: original={result2.stats.original_rows}, final={result2.stats.final_rows}, dupes={result2.stats.duplicates_dropped}")

    # Assertions
    # Chunk 1: 2 rows in, 2 rows out, 0 dupes
    # Chunk 2: 2 rows in, 1 row out (id 1 is duplicate), 1 dupe
    assert result1.stats.duplicates_dropped == 0
    assert result2.stats.duplicates_dropped == 1
    assert len(result2.cleaned_df) == 1

if __name__ == "__main__":
    test_cross_chunk_deduplication()
    print("Test passed!")
