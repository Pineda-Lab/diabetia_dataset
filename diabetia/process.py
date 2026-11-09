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

    Las n ventanas de un paciente empiezan un año aparte y cubren n + 1 años: c_k = v_k + v_(k+1). Con n impar,
    las ventanas 1, 3, …, n cubren todos los años sin traslape y el total es exacto. Con n par, el total es
    (ventanas impares) + v_(n+1) = (ventanas pares) + v_1; es exacto si el primer año no tiene visitas (first_cx un
    año o más después del inicio de la primera ventana) o el último tampoco (last_cx antes del segundo año de la
    última ventana); si no, queda acotado por max(impares, pares) y min(impares + c_n, pares + c_1).
    """
    d = df[[PATIENT_ID, "x_start", "first_cx", "last_cx"]].copy()
    for col in ["x_start", "first_cx", "last_cx"]:
        d[col] = pd.to_datetime(d[col], errors="coerce")
    d["c"] = df["count_cx_w"].fillna(0)
    d = d.sort_values([PATIENT_ID, "x_start"])
    k = d.groupby(PATIENT_ID).cumcount()
    g = d.groupby(PATIENT_ID)
    odd = d["c"].where(k % 2 == 0, 0).groupby(d[PATIENT_ID]).sum()  # ventanas 1, 3, 5, …
    even = d["c"].where(k % 2 == 1, 0).groupby(d[PATIENT_ID]).sum()
    n, first, last = g.size(), g.first(), g.last()
    first_year_empty = first["first_cx"] >= first["x_start"] + pd.DateOffset(years=1)
    last_year_empty = last["last_cx"] < last["x_start"] + pd.DateOffset(years=1)
    exact = odd.where((n % 2 == 1) | last_year_empty, even.where(first_year_empty))
    low = exact.fillna(odd.combine(even, max))
    high = exact.fillna((odd + last["c"]).combine(even + first["c"], min))
    return {
        "sum_over_windows": int(d["c"].sum()),
        "visits_min": int(low.sum()),
        "visits_max": int(high.sum()),
        "patients_exact": int((low == high).sum()),
        "patients": int(len(n)),
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
