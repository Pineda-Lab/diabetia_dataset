"""Technical Validation: plausibilidad de mediciones y laboratorios (Tabla Suplementaria S2).

Compara los valores mínimos y máximos registrados en DiabetIA (columnas *_min y *_max de
cada ventana) con el rango de referencia y con los valores extremos documentados en la
literatura (Tabla Suplementaria S4). Los valores fuera de esos límites se
cuentan pero no se eliminan.
"""

from pathlib import Path

import pandas as pd

from process import has_visit, load_data, process
from table1 import SUPPLEMENTARY_DIR, save_word_table

# Referencias de los valores extremos documentados (numeración de la Tabla Suplementaria S4).
REFERENCES = {
    1: "Kenney WL, DeGroot DW, Holowatz LA. Extremes of human heat tolerance: life at the precipice of thermoregulatory failure. J Therm Biol. 2004;29(7-8):479-85.",
    2: "Henry CJK. The biology of human starvation: some new insights. Nutr Bull. 2001;26(3):205-11.",
    3: "Letter to the Editor: Measured Values Incompatible with Human Life. EJIFCC. 2011;22(2):52-4.",
    6: "Alabbood M. The Highest HbA1c Ever Recorded: A Case Report. Endocr Pract. 2022;28(12):S23. doi:10.1016/j.eprac.2022.10.042.",
    9: "Triglyceride Levels Greater Than 10,000 mg/dL in a 49-Year-Old Female without Evidence of Pancreatitis. Case Rep Endocrinol. 2019. PMCID: PMC6556268.",
    10: "Guinness World Records. Heaviest man ever.",
    11: "Guinness World Records. Tallest man ever.",
    12: "Guinness World Records. Shortest man ever.",
    13: "Gilbert M, Busund R, Skagseth A, Nilsen PA, Solbø JP. Resuscitation from accidental hypothermia of 13.7 °C with circulatory arrest. Lancet. 2000;355(9201):375-6.",
    14: "Survival in a heat stroke victim with a core temperature in excess of 46.5 C. Ann Emerg Med. 1982.",
    15: "Mouse Heart Rate in a Human: Diagnostic Mystery of an Extreme Tachyarrhythmia. Indian Pacing Electrophysiol J. 2012. PMCID: PMC3273956.",
    18: "Guinness World Records. Lightest person. https://guinnessworldrecords.com/world-records/67485-lightest-person",
    19: "Extreme bradycardia: report of a case exhibiting a ventricular rate of less than twelve per minute. Am Heart J. 1948. doi:10.1016/0002-8703(48)90241-5.",
    20: "Steynor M, MacDuff A. Always consider the possibility of opioid induced respiratory depression in patients presenting with hypercapnic respiratory failure who fail to improve as expected with appropriate therapy. Case Rep Crit Care. 2015;2015:562319. doi:10.1155/2015/562319.",
}

# Límites por variable (rango de referencia y valores extremos documentados) en limits.csv,
# compartido con la figura en R. extreme_low/high vacío: sin valor extremo documentado.
# extreme_low_strict: el límite es "> extreme_low" (p. ej. > 0).
LIMITS_FILE = Path(__file__).resolve().parent / "limits.csv"


def load_limits(path: Path = LIMITS_FILE) -> pd.DataFrame:
    limits = pd.read_csv(path, dtype={"refs": str}, keep_default_na=False, na_values=[""])
    limits["extreme_low_strict"] = limits["extreme_low_strict"].astype(str).str.upper() == "TRUE"
    return limits

TITLE = (
    "Supplementary Table S2. Plausibility of measurements and laboratory values: values recorded in DiabetIA "
    "compared with reference ranges and with extreme values documented in the literature."
)
FOOTNOTE = (
    "Windows with value: % of the two-year windows with at least one visit. "
    "Recorded minimum and maximum are the lowest and highest values in any two-year window "
    "(BMI from the within-window median weight and height). Windows outside extreme values: windows whose minimum is "
    "below the lower limit or whose maximum is above the upper limit; values were flagged, not removed. "
    "“> 0”: no extreme low value is documented, so only values ≤ 0 are flagged. "
    "Urea limits were converted from BUN (urea = BUN × 2.14). "
    "Not documented: no extreme value is documented, so no values are flagged. References: {references}"
)


def _fmt(value: float, decimals: int = 2) -> str:
    return "–" if pd.isna(value) else f"{value:,.{decimals}f}".rstrip("0").rstrip(".")


def _limit(value, strict: bool = False) -> str:
    if pd.isna(value):
        return "Not documented"
    return f"> {_fmt(value, 3)}" if strict else _fmt(value, 3)


def plausibility(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula la Tabla S2: valores registrados frente a los valores extremos documentados."""
    df = df[has_visit(df)]
    df = df.assign(
        bmi_min=df["fn_weight_median"] / df["fn_height_median"] ** 2,
        bmi_max=df["fn_weight_median"] / df["fn_height_median"] ** 2,
    )
    rows = {}
    for row in load_limits().itertuples():
        low, high, low_strict = row.extreme_low, row.extreme_high, row.extreme_low_strict
        lo, hi = df[f"{row.column}_min"], df[f"{row.column}_max"]
        recorded = lo.notna() | hi.notna()
        below = False if pd.isna(low) else (lo <= low) if low_strict else (lo < low)
        above = False if pd.isna(high) else (hi > high)
        outside = recorded & (below | above)
        n = int(recorded.sum())
        rows[(row.group, f"{row.name} ({row.unit})")] = {
            "Windows with value, n (%)": f"{n:,} ({recorded.mean():.1%})",
            "Recorded minimum": _fmt(lo.min()),
            "Recorded maximum": _fmt(hi.max()),
            "Reference range": row.ref_label,
            "Extreme documented values (low – high)": f"{_limit(low, low_strict)} – {_limit(high)}",
            "Windows outside extreme values, n (%)": f"{int(outside.sum()):,} ({outside.sum() / n:.2%})" if n else "–",
            "Ref.": "–" if pd.isna(row.refs) else row.refs.replace(";", ", "),
        }
    result = pd.DataFrame(rows).T
    result.index.names = ["Variable", "Category"]
    return result


def write_validation(df: pd.DataFrame) -> None:
    """Genera results/supplementary/table_s2.{csv,html} a partir de los datos ya procesados."""
    SUPPLEMENTARY_DIR.mkdir(parents=True, exist_ok=True)
    result = plausibility(df)
    result.to_csv(SUPPLEMENTARY_DIR / "table_s2.csv")
    references = " ".join(f"{k}. {v}" for k, v in REFERENCES.items())
    save_word_table(result, SUPPLEMENTARY_DIR / "table_s2.html", TITLE, FOOTNOTE.format(references=references))
    print("Generado: results/supplementary/table_s2.csv y results/supplementary/table_s2.html")


def main() -> None:
    write_validation(process(load_data()))


if __name__ == "__main__":
    main()
