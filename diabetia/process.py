"""Procesamiento de datos de DiabetIA Insignia.

Lee data/diabetia/hk_database.csv y aplica los pasos de procesamiento.
"""

from pathlib import Path

import pandas as pd
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "diabetia"
INPUT_FILE = DATA_DIR / "hk_database.csv"
DICTIONARY_FILE = DATA_DIR / "data_dictionary.xlsx"

# Cada paciente (cx_curp) tiene varios renglones; cada renglón es una ventana
# de tiempo: 2 años de seguimiento (x_start–x_end) y 1 año de validación (y_start–y_end).
PATIENT_ID = "cx_curp"
WINDOW_COLS = ["window", "x_start", "x_end", "y_start", "y_end"]

# Variables objetivo: diabetes mellitus tipo 2 (E11) y sus subcódigos CIE-10.
TARGETS = ["e11", "e110", "e111", "e112", "e113", "e114", "e115", "e116", "e117", "e118", "e119"]


def read_csv_progress(path: Path, chunksize: int = 200_000, **kwargs) -> pd.DataFrame:
    """Lee un CSV por bloques mostrando una barra de progreso según los bytes leídos."""
    with open(path, "rb") as f, tqdm(
        total=path.stat().st_size, desc=f"Leyendo {path.name}", unit="B", unit_scale=True
    ) as bar:
        chunks = []
        for chunk in pd.read_csv(f, chunksize=chunksize, **kwargs):
            chunks.append(chunk)
            bar.update(f.tell() - bar.n)
        bar.update(bar.total - bar.n)
    return pd.concat(chunks, ignore_index=True)


def load_data(path: Path = INPUT_FILE) -> pd.DataFrame:
    """Carga la base de datos principal."""
    return read_csv_progress(path, low_memory=False)


def load_dictionary(path: Path = DICTIONARY_FILE) -> pd.DataFrame:
    """Carga el diccionario de variables (Group, column, Type, Description)."""
    dictionary = pd.read_excel(path)
    dictionary["Group"] = dictionary["Group"].ffill()
    return dictionary


def drop_patients_without_careunit(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina pacientes sin unidad de atención en ninguna de sus ventanas."""
    has_careunit = df["careunit"].notna().groupby(df[PATIENT_ID]).transform("any")
    return df[has_careunit]


def has_visit(df: pd.DataFrame) -> pd.Series:
    """Ventanas con al menos una visita. careunit nulo coincide con count_cx_w nulo (sin visitas);
    son 414,770 ventanas, el número que reporta el manuscrito."""
    return df["careunit"].notna()


def visit_counts(df: pd.DataFrame) -> dict:
    """Visitas: la suma sobre ventanas cuenta dos veces los años en que se traslapan ventanas sucesivas.

    Cota inferior sin traslapes: por paciente, la mayor suma entre las ventanas impares y las pares
    (cada conjunto cubre años disjuntos).
    """
    counts = df["count_cx_w"].fillna(0)
    odd = counts.where(df["window"] % 2 == 1, 0).groupby(df[PATIENT_ID]).sum()
    even = counts.where(df["window"] % 2 == 0, 0).groupby(df[PATIENT_ID]).sum()
    return {
        "sum_over_windows": int(counts.sum()),
        "lower_bound_non_overlapping": int(odd.combine(even, max).sum()),
    }


def process(df: pd.DataFrame) -> pd.DataFrame:
    """Pasos de procesamiento."""
    df = drop_patients_without_careunit(df)
    return df


def main() -> None:
    df = load_data()
    print(f"Cargado {INPUT_FILE.name}: {df.shape[0]:,} filas x {df.shape[1]} columnas")
    df = process(df)
    print(f"Procesado: {df.shape[0]:,} ventanas, {df[PATIENT_ID].nunique():,} pacientes")


if __name__ == "__main__":
    main()
