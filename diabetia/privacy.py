"""Riesgo de reidentificación: k-anonimato de los cuasi-identificadores de la versión tabular.

Para cada combinación de cuasi-identificadores (sexo, fecha o año de nacimiento, unidad médica y fechas de
primera y última visita) cuenta cuántos pacientes comparten exactamente los mismos valores (clase de
equivalencia, k). Un paciente con k = 1 es único en la base con esos atributos. Solo se reportan conteos
agregados.
"""

import pandas as pd

from process import PATIENT_ID, has_visit, load_data, process
from table1 import AUXILIARY_DIR

# Combinaciones evaluadas, de la menos a la más informativa.
SCENARIOS = {
    "Sex + year of birth": ["cs_sex", "birth_year"],
    "Sex + year of birth + care unit": ["cs_sex", "birth_year", "careunit"],
    "Sex + date of birth": ["cs_sex", "birthdate"],
    "Sex + date of birth + care unit": ["cs_sex", "birthdate", "careunit"],
    "Sex + date of birth + care unit + date of first visit": ["cs_sex", "birthdate", "careunit", "first_cx"],
    "Sex + date of birth + care unit + dates of first and last visit": [
        "cs_sex", "birthdate", "careunit", "first_cx", "last_cx"],
}


def patients_table(df: pd.DataFrame) -> pd.DataFrame:
    """Un renglón por paciente con sus atributos constantes (la unidad médica, de sus ventanas con visita)."""
    first = df.sort_values("window").groupby(PATIENT_ID)[["cs_sex", "birthdate", "first_cx", "last_cx"]].first()
    unit = df[has_visit(df)].groupby(PATIENT_ID)["careunit"].first()
    patients = first.join(unit)
    patients["birth_year"] = pd.to_datetime(patients["birthdate"], errors="coerce").dt.year
    return patients


def k_anonymity(patients: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, cols in SCENARIOS.items():
        k = patients.groupby(cols, dropna=False)[cols[0]].transform("size")
        n = len(k)
        rows.append({
            "Quasi-identifiers": name,
            "Patients": n,
            "Unique (k = 1), n (%)": f"{(k == 1).sum():,} ({(k == 1).mean():.1%})",
            "k < 5, n (%)": f"{(k < 5).sum():,} ({(k < 5).mean():.1%})",
            "k < 11, n (%)": f"{(k < 11).sum():,} ({(k < 11).mean():.1%})",
            "Median k": int(k.median()),
        })
    return pd.DataFrame(rows)


def write_privacy(df: pd.DataFrame) -> None:
    """Genera results/auxiliary/reidentification_risk.csv."""
    AUXILIARY_DIR.mkdir(parents=True, exist_ok=True)
    k_anonymity(patients_table(df)).to_csv(AUXILIARY_DIR / "reidentification_risk.csv", index=False)
    print("Generado: results/auxiliary/reidentification_risk.csv")


def main() -> None:
    write_privacy(process(load_data()))


if __name__ == "__main__":
    main()
