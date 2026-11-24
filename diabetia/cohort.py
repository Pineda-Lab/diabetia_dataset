"""Descripción de la cohorte para Methods (criterios de inclusión) y Data Records.

Ventanas por paciente (todas y con visita), duración del seguimiento (primera a última visita, y del inicio de la
primera ventana al final de la última) y edad mínima (en la primera visita, en la primera ventana y al 31 de
diciembre de 2018), para comprobar los criterios de "seguimiento de al menos tres años" y "18 años o más".
También cuenta los pacientes y ventanas con 90 años o más: el método Safe Harbor de HIPAA pide agrupar esas edades.
Solo se reportan conteos y percentiles agregados.
"""

import pandas as pd

from process import PATIENT_ID, has_visit, load_data, process
from table1 import AUXILIARY_DIR

YEAR = 365.25


def _describe(name: str, values: pd.Series, decimals: int = 1) -> dict:
    q = values.quantile([0, 0.25, 0.5, 0.75, 1])
    fmt = lambda v: f"{v:.{decimals}f}"
    return {"Measure": name, "n": int(values.notna().sum()), "Minimum": fmt(q[0]), "Q1": fmt(q[0.25]),
            "Median": fmt(q[0.5]), "Q3": fmt(q[0.75]), "Maximum": fmt(q[1])}


def _count(name: str, mask: pd.Series) -> dict:
    return {"Measure": name, "n": int(mask.sum()), "Minimum": f"{mask.mean():.2%}", "Q1": "", "Median": "", "Q3": "",
            "Maximum": ""}


def cohort_checks(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["x_start", "y_end", "first_cx", "last_cx", "birthdate"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    g = df.groupby(PATIENT_ID)
    windows = g.size()
    visit_windows = has_visit(df).groupby(df[PATIENT_ID]).sum()
    first = g[["first_cx", "last_cx", "birthdate"]].first()
    visits_span = (first["last_cx"] - first["first_cx"]).dt.days / YEAR
    windows_span = (g["y_end"].max() - g["x_start"].min()).dt.days / YEAR
    age_first_visit = (first["first_cx"] - first["birthdate"]).dt.days / YEAR
    age_2018 = (pd.Timestamp("2018-12-31") - first["birthdate"]).dt.days / YEAR
    age_first_window = df.sort_values("window").groupby(PATIENT_ID)["age_at_wx"].first()
    age_last_visit = (first["last_cx"] - first["birthdate"]).dt.days / YEAR
    age_max_window = g["age_at_wx"].max()
    rows = [
        _describe("Windows per patient", windows, 0),
        _describe("Windows with a visit per patient", visit_windows, 0),
        _count("Patients with 1 window", windows == 1),
        _count("Patients with 1 window with a visit", visit_windows == 1),
        _describe("Years from first to last visit (first_cx to last_cx)", visits_span),
        _count("Patients with < 3 years from first to last visit", visits_span < 3),
        _count("Patients with < 2 years from first to last visit", visits_span < 2),
        _describe("Years from first x_start to last y_end", windows_span),
        _describe("Age at first visit (first_cx), years", age_first_visit),
        _count("Patients aged < 18 years at first visit", age_first_visit < 18),
        _describe("Age at first window (age_at_wx), years", age_first_window),
        _describe("Age on 31 December 2018, years", age_2018),
        _count("Patients aged < 18 years on 31 December 2018", age_2018 < 18),
        _describe("Age at last visit (last_cx), years", age_last_visit),
        _count("Patients aged >= 90 years at last visit", age_last_visit >= 90),
        _count("Patients aged >= 90 years (age_at_wx) in any window", age_max_window >= 90),
        _count("Windows with age_at_wx >= 90 years", df["age_at_wx"] >= 90),
        _describe("Year of first visit", first["first_cx"].dt.year, 0),
        _describe("Year of last visit", first["last_cx"].dt.year, 0),
    ]
    return pd.DataFrame(rows)


def write_cohort(df: pd.DataFrame) -> None:
    """Genera results/auxiliary/cohort_checks.csv (en los conteos, la columna Minimum es el porcentaje)."""
    AUXILIARY_DIR.mkdir(parents=True, exist_ok=True)
    cohort_checks(df).to_csv(AUXILIARY_DIR / "cohort_checks.csv", index=False)
    print("Generado: results/auxiliary/cohort_checks.csv")


def main() -> None:
    write_cohort(process(load_data()))


if __name__ == "__main__":
    main()
