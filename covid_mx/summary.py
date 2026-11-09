"""Resumen armonizado de los datos abiertos COVID-19 de la Secretaría de Salud (México).

Lee data/covid-mx/*.csv. Los archivos anuales se traslapan: un mismo ID_REGISTRO puede
aparecer en dos archivos, así que se conserva su versión más reciente (FECHA_ACTUALIZACION).
Cada registro es un caso estudiado (sospechoso o confirmado), no un paciente único.

Códigos: SEXO 1=mujer, 2=hombre; comorbilidades 1=sí, 2=no, 97/98/99=no aplica/se ignora;
CLASIFICACION_FINAL 1–3 = caso confirmado de SARS-CoV-2.
"""

from pathlib import Path

import pandas as pd
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "covid-mx"
RESULTS_DIR = ROOT / "results"
OUTPUT_FILE = RESULTS_DIR / "summary_covid_mx.csv"

COMORBIDITIES = {
    "Type 2 diabetes": "DIABETES",
    "Hypertension": "HIPERTENSION",
    "Obesity": "OBESIDAD",
    "Cardiovascular disease": "CARDIOVASCULAR",
}
COLUMNS = ["FECHA_ACTUALIZACION", "ID_REGISTRO", "FECHA_INGRESO", "SEXO", "EDAD", "CLASIFICACION_FINAL"] + list(
    COMORBIDITIES.values()
)

# Mismos rangos que reportan SIDIAP, CPRD y MIMIC-IV, para poder comparar.
AGE_BINS = [-1, 17, 64, 200]
AGE_LABELS = ["<18", "18 – 64", "65 and older"]


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


def _count(mask: pd.Series) -> str:
    return f"{int(mask.sum()):,} ({mask.mean():.2%})"


def load_data(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Une los archivos anuales y elimina registros repetidos entre archivos."""
    parts = [
        read_csv_progress(f, usecols=COLUMNS, encoding="latin-1", dtype={"ID_REGISTRO": str})
        for f in sorted(data_dir.glob("*.csv"))
    ]
    df = pd.concat(parts, ignore_index=True)
    return df.sort_values("FECHA_ACTUALIZACION").drop_duplicates("ID_REGISTRO", keep="last")


def summary(df: pd.DataFrame) -> pd.Series:
    years = df["FECHA_INGRESO"].str[:4].astype(int)
    age = pd.cut(df["EDAD"], AGE_BINS, labels=AGE_LABELS)
    rows = {
        ("", "Patients"): f"{len(df):,} (records; patients are not uniquely identified)",
        ("", "Records"): f"{len(df):,} suspected or confirmed cases",
        ("", "Confirmed SARS-CoV-2"): _count(df["CLASIFICACION_FINAL"].isin([1, 2, 3])),
        ("", "Collection years"): f"{years.min()}–{years.max()}",
        ("Sex", "Female"): _count(df["SEXO"] == 1),
        ("Sex", "Male"): _count(df["SEXO"] == 2),
    }
    rows.update({("Age (years)", a): _count(age == a) for a in AGE_LABELS})
    rows.update({("Comorbidities", name): _count(df[col] == 1) for name, col in COMORBIDITIES.items()})
    return pd.Series(rows, name="COVID-19 Open Data (Mexico)")


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    result = summary(load_data())
    result.rename_axis(["Variable", "Category"]).to_csv(OUTPUT_FILE)
    print(f"Generado: {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
