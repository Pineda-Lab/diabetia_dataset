"""Technical Validation: consistencia interna de los datos (Tabla Suplementaria S7).

Cada regla cuenta las ventanas (o pacientes) evaluables y las que no la cumplen. Los registros
inconsistentes se cuentan pero no se eliminan.
"""

import pandas as pd

from process import PATIENT_ID, has_visit, load_data, process, visit_counts
from table1 import AUXILIARY_DIR, SUPPLEMENTARY_DIR, T2D, save_word_table

DATE_COLS = ["birthdate", "first_cx", "last_cx", "x_start", "x_end", "y_start", "y_end"]
FEMALE_ONLY = "ovarian_dysfunction"     # E28
MALE_ONLY = "testicular_dysfunction"    # E29
DAY_TOLERANCE = 2  # días de holgura en la duración de los periodos (años bisiestos, redondeo)

TITLE = "Supplementary Table S7. Internal consistency of dates, ages, diagnoses and window structure."
FOOTNOTE = (
    "Each rule was evaluated on the windows (or patients) with the information required; inconsistent records were "
    "flagged, not removed. Follow-up period= x_start to x_end; outcome period= y_start to y_end. Ages were computed "
    "in completed years at the start of the window (x_start); differences of up to 1 year were accepted because of "
    "rounding conventions. T2D= type 2 "
    "diabetes (diabetes_mellitus_type_2 diagnosis column; dx_year_e11 and dx_age_e11 for the year and age at "
    "diagnosis). Persistence of T2D is descriptive: a chronic diagnosis is expected to be recorded again in later "
    "windows with a visit."
)


def _age(birth: pd.Series, at: pd.Series) -> pd.Series:
    """Edad en años cumplidos en la fecha `at`."""
    before_birthday = (at.dt.month < birth.dt.month) | ((at.dt.month == birth.dt.month) & (at.dt.day < birth.dt.day))
    return at.dt.year - birth.dt.year - before_birthday.astype(int)


def _row(level, check, rule, evaluated, inconsistent):
    evaluated = pd.Series(evaluated).fillna(False).astype(bool)
    bad = pd.Series(inconsistent).fillna(False).astype(bool) & evaluated
    n = int(evaluated.sum())
    return {
        "Level": level,
        "Check": check,
        "Rule": rule,
        "Evaluated, n": f"{n:,}",
        "Inconsistent, n (%)": f"{int(bad.sum()):,} ({bad.sum() / n:.2%})" if n else "–",
    }


