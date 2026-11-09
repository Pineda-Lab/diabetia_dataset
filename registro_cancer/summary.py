"""Resumen armonizado del Registro Nacional de Cáncer (México), solicitud de transparencia 2020.

Lee data/registro-cancer/Mexico-RegistroNacionalCancer2020.xlsx. Cada renglón es un caso
de cáncer; el registro no trae identificador de paciente.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "registro-cancer"
INPUT_FILE = DATA_DIR / "Mexico-RegistroNacionalCancer2020.xlsx"
RESULTS_DIR = ROOT / "results" / "auxiliary"
OUTPUT_FILE = RESULTS_DIR / "summary_registro_cancer.csv"

# Mismos rangos que reportan SIDIAP, CPRD y MIMIC-IV, para poder comparar.
AGE_BINS = [-1, 17, 64, 200]
AGE_LABELS = ["<18", "18 – 64", "65 and older"]


def _count(mask: pd.Series) -> str:
    return f"{int(mask.sum()):,} ({mask.mean():.2%})"


def load_data(path: Path = INPUT_FILE, drop_duplicates: bool = False) -> pd.DataFrame:
    """Carga el registro. La primera columna es un índice sin nombre y se descarta.

    Hay renglones idénticos en todas las columnas; `drop_duplicates=True` los elimina.
    """
    df = pd.read_excel(path).iloc[:, 1:]
    if drop_duplicates:
        df = df.drop_duplicates()
    return df


def summary(df: pd.DataFrame) -> pd.Series:
    years = df["AÑO_DE_INCIDENCIA"][df["AÑO_DE_INCIDENCIA"] != 9999]
    age = pd.cut(df["EDAD_CUMPLIDA_AL_DIAGNOSTICO"], AGE_BINS, labels=AGE_LABELS)
    rows = {
        ("", "Patients"): f"{len(df):,} (cases; patients are not uniquely identified)",
        ("", "Records"): f"{len(df):,} incident cancer cases",
        ("", "Collection years"): f"{years.min()}–{years.max()}",
        ("Sex", "Female"): _count(df["SEXO"] == "MUJER"),
        ("Sex", "Male"): _count(df["SEXO"] == "HOMBRE"),
    }
    rows.update({("Age (years)", a): _count(age == a) for a in AGE_LABELS})
    return pd.Series(rows, name="National Cancer Registry (Mexico)")


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result = summary(load_data())
    result.rename_axis(["Variable", "Category"]).to_csv(OUTPUT_FILE)
    print(f"Generado: {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
