"""Tabla 2 del paper: comparación de DiabetIA con otras bases de datos clínicas.

Combina dos tipos de columnas:
  - Calculadas: resúmenes armonizados results/auxiliary/summary_*.csv (summary.py de cada carpeta).
  - Literatura: valores reportados en los artículos de descripción de cada base (LITERATURE).
"""

import pandas as pd

from table1 import AUXILIARY_DIR, MANUSCRIPT_DIR, RESULTS_DIR, save_word_table

# Columnas calculadas a partir de los datos: archivo de resumen -> nombre en la tabla.
COMPUTED = {
    "summary_diabetia.csv": "DiabetIA",
    "summary_registro_cancer.csv": "National Cancer Registry (Mexico)",
    "summary_covid_mx.csv": "COVID-19 Open Data (Mexico)",
}

# Columnas tomadas de la literatura: valores por (Variable, Category), según su referencia.
# "note" aclara en la nota al pie los valores que no tienen la misma definición que el resto.
LITERATURE = {
    # Recalde et al. 2022, Tabla 1, columna "Total since 2006" (p. e326).
    "SIDIAP": {
        "reference": "Recalde et al., Int J Epidemiol 2022 (doi:10.1093/ije/dyac068)",
        "values": {
            ("", "Patients"): "8,036,948",
            ("", "Collection years"): "2006–2021",
            ("Sex", "Female"): "4,029,112 (50.1%)",
            ("Sex", "Male"): "4,007,836 (49.9%)",
            ("Age (years)", "<18"): "1,245,702 (15.5%)",
            ("Age (years)", "18 – 64"): "4,912,030 (61.1%)",
            ("Age (years)", "65 and older"): "1,879,216 (23.4%)",
        },
        "note": "SIDIAP: all patients since 2006 (data as of 30 June 2021).",
    },
    # Wolf et al. 2019 (CPRD Aurum), Tabla 2 (p. 1740b).
    "CPRD": {
        "reference": "Wolf et al., Int J Epidemiol 2019 (doi:10.1093/ije/dyz034)",
        "values": {
            ("", "Patients"): "19,305,234",
            ("", "Records"): "738 general practices",
            ("", "Collection years"): "1995–2018",
            ("Sex", "Female"): "9,994,725 (51.8%)",
            ("Sex", "Male"): "9,309,928 (48.2%)",
            ("Age (years)", "<18"): "1,427,297 (20.0%)ᵃ",
            ("Age (years)", "18 – 64"): "4,463,385 (62.6%)ᵃ",
            ("Age (years)", "65 and older"): "1,235,104 (17.3%)ᵃ",
        },
        "note": "CPRD: CPRD Aurum as of September 2018; ᵃ age in 2018 among the 7,125,786 currently registered patients.",
    },
    # Johnson et al. 2023 (MIMIC-IV v2.2), Tabla 1, columna "Hospital admissions" (p. 3).
    "MIMIC-IV": {
        "reference": "Johnson et al., Sci Data 2023 (doi:10.1038/s41597-022-01899-x)",
        "values": {
            ("", "Patients"): "180,733",
            ("", "Records"): "431,231 hospital admissions (73,181 ICU stays)",
            ("", "Collection years"): "2008–2019",
            ("Sex", "Female"): "224,990 (52.2%)ᵇ",
            # No reportado: diferencia con el total de hospitalizaciones (sexo administrativo solo F/M).
            ("Sex", "Male"): "206,241 (47.8%)ᵇ",
        },
        "note": "MIMIC-IV: v2.2, adults (≥18 years) admitted to hospital; ᵇ percentage of hospital admissions (male derived as total minus female); "
                "age reported only as mean (SD) 58.8 (19.2) years.",
    },
}

COLUMN_ORDER = [
    "DiabetIA",
    "SIDIAP",
    "CPRD",
    "MIMIC-IV",
    "National Cancer Registry (Mexico)",
    "COVID-19 Open Data (Mexico)",
]

# Encabezado de cada columna en la tabla final, con el país de la base.
HEADERS = {
    "DiabetIA": "DiabetIA (Mexico)",
    "SIDIAP": "SIDIAP (Spain)",
    "CPRD": "CPRD (UK)",
    "MIMIC-IV": "MIMIC-IV (USA)",
}