def consistency(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula la Tabla S7: una fila por regla de consistencia."""
    df = df.sort_values([PATIENT_ID, "window"]).copy()
    for col in DATE_COLS:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    visit = has_visit(df)
    days = lambda a, b: (df[b] - df[a]).dt.days
    rows = []

    # --- Ventanas -------------------------------------------------------------------------------
    rows.append(_row("Window", "Follow-up period order", "x_start < x_end",
                     df["x_start"].notna() & df["x_end"].notna(), df["x_start"] >= df["x_end"]))
    rows.append(_row("Window", "Follow-up period length", f"x_end − x_start = 2 years (± {DAY_TOLERANCE} days)",
                     df["x_start"].notna() & df["x_end"].notna(), (days("x_start", "x_end") - 730.5).abs() > DAY_TOLERANCE + 0.5))
    rows.append(_row("Window", "Outcome period follows follow-up", "y_start = x_end (± 1 day)",
                     df["y_start"].notna() & df["x_end"].notna(), days("x_end", "y_start").abs() > 1))
    rows.append(_row("Window", "Outcome period length", f"y_end − y_start = 1 year (± {DAY_TOLERANCE} days)",
                     df["y_start"].notna() & df["y_end"].notna(), (days("y_start", "y_end") - 365.25).abs() > DAY_TOLERANCE + 0.25))
    # age_at_wx es la edad al inicio de la ventana (x_start), aunque el diccionario dice x_end.
    age = _age(df["birthdate"], df["x_start"])
    rows.append(_row("Window", "Age vs date of birth", "|age_at_wx − age computed at x_start| ≤ 1 year",
                     df["age_at_wx"].notna() & age.notna(), (df["age_at_wx"] - age).abs() > 1))
    rows.append(_row("Window", "Adult age", "age_at_wx ≥ 18 years", df["age_at_wx"].notna(), df["age_at_wx"] < 18))
    rows.append(_row("Window", "Plausible age", "age_at_wx ≤ 110 years", df["age_at_wx"].notna(), df["age_at_wx"] > 110))
    rows.append(_row("Window", "Visits and care unit", "care unit recorded if and only if number of visits > 0",
                     pd.Series(True, index=df.index), visit != (df["count_cx_w"].fillna(0) > 0)))
    rows.append(_row("Window", "Window within visit history", "windows with a visit overlap first_cx – last_cx",
                     visit & df["first_cx"].notna() & df["last_cx"].notna(),
                     (df["x_end"] < df["first_cx"]) | (df["x_start"] > df["last_cx"])))
    rows.append(_row("Window", "Sex-specific diagnosis", "no ovarian dysfunction (E28) in men",
                     df["cs_sex"] == "M", df[FEMALE_ONLY] > 0))
    rows.append(_row("Window", "Sex-specific diagnosis", "no testicular dysfunction (E29) in women",
                     df["cs_sex"] == "F", df[MALE_ONLY] > 0))

    # Persistencia de DM2: ventanas con visita posteriores a la primera ventana con DM2.
    t2d = df[T2D] > 0
    seen_before = (t2d.groupby(df[PATIENT_ID]).cumsum() - t2d) > 0  # DM2 en alguna ventana anterior
    rows.append(_row("Window", "Persistence of T2D", "T2D recorded again in later windows with a visit",
                     seen_before & visit, ~t2d))

    # --- Pacientes ------------------------------------------------------------------------------
    g = df.groupby(PATIENT_ID)
    numbering = g["window"].agg(lambda w: list(w) == list(range(1, len(w) + 1)))
    rows.append(_row("Patient", "Window numbering", "windows numbered 1, 2, …, k without gaps",
                     pd.Series(True, index=numbering.index), ~numbering))
    step = g["x_start"].diff().dt.days
    bad_step = (step - 365.25).abs() > DAY_TOLERANCE + 0.25
    rows.append(_row("Patient", "Successive windows", f"x_start of successive windows 1 year apart (± {DAY_TOLERANCE} days)",
                     (g.size() > 1), bad_step.groupby(df[PATIENT_ID]).any()))
    every_patient = pd.Series(True, index=g.size().index)
    rows.append(_row("Patient", "Constant sex", "same sex in all windows", every_patient, g["cs_sex"].nunique() > 1))
    rows.append(_row("Patient", "Constant date of birth", "same date of birth in all windows",
                     every_patient, g["birthdate"].nunique() > 1))
    dx_recorded = g["dx_year_e11"].count() > 0
    rows.append(_row("Patient", "Constant T2D diagnosis year and age",
                     "same dx_year_e11 and dx_age_e11 in all windows where they are recorded",
                     dx_recorded, g[["dx_year_e11", "dx_age_e11"]].nunique().max(axis=1) > 1))
    rows.append(_row("Patient", "T2D diagnosis year in all windows",
                     "dx_year_e11 recorded in every window once it is recorded in one",
                     dx_recorded, g["dx_year_e11"].count() < g.size()))
    first = g.first()
    rows.append(_row("Patient", "Visit history order", "first_cx ≤ last_cx",
                     first["first_cx"].notna() & first["last_cx"].notna(), first["first_cx"] > first["last_cx"]))

    dx_year, dx_age = first["dx_year_e11"], first["dx_age_e11"]
    has_dx = dx_year.notna() & dx_age.notna()
    rows.append(_row("Patient", "Age at T2D diagnosis", "|dx_age_e11 − (dx_year_e11 − year of birth)| ≤ 1 year",
                     has_dx & first["birthdate"].notna(), (dx_age - (dx_year - first["birthdate"].dt.year)).abs() > 1))
    rows.append(_row("Patient", "Adult-onset T2D", "dx_age_e11 ≥ 18 years", dx_age.notna(), dx_age < 18))
    last_year = g["y_end"].max().dt.year
    rows.append(_row("Patient", "T2D diagnosis year within life and observation",
                     "year of birth ≤ dx_year_e11 ≤ year of last y_end",
                     dx_year.notna(), (dx_year < first["birthdate"].dt.year) | (dx_year > last_year)))
    any_t2d = t2d.groupby(df[PATIENT_ID]).any()
    rows.append(_row("Patient", "T2D diagnosis with year", "patients with T2D recorded in a window have dx_year_e11",
                     any_t2d, dx_year.isna()))
    first_t2d_end = df.loc[t2d].groupby(PATIENT_ID)["x_end"].min().dt.year.reindex(first.index)
    rows.append(_row("Patient", "T2D diagnosis year before first record", "dx_year_e11 ≤ year of x_end of the first window with T2D",
                     dx_year.notna() & first_t2d_end.notna(), dx_year > first_t2d_end))
    rows.append(_row("Patient", "Diagnosis year with T2D record", "patients with dx_year_e11 have T2D recorded in some window",
                     dx_year.notna(), ~any_t2d))

    return pd.DataFrame(rows)


def write_consistency(df: pd.DataFrame) -> None:
    """Genera results/supplementary/table_s7.{csv,html} y results/auxiliary/visit_counts.csv."""
    SUPPLEMENTARY_DIR.mkdir(parents=True, exist_ok=True)
    AUXILIARY_DIR.mkdir(parents=True, exist_ok=True)
    result = consistency(df)
    result.to_csv(SUPPLEMENTARY_DIR / "table_s7.csv", index=False)
    table = result.set_index(["Level", "Check"])
    table.index.names = ["Variable", "Category"]
    save_word_table(table, SUPPLEMENTARY_DIR / "table_s7.html", TITLE, FOOTNOTE)
    pd.Series(visit_counts(df)).to_csv(AUXILIARY_DIR / "visit_counts.csv", header=["visits"])
    print("Generado: results/supplementary/table_s7.{csv,html} y results/auxiliary/visit_counts.csv")


def main() -> None:
    write_consistency(process(load_data()))


if __name__ == "__main__":
    main()
