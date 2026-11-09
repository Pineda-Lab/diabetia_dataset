"""Technical Validation: comparación externa con la ENSANUT 2018 de Michoacán (Tabla Suplementaria S9).

Prevalencia de DM2 e hipertensión (diagnóstico registrado) y de obesidad (IMC ≥ 30) en la ventana basal de
DiabetIA (Tabla 1), en adultos de 20 años o más, por grupo de edad y sexo, junto a las prevalencias de la
ENSANUT 2018 en Michoacán (diagnóstico médico previo reportado, y obesidad medida). Los valores de la ENSANUT
se copian del informe estatal (cuadros 4.15, 4.16 y 5.21).
"""

import pandas as pd

from process import load_data, process
from table1 import COMORBIDITIES, SUPPLEMENTARY_DIR, T2D, patient_level, save_word_table

TITLE = ("Supplementary Table S9. Prevalence of type 2 diabetes, hypertension and obesity in DiabetIA compared with "
         "the 2018 National Health and Nutrition Survey (ENSANUT) in Michoacán.")
FOOTNOTE = (
    "DiabetIA: patients aged 20 years or older at their baseline window (first two-year window with a visit, as in "
    "Table 1); diabetes and hypertension are diagnoses recorded in that window (ICD-10 E11 and I10), and obesity is "
    "BMI ≥30 kg/m² measured in that window (among patients with BMI). ENSANUT 2018, Michoacán: adults aged 20 years "
    "or older; diabetes and hypertension by previous medical diagnosis reported in the survey, and obesity measured "
    "(BMI ≥30 kg/m²); percentage (95% confidence interval), from Tables 4.15, 4.16 and 5.21 of the state report "
    "(Instituto Nacional de Salud Pública, 2020). DiabetIA describes people who attend IMSS primary care, not the "
    "general population, and its baseline windows span 2005–2018. – = not reported by age group."
)
AGE_GROUPS = {"20–39 years": (20, 39), "40–59 years": (40, 59), "60 years and older": (60, 200), "Total (20 years and older)": (20, 200)}

# ENSANUT 2018, Resultados de Michoacán (INSP, 2020): % (IC95%).
ENSANUT = {
    ("Type 2 diabetes", "Total"): {"20–39 years": "1.9 (1.0–3.6)", "40–59 years": "12.1 (9.2–15.6)",
                                   "60 years and older": "23.9 (19.0–29.7)", "Total (20 years and older)": "9.9 (8.5–11.6)"},
    ("Type 2 diabetes", "Women"): {"Total (20 years and older)": "11.8 (9.5–14.5)"},
    ("Type 2 diabetes", "Men"): {"Total (20 years and older)": "7.8 (6.1–9.9)"},
    ("Hypertension", "Total"): {"20–39 years": "8.0 (5.7–11.1)", "40–59 years": "20.1 (16.2–24.5)",
                                "60 years and older": "42.1 (35.7–48.7)", "Total (20 years and older)": "19.2 (16.9–21.6)"},
    ("Hypertension", "Women"): {"Total (20 years and older)": "23.7 (20.5–27.3)"},
    ("Hypertension", "Men"): {"Total (20 years and older)": "13.7 (11.1–16.9)"},
    ("Obesity", "Total"): {"Total (20 years and older)": "31.6 (26.5–37.3)"},
    ("Obesity", "Women"): {"Total (20 years and older)": "37.4 (29.0–46.7)"},
    ("Obesity", "Men"): {"Total (20 years and older)": "24.4 (19.2–30.5)"},
}


def _pct(mask: pd.Series) -> str:
    mask = mask.dropna()
    return f"{mask.mean():.1%}".replace("%", "") + f" (n={len(mask):,})" if len(mask) else "–"


def external_comparison(df: pd.DataFrame) -> pd.DataFrame:
    patients = patient_level(df, baseline="first")
    patients = patients[patients["age_at_wx"] >= 20]
    conditions = {
        "Type 2 diabetes": patients[T2D].astype(float),
        "Hypertension": patients[COMORBIDITIES["HTN (I10)"]].any(axis=1).astype(float),
        "Obesity": (patients["bmi"] >= 30).astype(float).where(patients["bmi"].notna()),
    }
    sexes = {"Total": patients.index == patients.index, "Women": patients["cs_sex"] == "F", "Men": patients["cs_sex"] == "M"}
    rows = []
    for condition, values in conditions.items():
        for sex, in_sex in sexes.items():
            for age, (low, high) in AGE_GROUPS.items():
                in_age = patients["age_at_wx"].between(low, high)
                if sex != "Total" and not age.startswith("Total"):
                    continue
                rows.append({
                    "Variable": condition,
                    "Category": f"{sex}, {age}" if sex != "Total" else age,
                    "DiabetIA, % (n)": _pct(values[in_sex & in_age]),
                    "ENSANUT 2018 Michoacán, % (95% CI)": ENSANUT.get((condition, sex), {}).get(age, "–"),
                })
    return pd.DataFrame(rows).set_index(["Variable", "Category"])


def write_external(df: pd.DataFrame) -> None:
    """Genera results/supplementary/table_s9.{csv,html}."""
    SUPPLEMENTARY_DIR.mkdir(parents=True, exist_ok=True)
    result = external_comparison(df)
    result.to_csv(SUPPLEMENTARY_DIR / "table_s9.csv")
    save_word_table(result, SUPPLEMENTARY_DIR / "table_s9.html", TITLE, FOOTNOTE)
    print("Generado: results/supplementary/table_s9.csv y results/supplementary/table_s9.html")


def main() -> None:
    write_external(process(load_data()))


if __name__ == "__main__":
    main()
