"""Technical Validation: completitud de las variables (Tabla Suplementaria S3).

Para cada variable demográfica, antropométrica, de signos vitales y de laboratorio, cuenta las
ventanas de dos años con al menos una visita que tienen un valor registrado, en total y según el
estado de DM2 de esa misma ventana, y los pacientes con al menos un valor en cualquier ventana.
Las variables de medición son las de limits.csv (las mismas de la Tabla S2 y de la figura). Las
ventanas sin visitas no pueden tener mediciones, así que no entran en el denominador; su número se
reporta en la nota al pie.
"""

import numpy as np
import pandas as pd

from process import PATIENT_ID, has_visit, load_data, process
from table1 import COMPLICATIONS, GROUPS, SUPPLEMENTARY_DIR, T2D, save_word_table
from validation import load_limits

DEMOGRAPHICS = {
    "Sex": "cs_sex",
    "Age": "age_at_wx",
}

TITLE = (
    "Supplementary Table S3. Completeness of demographic, anthropometric, vital sign and laboratory variables, "
    "by two-year window and type 2 diabetes status, and by patient."
)
FOOTNOTE = (
    "T2D= Type 2 diabetes. Values are n (%) of windows (or patients) with a recorded value, relative to the N of "
    "each column. Window columns include only two-year windows with at least one visit; {no_visit:,} of "
    "{all_windows:,} windows ({pct_no_visit:.1%}) had no visit and therefore no recorded measurements. "
    "A measurement is recorded in a window when it has at least one value during the two-year follow-up "
    "(within-window median not missing); BMI requires both weight and height. Window columns classify each window "
    "by the diagnoses recorded in that same window: T2D with complications= T2D and any diagnosis of E11.2, E11.3, "
    "E11.4 or E11.5. The last column counts patients with a recorded value in at least one window."
)


def window_group(df: pd.DataFrame) -> pd.Series:
    """Grupo de cada ventana según los diagnósticos registrados en esa misma ventana."""
    t2d = df[T2D] > 0
    has_comp = (df[list(COMPLICATIONS.values())] > 0).any(axis=1)
    return pd.Series(np.select([t2d & has_comp, t2d], [GROUPS[3], GROUPS[2]], default=GROUPS[1]), index=df.index)


def _count(mask: pd.Series) -> str:
    """Celda: "n (%)" sobre el total de la columna, con un decimal."""
    return f"{int(mask.sum()):,} ({mask.mean():.1%})"


def recorded(df: pd.DataFrame) -> pd.DataFrame:
    """Indicador por ventana (True/False) de valor registrado para cada variable."""
    flags = {("Demographics", name): df[col].notna() for name, col in DEMOGRAPHICS.items()}
    for row in load_limits().itertuples():
        if row.column == "bmi":
            value = df["fn_weight_median"].notna() & df["fn_height_median"].notna()
        else:
            value = df[f"{row.column}_median"].notna()
        flags[(row.group, f"{row.name} ({row.unit})")] = value
    return pd.DataFrame(flags)


def completeness(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula la Tabla S3: "n (%)" de ventanas con visita y de pacientes con valor registrado."""
    df = df[has_visit(df)]
    flags = recorded(df)
    group = window_group(df)
    columns = {f"All windows (N={len(flags):,})": flags}
    for g in GROUPS[1:]:
        subset = flags[group == g]
        columns[f"{g} (N={len(subset):,})"] = subset
    patients = flags.groupby(df[PATIENT_ID]).any()
    columns[f"Patients, any window (N={len(patients):,})"] = patients

    result = pd.DataFrame({name: {var: _count(f[var]) for var in flags.columns} for name, f in columns.items()})
    result.index = pd.MultiIndex.from_tuples(result.index, names=["Variable", "Category"])
    return result


def write_completeness(df: pd.DataFrame) -> None:
    """Genera results/supplementary/table_s3.{csv,html} a partir de los datos ya procesados."""
    SUPPLEMENTARY_DIR.mkdir(parents=True, exist_ok=True)
    result = completeness(df)
    result.to_csv(SUPPLEMENTARY_DIR / "table_s3.csv")
    no_visit = int((~has_visit(df)).sum())
    footnote = FOOTNOTE.format(no_visit=no_visit, all_windows=len(df), pct_no_visit=no_visit / len(df))
    save_word_table(result, SUPPLEMENTARY_DIR / "table_s3.html", TITLE, footnote)
    print("Generado: results/supplementary/table_s3.csv y results/supplementary/table_s3.html")


def main() -> None:
    write_completeness(process(load_data()))


if __name__ == "__main__":
    main()
