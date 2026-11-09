"""Technical Validation: cobertura temporal (Tabla Suplementaria S8 y datos de la figura temporal).

- results/auxiliary/temporal_coverage.csv: por año de inicio de la ventana (x_start), número de ventanas,
  ventanas con visita, pacientes y % de ventanas con visita que tienen cada variable. La figura
  (diabetia/figure_temporal.R) se hace a partir de este archivo, sin volver a leer la base.
- results/supplementary/table_s8.{csv,html}: cobertura por unidad médica.
"""

import pandas as pd

from completeness import recorded
from process import PATIENT_ID, has_visit, load_data, process
from table1 import AUXILIARY_DIR, SUPPLEMENTARY_DIR, save_word_table

TITLE = "Supplementary Table S8. Temporal coverage of DiabetIA by care unit."
FOOTNOTE = (
    "Only two-year windows with at least one visit are counted. Windows per patient: median (interquartile range) "
    "of the windows with a visit of each patient in that care unit. Years: calendar years of the start of the "
    "first and last window (x_start). Successive windows of a patient start one year apart and overlap by one "
    "year. {dates}"
)


def _median_iqr(values: pd.Series) -> str:
    q1, med, q3 = values.quantile([0.25, 0.5, 0.75])
    return f"{med:.0f} ({q1:.0f}–{q3:.0f})"


def coverage_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Formato largo: un renglón por año y variable."""
    year = pd.to_datetime(df["x_start"], errors="coerce").dt.year.rename("year")
    visit = has_visit(df)
    counts = pd.DataFrame({
        "windows": df.groupby(year).size(),
        "windows_with_visit": visit.groupby(year).sum(),
        "patients_with_visit": df.loc[visit].groupby(year.loc[visit])[PATIENT_ID].nunique(),
    }).fillna(0).astype(int)

    flags = recorded(df.loc[visit])
    flags.columns = [f"{group}|{name}" for group, name in flags.columns]
    with_value = flags.groupby(year.loc[visit]).sum()
    long = with_value.reset_index().melt(id_vars="year", var_name="variable", value_name="n_with_value")
    long[["group", "variable"]] = long["variable"].str.split("|", n=1, expand=True)
    long = long.merge(counts.reset_index(), on="year")
    long["pct"] = 100 * long["n_with_value"] / long["windows_with_visit"]
    return long[["year", "group", "variable", "windows", "windows_with_visit", "patients_with_visit",
                 "n_with_value", "pct"]]


def coverage_by_unit(df: pd.DataFrame) -> pd.DataFrame:
    df = df.loc[has_visit(df)]
    year = pd.to_datetime(df["x_start"], errors="coerce").dt.year

    def summary(d: pd.DataFrame, y: pd.Series) -> dict:
        return {
            "Patients, n": f"{d[PATIENT_ID].nunique():,}",
            "Windows with a visit, n": f"{len(d):,}",
            "Windows per patient": _median_iqr(d.groupby(PATIENT_ID).size()),
            "Years": f"{int(y.min())}–{int(y.max())}",
        }

    rows = {("Care unit", unit): summary(d, year.loc[d.index]) for unit, d in df.groupby("careunit")}
    rows[("", "Total")] = summary(df, year)
    result = pd.DataFrame(rows).T
    result.index.names = ["Variable", "Category"]
    return result


def date_ranges(df: pd.DataFrame) -> str:
    d = {c: pd.to_datetime(df[c], errors="coerce") for c in ["x_start", "x_end", "y_end", "first_cx", "last_cx"]}
    fmt = lambda s: s.strftime("%Y-%m-%d")
    return (f"Follow-up periods span {fmt(d['x_start'].min())} to {fmt(d['x_end'].max())}, and outcome periods end "
            f"by {fmt(d['y_end'].max())}. Recorded visit history (first_cx – last_cx): {fmt(d['first_cx'].min())} "
            f"to {fmt(d['last_cx'].max())}.")


def write_temporal(df: pd.DataFrame) -> None:
    """Genera results/auxiliary/temporal_coverage.csv y results/supplementary/table_s8.{csv,html}."""
    SUPPLEMENTARY_DIR.mkdir(parents=True, exist_ok=True)
    AUXILIARY_DIR.mkdir(parents=True, exist_ok=True)
    coverage_by_year(df).to_csv(AUXILIARY_DIR / "temporal_coverage.csv", index=False)
    result = coverage_by_unit(df)
    result.to_csv(SUPPLEMENTARY_DIR / "table_s8.csv")
    save_word_table(result, SUPPLEMENTARY_DIR / "table_s8.html", TITLE, FOOTNOTE.format(dates=date_ranges(df)))
    print("Generado: results/auxiliary/temporal_coverage.csv y results/supplementary/table_s8.{csv,html}")


def main() -> None:
    write_temporal(process(load_data()))


if __name__ == "__main__":
    main()