# Características cualitativas (no salen de los datos): revisar contra las referencias.
CHARACTERISTICS = {
    "DiabetIA": {
        "Clinical focus": "Patient journeys",
        "Care setting": "Primary care / Outpatient",
        "Country": "Mexico (Michoacán)",
        "Design / Horizon": "Longitudinal",
        "Data standard": "OMOP CDM v5.4 (Tabular ext. available)",
        "Access": "Controlled (DUA)",
    },
    "SIDIAP": {
        "Clinical focus": "Population-wide primary care",
        "Care setting": "Primary care / Outpatient",
        "Country": "Spain (Catalonia)",
        "Design / Horizon": "Longitudinal",
        "Data standard": "Relational database (mapped to OMOP CDM)",
        "Access": "Controlled (public research institutions, project approval)",
    },
    "CPRD": {
        "Clinical focus": "Population-wide primary care",
        "Care setting": "Primary care / Outpatient",
        "Country": "United Kingdom (England)",
        "Design / Horizon": "Longitudinal",
        "Data standard": "SNOMED CT, Read v2 and EMIS codes",
        "Access": "Controlled (protocol approval, licence fee)",
    },
    "MIMIC-IV": {
        "Clinical focus": "Critical care monitoring",
        "Care setting": "ICU & Emergency / Inpatient",
        "Country": "United States (Boston, MA)",
        "Design / Horizon": "Longitudinal (per admission)",
        "Data standard": "Relational database (OMOP ext. available)",
        "Access": "Credentialed (training + PhysioNet DUA)",
    },
    "National Cancer Registry (Mexico)": {
        "Clinical focus": "Population-level cancer incidence",
        "Care setting": "Multi-center registry / Outpatient & Inpatient",
        "Country": "Mexico (9 population-based registries)",
        "Design / Horizon": "Cross-sectional",
        "Data standard": "Single-format / Tabular",
        "Access": "Transparency request",
    },
    "COVID-19 Open Data (Mexico)": {
        "Clinical focus": "Syndromic surveillance",
        "Care setting": "Multi-center registry / Outpatient",
        "Country": "Mexico (national)",
        "Design / Horizon": "Cross-sectional",
        "Data standard": "Single-format / Tabular",
        "Access": "Open",
    },
}

TITLE = "Table 2. Comparison of DiabetIA with other clinical databases and registries."
FOOTNOTE = (
    "Counts are n (%) relative to the patients (or records, when patients are not uniquely identified) of each database. "
    "DiabetIA: values from the first two-year window with a visit, as in Table 1; obesity = BMI ≥30. "
    "COVID-19 Open Data: suspected or confirmed cases, deduplicated by record ID; comorbidities as reported at intake. "
    "{literature} "
    "– = not available or not reported."
)

ROW_ORDER = [
    ("", "Patients"), ("", "Records"), ("", "Confirmed SARS-CoV-2"), ("", "Collection years"),
    ("Sex", "Female"), ("Sex", "Male"),
    ("Age (years)", "<18"), ("Age (years)", "18 – 64"), ("Age (years)", "65 and older"),
    ("Comorbidities", "Type 2 diabetes"), ("Comorbidities", "Hypertension"), ("Comorbidities", "Obesity"),
    ("Comorbidities", "Cardiovascular disease"),
]


def table2() -> pd.DataFrame:
    """Une las columnas calculadas y de literatura; lo que falte queda como "–"."""
    columns = {}
    for filename, name in COMPUTED.items():
        path = AUXILIARY_DIR / filename
        if path.exists():
            columns[name] = pd.read_csv(path, index_col=[0, 1], keep_default_na=False).iloc[:, 0]
        else:
            print(f"Falta {path.relative_to(RESULTS_DIR.parent)}: se deja vacía la columna {name}")
    for name, source in LITERATURE.items():
        columns[name] = pd.Series(source["values"], dtype=str)

    characteristics = list(next(iter(CHARACTERISTICS.values())))
    index = pd.MultiIndex.from_tuples([("", k) for k in characteristics] + ROW_ORDER, names=["Variable", "Category"])
    qualitative = pd.DataFrame({name: {("", k): v for k, v in rows.items()} for name, rows in CHARACTERISTICS.items()})
    data = pd.DataFrame(columns).reindex(columns=COLUMN_ORDER)
    result = data.combine_first(qualitative).reindex(index=index, columns=COLUMN_ORDER).fillna("–")
    return result.rename(columns=HEADERS)


def main() -> None:
    result = table2()
    MANUSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(MANUSCRIPT_DIR / "table2.csv")
    references = "; ".join(f"{name}: {source['reference']}" for name, source in LITERATURE.items())
    notes = " ".join(source["note"] for source in LITERATURE.values())
    footnote = FOOTNOTE.format(literature=f"Values reported in the literature ({references}). {notes}")
    save_word_table(result, MANUSCRIPT_DIR / "table2.html", TITLE, footnote)
    print("Generado: results/manuscript/table2.csv y results/manuscript/table2.html")


if __name__ == "__main__":
    main()
