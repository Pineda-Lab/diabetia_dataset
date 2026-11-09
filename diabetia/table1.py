"""Tabla 1 del paper: características demográficas, clínicas y basales.

Columnas: total, sin DM2, DM2 sin complicaciones y DM2 con complicaciones.
"""

from html import escape
from pathlib import Path

import numpy as np
import pandas as pd

from process import PATIENT_ID, ROOT, load_data, process

RESULTS_DIR = ROOT / "results"
MANUSCRIPT_DIR = RESULTS_DIR / "manuscript"        # tablas y figuras del manuscrito principal
SUPPLEMENTARY_DIR = RESULTS_DIR / "supplementary"  # tablas del material suplementario
AUXILIARY_DIR = RESULTS_DIR / "auxiliary"          # resúmenes y cálculos intermedios

TITLE = "Table 1. Demographic, clinical and baseline biochemical characteristics of the study population."
# La versión con diagnósticos en cualquier ventana va al Material Suplementario.
OUTPUTS = {
    "first": ("table1", TITLE),
    "any": (
        "table_s1",
        "Supplementary Table S1. Demographic, clinical and baseline biochemical characteristics of the study "
        "population, with diagnoses present in any window of follow-up.",
    ),
}
FOOTNOTE = (
    "T2D= Type 2 diabetes; HTN= Arterial hypertension; BMI= Body Mass Index. "
    "Underweight= BMI<18.5; Normal weight= BMI ≥18.5 and <25; Overweight= BMI ≥25 and <30; Obesity= BMI ≥30 (World Health Organization categories; see Supplementary Table S5). "
    "{baseline} "
    "T2D with complications= any diagnosis of E11.2, E11.3, E11.4 or E11.5. "
    "Categorical variables are n (%) relative to the total of each column. "
    "Continuous variables are median (interquartile range) of the patients with a recorded value (n)."
)
BASELINE_NOTE = {
    "first": "Age, BMI, vital signs, biochemical values and diagnoses were taken from the first two-year window of each patient.",
    "any": "Age, BMI, vital signs and biochemical values were taken from the first two-year window; "
           "diagnoses were present in any window of follow-up.",
}

T2D = "diabetes_mellitus_type_2"

# Complicaciones crónicas de DM2 que definen el grupo "con complicaciones".
COMPLICATIONS = {
    "Diabetic nephropathy (E11.2)": "type_2_diabetes_mellitus_with_renal_complications",
    "Diabetic retinopathy (E11.3)": "type_2_diabetes_mellitus_with_ophthalmic_complications",
    "Diabetic neuropathy (E11.4)": "type_2_diabetes_mellitus_with_neurological_complications",
    "Diabetic foot (E11.5)": "type_2_diabetes_mellitus_with_peripheral_circulatory_complications",
}

# Comorbilidades: cada una es la presencia de cualquiera de sus columnas de diagnóstico.
# EPOC, ERC, depresión y COVID-19 no tienen columna específica en la base
# (solo vienen agrupadas por capítulo CIE-10), por eso no se incluyen.
COMORBIDITIES = {
    "T2D (E11)": [T2D],
    "HTN (I10)": ["essential_(primary)_hypertension"],
    "Dyslipidemia (E78)": ["disorders_of_lipoprotein_metabolism_and_other_lipidemias"],
    "Heart or coronary disease (I20–I25, I50)": [
        "angina_pectoris",
        "acute_myocardial_infarction",
        "subsequent_myocardial_infarction",
        "certain_complications_present_after_acute_myocardial_infarction",
        "other_acute_ischemic_heart_diseases",
        "chronic_ischemic_heart_disease",
        "heart_failure",
    ],
    "Stroke or cerebrovascular disease (I60–I64, I69)": [
        "subarachnoid_hemorrhage",
        "intraencephalic_hemorrhage",
        "other_non_traumatic_intracranial_hemorrhages",
        "cerebral_stroke",
        "acute_cerebrovascular_accident_not_specified_as_hemorrhagic_or_ischemic",
        "sequelae_of_cerebrovascular_disease",
    ],
    "Any neoplasm (C00–D49)": ["tumors_(neoplasms)"],
}

