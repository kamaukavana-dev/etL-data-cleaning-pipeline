from __future__ import annotations

import logging
import time
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Tuple

import pandas as pd

from src.core.config import AppConfig, read_env_value
from src.core.constants import SUPPORTED_INPUT_SUFFIXES
from src.core.exceptions import IngestionError

LOGGER = logging.getLogger("etl.ingestion")


@dataclass(frozen=True)
class IngestionResult:
    source_path: Path
    effective_path: Path
    dataframe: pd.DataFrame | None
    source_type: str
    rows_read: int
    is_streaming: bool
    conversion_time_ms: float | None = None
    sheet_mode: str | None = None


class IngestionService:
    COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
        "id": ("id", "ID", "transaction_id", "transactionid"),
        "name": ("name", "Name", "customer_name", "customername"),
        "email": ("email", "Email"),
        "phone": ("phone", "Phone"),
        "salary": ("salary", "Salary", "total_amount", "totalamount"),
        "date_joined": ("date_joined", "Date", "JoinDate", "JoiningDate", "order_date", "orderdate"),
        "department": ("department", "Dept", "Division", "category"),
        "notes": ("notes", "Remarks", "Comments", "status"),
    }

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def get_ingestion_plan(self, input_path: Path | None = None) -> Tuple[Path, bool, float | None]:
        """
        Determines the effective path (CSV) and whether conversion is needed.
        Returns (effective_path, was_converted, conversion_time_ms)
        """
        path = input_path or self.config.data_file
        path = path.resolve(strict=False)
        suffix = path.suffix.lower()

        if suffix == ".csv":
            return path, False, None

        if suffix in {".xlsx", ".xls"}:
            csv_path = path.with_suffix(".csv")
            if csv_path.exists():
                LOGGER.info(f"Existing CSV cache found: {csv_path}")
                return csv_path, False, None
            
            # Conversion triggered
            start_conv = time.perf_counter()
            self._convert_xlsx_to_csv(path, csv_path)
            elapsed_ms = (time.perf_counter() - start_conv) * 1000
            LOGGER.info(f"XLSX to CSV conversion completed in {elapsed_ms:.2f}ms")
            return csv_path, True, elapsed_ms

        raise IngestionError(
            "Unsupported input file type.",
            error_code="INGESTION_UNSUPPORTED_FILE_TYPE",
            context={"path": str(path), "suffix": suffix, "supported": sorted(SUPPORTED_INPUT_SUFFIXES)},
        )

    def load(self, input_path: Path | None = None) -> IngestionResult:
        original_path = (input_path or self.config.data_file).resolve(strict=False)
        effective_path, converted, conv_time = self.get_ingestion_plan(original_path)
        
        file_size_mb = effective_path.stat().st_size / (1024 * 1024)
        is_streaming = self._should_stream(effective_path, file_size_mb)

        LOGGER.info(
            "Ingestion start.",
            extra={
                "original_format": original_path.suffix.lower(),
                "file_size_mb": round(file_size_mb, 2),
                "mode": "streaming" if is_streaming else "in_memory",
                "converted": converted,
                "conversion_time_ms": conv_time
            }
        )

        if is_streaming:
            # We don't load the dataframe for streaming mode
            return IngestionResult(
                source_path=original_path,
                effective_path=effective_path,
                dataframe=None,
                source_type="csv",
                rows_read=0, # Unknown until streamed
                is_streaming=True,
                conversion_time_ms=conv_time
            )

        df = self._load_csv(effective_path)
        return IngestionResult(
            source_path=original_path,
            effective_path=effective_path,
            dataframe=df,
            source_type="csv",
            rows_read=len(df),
            is_streaming=False,
            conversion_time_ms=conv_time
        )

    def iter_csv_chunks(self, input_path: Path | None = None) -> Iterator[pd.DataFrame]:
        # Always resolve the plan first to ensure we use the CSV version
        original_path = (input_path or self.config.data_file).resolve(strict=False)
        effective_path, _, _ = self.get_ingestion_plan(original_path)

        csv_kwargs = self._csv_read_kwargs()
        try:
            iterator = pd.read_csv(
                effective_path,
                chunksize=self.config.csv_chunk_size,
                **csv_kwargs,
            )
        except UnicodeDecodeError:
            csv_kwargs["encoding_errors"] = "replace"
            iterator = pd.read_csv(
                effective_path,
                chunksize=self.config.csv_chunk_size,
                **csv_kwargs,
            )
        except Exception as exc:
            raise IngestionError(
                "Failed to initialize CSV chunk reader.",
                error_code="INGESTION_CHUNK_READER_INIT_FAILED",
                context={"path": str(effective_path), "chunk_size": self.config.csv_chunk_size},
            ) from exc

        for chunk_idx, chunk in enumerate(iterator, start=1):
            yield self.normalize_columns(chunk)

    def _convert_xlsx_to_csv(self, input_path: Path, output_path: Path) -> None:
        """Optimized Excel to CSV conversion."""
        try:
            df, sheet_mode = self._read_excel(input_path)
            df.to_csv(output_path, index=False, encoding="utf-8")
            LOGGER.info("Excel conversion completed.", extra={"sheet_mode": sheet_mode})
        except Exception as exc:
            raise IngestionError(
                "Failed to convert Excel to CSV.",
                error_code="INGESTION_CONVERSION_FAILED",
                context={"input": str(input_path), "output": str(output_path)},
            ) from exc

    def _read_excel(self, input_path: Path) -> tuple[pd.DataFrame, str]:
        sheet_mode = (read_env_value("EXCEL_SHEET_MODE") or "first_sheet").strip().lower()
        sheet_name = read_env_value("EXCEL_SHEET_NAME")

        if sheet_mode == "combine_sheets":
            sheets = pd.read_excel(
                input_path,
                engine="calamine",
                dtype=str,
                sheet_name=None,
                na_filter=False,
                keep_default_na=False,
            )
            frames: list[pd.DataFrame] = []
            for name, frame in sheets.items():
                tagged = frame.copy()
                tagged["source_sheet"] = str(name)
                frames.append(tagged)
            combined = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
            return combined, sheet_mode

        if sheet_mode in {"first_sheet", "single_sheet"}:
            target = sheet_name if sheet_name else 0
            df = pd.read_excel(
                input_path,
                engine="calamine",
                dtype=str,
                sheet_name=target,
                na_filter=False,
                keep_default_na=False,
            )
            return df, sheet_mode

        raise IngestionError(
            "Invalid EXCEL_SHEET_MODE value.",
            error_code="INGESTION_INVALID_SHEET_MODE",
            context={"sheet_mode": sheet_mode},
        )

    def _load_csv(self, path: Path) -> pd.DataFrame:
        csv_kwargs = self._csv_read_kwargs()
        try:
            df = pd.read_csv(path, **csv_kwargs)
        except UnicodeDecodeError:
            csv_kwargs["encoding_errors"] = "replace"
            df = pd.read_csv(path, **csv_kwargs)
        except Exception as exc:
            raise IngestionError(
                "Failed to read CSV file.",
                error_code="INGESTION_CSV_READ_FAILED",
                context={"path": str(path)},
            ) from exc
        return self.normalize_columns(df)

    def _csv_read_kwargs(self) -> dict[str, object]:
        # Keep parsing consistent between streaming and in-memory loads.
        return {
            "encoding": "utf-8",
            "engine": "c",
            "low_memory": False,
            "dtype": str,
            "na_filter": False,
        }

    def _should_stream(self, path: Path, size_mb: float) -> bool:
        if not self.config.enable_streaming_for_csv:
            return False
        return size_mb >= self.config.stream_file_size_mb_threshold

    @classmethod
    def normalize_columns(cls, df: pd.DataFrame) -> pd.DataFrame:
        normalized = df.copy()
        normalized.columns = (
            normalized.columns.astype(str).str.strip().str.lower().str.replace(" ", "_", regex=False)
        )

        rename_map: dict[str, str] = {}
        for canonical, aliases in cls.COLUMN_ALIASES.items():
            for alias in aliases:
                key = alias.lower()
                if key in normalized.columns:
                    rename_map[key] = canonical

        if rename_map:
            normalized = normalized.rename(columns=rename_map)
        return normalized
