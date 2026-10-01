from __future__ import annotations
from io import BytesIO, StringIO
from pathlib import Path
import pandas as pd
import numpy as np

def list_excel_sheets(file_bytes):
    xls = pd.ExcelFile(BytesIO(file_bytes), engine="openpyxl")
    return xls.sheet_names

def read_table(filename, file_bytes, sheet_name=None, decimal="."):
    ext = Path(filename).suffix.lower()

    if ext == ".xlsx":
        return pd.read_excel(
            BytesIO(file_bytes),
            sheet_name=sheet_name if sheet_name is not None else 0,
            engine="openpyxl",
        )

    if ext in {".csv", ".txt"}:
        raw = file_bytes.decode("utf-8-sig", errors="replace")
        attempts = [
            dict(sep=None, engine="python"),
            dict(sep=";", engine="python"),
            dict(sep=",", engine="python"),
            dict(sep="\t", engine="python"),
            dict(sep=r"\s+", engine="python"),
        ]
        for kwargs in attempts:
            try:
                df = pd.read_csv(StringIO(raw), decimal=decimal, **kwargs)
                if df.shape[1] >= 1:
                    return df
            except Exception:
                pass
        raise ValueError("No pude leer el archivo como una tabla convencional.")

    raise ValueError("Formato no compatible. Usa XLSX, CSV o TXT.")

def extract_numeric_column(df, column_name):
    original = df[column_name]
    numeric = pd.to_numeric(original, errors="coerce")
    finite_mask = numeric.notna() & np.isfinite(numeric.astype(float))
    valid = numeric.loc[finite_mask].to_numpy(dtype=float)

    excluded_empty = int(original.isna().sum())
    excluded_non_numeric = int(((~original.isna()) & (~finite_mask)).sum())
    zero_count = int(np.sum(valid == 0))

    return {
        "values": valid,
        "valid_count": int(len(valid)),
        "excluded_empty": excluded_empty,
        "excluded_non_numeric": excluded_non_numeric,
        "zero_count": zero_count,
    }
