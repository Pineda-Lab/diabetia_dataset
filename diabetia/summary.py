"""Resumen armonizado de DiabetIA para la Tabla 2 (comparación con otras bases).

Usa las mismas definiciones que la Tabla 1 (primera ventana) para que las cifras coincidan.
"""

import pandas as pd

from process import ROOT, load_data, process
from table1 import COMORBIDITIES, patient_level

RESULTS_DIR = ROOT / "results"
OUTPUT_FILE = RESULTS_DIR / "summary_diabetia.csv"

# Mismos rangos que reportan SIDIAP, CPRD y MIMIC-IV, para poder comparar.
AGE_BINS = [-1, 17, 64, 200]
AGE_LABELS = ["<18", "18 – 64", "65 and older"]


def _count(mask: pd.Series) -> str:
    return f"{int(mask.sum()):,} ({mask.mean():.2%})"


def summary(df: pd.DataFrame) -> pd.Series:
    patients = patient_level(df, baseline="first")
    age = pd.cut(patients["age_at_wx"], AGE_BINS, labels=AGE_LABELS)
    rows = {
        ("", "Patients"): f"{len(patients):,}",
        ("", "Records"): f"{len(df):,} two-year windows ({int(df['count_cx_w'].sum()):,} visits)",
        ("", "Collection years"): f"{pd.to_datetime(df['first_cx']).dt.year.min()}–{pd.to_datetime(df['last_cx']).dt.year.max()}",
        ("Sex", "Female"): _count(patients["cs_sex"] == "F"),
        ("Sex", "Male"): _count(patients["cs_sex"] == "M"),
    }
    rows.update({("Age (years)", a): _count(age == a) for a in AGE_LABELS})
    rows.update({
        ("Comorbidities", "Type 2 diabetes"): _count(patients[COMORBIDITIES["T2D (E11)"]].any(axis=1)),
        ("Comorbidities", "Hypertension"): _count(patients[COMORBIDITIES["HTN (I10)"]].any(axis=1)),
        ("Comorbidities", "Obesity"): _count(patients["bmi"] >= 30),
        ("Comorbidities", "Cardiovascular disease"): _count(
            patients[COMORBIDITIES["Heart or coronary disease (I20–I25, I50)"]].any(axis=1)
        ),
    })
    return pd.Series(rows, name="DiabetIA")


def write_summary(df: pd.DataFrame) -> None:
    """Genera results/summary_diabetia.csv a partir de los datos ya procesados."""
    RESULTS_DIR.mkdir(exist_ok=True)
    summary(df).rename_axis(["Variable", "Category"]).to_csv(OUTPUT_FILE)
    print(f"Generado: {OUTPUT_FILE.relative_to(ROOT)}")


def main() -> None:
    write_summary(process(load_data()))


if __name__ == "__main__":
    main()