# Variables continuas de la primera ventana (mediana por ventana): etiqueta -> (columna, decimales).
VITAL_SIGNS = {
    "Systolic blood pressure (mmHg)": ("fn_ta_systolic_median", 0),
    "Diastolic blood pressure (mmHg)": ("fn_ta_diastolic_median", 0),
}
BIOCHEMICAL = {
    "Fasting glucose (mg/dL)": ("fn_fasting_glucose_median", 0),
    "Blood glucose (mg/dL)": ("in_glucose_median", 0),
    "HbA1c (%)": ("fn_hemoglobin_median", 1),
    "Triglycerides (mg/dL)": ("fn_triglycerides_median", 0),
    "Total cholesterol (mg/dL)": ("fn_cholesterol_median", 0),
    "Creatinine (mg/dL)": ("fn_creatinine_median", 2),
    "Urea (mg/dL)": ("fn_urea_median", 1),
    "Uric acid (mg/dL)": ("fn_aurico_median", 1),
}
CONTINUOUS = {**VITAL_SIGNS, **BIOCHEMICAL}

GROUPS = ["Total", "Without T2D", "T2D without complications", "T2D with complications"]

BMI_BINS = [-np.inf, 18.5, 25, 30, np.inf]
BMI_LABELS = ["Underweight", "Normal weight", "Overweight", "Obesity (any class)"]

AGE_BINS = [-np.inf, 44, 64, np.inf]
AGE_LABELS = ["18 – 44", "45 - 64", "65 and older"]


def patient_level(df: pd.DataFrame, baseline: str = "first") -> pd.DataFrame:
    """Resume las ventanas a un renglón por paciente.

    Demografía, edad e IMC siempre vienen de la primera ventana.
    Los diagnósticos dependen de `baseline`:
      - "first": presentes en la primera ventana (corte basal; reproduce el manuscrito).
      - "any": presentes en cualquier ventana del paciente (prevalencia durante el seguimiento).
    """
    if baseline not in ("first", "any"):
        raise ValueError("baseline debe ser 'first' o 'any'")

    dx_cols = list(COMPLICATIONS.values()) + [c for cols in COMORBIDITIES.values() for c in cols]

    first = df.sort_values("window").groupby(PATIENT_ID).first()
    continuous_cols = [col for col, _ in CONTINUOUS.values()]
    patients = first[["cs_sex", "age_at_wx", "fn_weight_median", "fn_height_median"] + continuous_cols].copy()
    if baseline == "first":
        patients[dx_cols] = first[dx_cols] > 0
    else:
        patients[dx_cols] = df.groupby(PATIENT_ID)[dx_cols].max() > 0

    patients["bmi"] = patients["fn_weight_median"] / patients["fn_height_median"] ** 2
    has_comp = patients[list(COMPLICATIONS.values())].any(axis=1)
    patients["group"] = np.select(
        [patients[T2D] & has_comp, patients[T2D]],
        [GROUPS[3], GROUPS[2]],
        default=GROUPS[1],
    )
    return patients


def _count(mask: pd.Series) -> str:
    """Celda categórica: "n (%)" sobre el total de la columna."""
    return f"{int(mask.sum()):,} ({mask.mean():.2%})"


def _median_iqr(values: pd.Series, decimals: int) -> str:
    """Celda continua: "mediana (Q1–Q3); n=" con los pacientes que tienen valor."""
    values = values.dropna()
    if values.empty:
        return "–"
    q1, med, q3 = values.quantile([0.25, 0.5, 0.75])
    return f"{med:,.{decimals}f} ({q1:,.{decimals}f}–{q3:,.{decimals}f}); n={len(values):,}"


