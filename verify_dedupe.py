import pandas as pd
from src.services.validation_service import ValidationService
from src.core.config import load_config
import pytest

def test_cross_chunk_deduplication():
    # Setup
    config, _ = load_config()
    vs = ValidationService(config)
    
    # Chunk 1: IDs 1, 2
    df1 = pd.DataFrame({"id": ["1", "2"], "name": ["a", "b"]})
    # Chunk 2: IDs 1 (duplicate), 3
    df2 = pd.DataFrame({"id": ["1", "3"], "name": ["a", "c"]})
    
    # Process Chunk 1
    result1, seen_ids = vs.validate_and_clean(df1)
    
    # Process Chunk 2
    result2, seen_ids = vs.validate_and_clean(df2, seen_ids=seen_ids)
    
    print(f"Chunk 1: kept={len(result1.cleaned_df)}")
    print(f"Chunk 2: kept={len(result2.cleaned_df)}")
    
    # Assertions
    # Total rows: 4, IDs: 1, 2, 1, 3. Unique: 1, 2, 3. Kept: 3.
    # Chunk 1: Keeps 2
    # Chunk 2: Drops ID 1. Keeps 1 (ID 3).
    assert len(result1.cleaned_df) == 2
    assert len(result2.cleaned_df) == 1
    print("Deduplication check passed!")

if __name__ == "__main__":
    test_cross_chunk_deduplication()