def table1(df: pd.DataFrame, baseline: str = "first") -> pd.DataFrame:
    """Calcula la Tabla 1: "n (%)" para categóricas y "mediana (RIC); n" para continuas."""
    patients = patient_level(df, baseline)
    columns = {GROUPS[0]: patients}
    columns.update({g: patients[patients["group"] == g] for g in GROUPS[1:]})

    def cells(p: pd.DataFrame) -> dict:
        bmi = pd.cut(p["bmi"], BMI_BINS, labels=BMI_LABELS, right=False)
        age = pd.cut(p["age_at_wx"], AGE_BINS, labels=AGE_LABELS)
        rows = {
            ("", "N"): f"{len(p):,}",
            ("Sex", "Female"): _count(p["cs_sex"] == "F"),
            ("Sex", "Male"): _count(p["cs_sex"] == "M"),
        }
        rows.update({("BMI (Weight kg/Height m2)", b): _count(bmi == b) for b in BMI_LABELS})
        rows.update({("Age at first window (years)", a): _count(age == a) for a in AGE_LABELS})
        rows.update({("Comorbidities", name): _count(p[cols].any(axis=1)) for name, cols in COMORBIDITIES.items()})
        rows.update({("Chronic complications", name): _count(p[col]) for name, col in COMPLICATIONS.items()})
        rows.update({("Vital signs", name): _median_iqr(p[col], dec) for name, (col, dec) in VITAL_SIGNS.items()})
        rows.update({("Biochemical", name): _median_iqr(p[col], dec) for name, (col, dec) in BIOCHEMICAL.items()})
        return rows

    table = {group: cells(p) for group, p in columns.items()}
    result = pd.DataFrame(table)
    result.index = pd.MultiIndex.from_tuples(result.index, names=["Variable", "Category"])
    return result


def save_word_table(table: pd.DataFrame, path: Path, title: str, footnote: str) -> None:
    """Guarda la tabla como HTML para abrir en el navegador y copiar/pegar en Word."""
    cell = "padding:2pt 6pt;"
    header = "".join(f'<th style="{cell}text-align:center;">{escape(c)}</th>' for c in table.columns)
    rows = []
    for variable, block in table.groupby(level="Variable", sort=False):
        if variable:
            rows.append(f'<tr><td colspan="{len(table.columns) + 1}" style="{cell}font-weight:bold;">{escape(variable)}</td></tr>')
        for (_, category), values in block.iterrows():
            label = f"&nbsp;&nbsp;&nbsp;{escape(category)}" if variable else f"<b>{escape(category)}</b>"
            cells = "".join(f'<td style="{cell}text-align:center;">{escape(v)}</td>' for v in values)
            rows.append(f'<tr><td style="{cell}">{label}</td>{cells}</tr>')

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Table 1</title></head>
<body style="font-family:'Times New Roman',serif;font-size:10pt;">
<p><b>{escape(title)}</b></p>
<table style="border-collapse:collapse;border-top:1.5pt solid black;border-bottom:1.5pt solid black;font-size:10pt;">
<thead><tr style="border-bottom:1pt solid black;"><th style="{cell}"></th>{header}</tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody>
</table>
<p style="font-size:9pt;">{escape(footnote)}</p>
</body></html>
"""
    path.write_text(html, encoding="utf-8")


def write_table1(df: pd.DataFrame) -> None:
    """Genera results/manuscript/table1.{csv,html} y results/supplementary/table_s1.{csv,html}."""
    for baseline, (name, title) in OUTPUTS.items():
        out_dir = SUPPLEMENTARY_DIR if name.startswith("table_s") else MANUSCRIPT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        result = table1(df, baseline)
        result.to_csv(out_dir / f"{name}.csv")
        footnote = FOOTNOTE.format(baseline=BASELINE_NOTE[baseline])
        save_word_table(result, out_dir / f"{name}.html", title, footnote)
        print(f"Generado: {(out_dir / name).relative_to(ROOT)}.{{csv,html}}")


def main() -> None:
    write_table1(process(load_data()))


if __name__ == "__main__":
    main()
