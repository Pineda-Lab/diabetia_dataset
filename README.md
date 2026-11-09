# DiabetIA: analysis code

Code to reproduce the descriptive tables of the manuscript:

> López-Pineda A, Tripp J, Santana-Quinteros D, Flores-Garrido M, García-Velázquez LM, Figueroa-Mora KM, Alvarez-Aguilar C, Gómez-García A.
> **DiabetIA: An Open-Access Longitudinal Electronic Health Record Dataset for Diabetes Research from Mexico.** *(under review)*

DiabetIA is a de-identified longitudinal dataset of primary care electronic health records from six clinics of the Mexican Institute for Social Security (IMSS) in Michoacán, Mexico (2005–2020). It includes 136,674 adult patients.

This repository contains **only code**. No patient-level data are included.

## What this code produces

| Output | Manuscript | Script |
|---|---|---|
| `results/table1_first.{csv,html}` | Table 1: demographic, clinical and baseline biochemical characteristics, stratified by type 2 diabetes status | `diabetia/table1.py` |
| `results/table1_any.{csv,html}` | Sensitivity version of Table 1: diagnoses present in any window of follow-up | `diabetia/table1.py` |
| `results/table2.{csv,html}` | Table 2: comparison of DiabetIA with other clinical databases and registries | `diabetia/table2.py` |

The `.html` files are formatted to be pasted into a word processor. The `.csv` files hold the same values.

## Repository structure

```
.
├── diabetia/
│   ├── process.py        # Loads the DiabetIA tabular file and applies the cohort filter
│   ├── table1.py         # Table 1
│   ├── summary.py        # Harmonized summary of DiabetIA for Table 2
│   ├── table2.py         # Table 2 (computed columns + values reported in the literature)
│   └── run.py            # Runs table1.py and summary.py reading the dataset only once
├── covid_mx/
│   └── summary.py        # Harmonized summary of the Mexican COVID-19 open data
├── registro_cancer/
│   └── summary.py        # Harmonized summary of the Mexican National Cancer Registry
├── run_all.sh            # Runs the full pipeline in order
└── requirements.txt
```

Code comments are in Spanish; variable names and outputs are in English.

## Data

Place the input files in `data/` with the following layout. `data/` is excluded from version control.

```
data/
├── diabetia/
│   ├── hk_database.csv            # DiabetIA tabular release (one row per patient and two-year window)
│   └── data_dictionary.xlsx       # Data dictionary (520 variables)
├── covid-mx/
│   └── COVID19MEXICO*.csv         # Yearly files, 2020–2024
└── registro-cancer/
    └── Mexico-RegistroNacionalCancer2020.xlsx
```

| Dataset | Source and access |
|---|---|
| DiabetIA | National Informatics Ecosystem for Health (ENI Salud): <https://repositorio-salud.conacyt.mx/jspui/handle/1000/56>. Access requires training in research with human data and a Data Use Agreement. |
| COVID-19 Open Data (Mexico) | Secretaría de Salud, Dirección General de Epidemiología, open data: <https://www.gob.mx/salud/documentos/datos-abiertos-152127> |
| National Cancer Registry (Mexico) | Obtained through a public information (transparency) request. |

SIDIAP, CPRD and MIMIC-IV are not processed here. Their columns in Table 2 use the values published in their data descriptors (see `LITERATURE` in `diabetia/table2.py`, which cites the table and page of each value):

- SIDIAP: Recalde M et al. *Int J Epidemiol* 2022;51(6):e324–e336. doi:10.1093/ije/dyac068
- CPRD Aurum: Wolf A et al. *Int J Epidemiol* 2019;48(6):1740–1740g. doi:10.1093/ije/dyz034
- MIMIC-IV: Johnson AEW et al. *Sci Data* 2023;10:1. doi:10.1038/s41597-022-01899-x

## How to run

Requires Python 3.9 or later.

```bash
pip install -r requirements.txt
./run_all.sh
```

`run_all.sh` runs every step in order and skips the comparison datasets that are not present in `data/`. Table 2 is generated anyway, with "–" in their columns. Each script can also be run on its own:

```bash
python diabetia/run.py              # Table 1 and DiabetIA summary
python covid_mx/summary.py          # COVID-19 summary (reads ~3.5 GB; several GB of RAM)
python registro_cancer/summary.py   # Cancer registry summary
python diabetia/table2.py           # Table 2, from the summaries in results/
```

## Definitions

These are the definitions implemented in the code. They are also stated in the table footnotes.

**Cohort.** The tabular release has 477,036 rows (two-year windows) from 137,131 patients. Patients without a care unit recorded in any of their windows (457 patients, "sparse or irregular visit patterns" in the manuscript) are excluded. This leaves 136,674 patients and 475,924 windows.

**Baseline.** Each window has two years of follow-up (`x_start`–`x_end`) and one year for outcome assessment (`y_start`–`y_end`). Table 1 uses each patient's first window:

- Age is `age_at_wx`, the age at the end of the first follow-up period.
- BMI is the median weight divided by the squared median height within the window.
- Vital signs and biochemical values are the within-window medians, summarized as median (IQR) among patients with a recorded value.

**Groups (Table 1).**

- Type 2 diabetes (T2D): diagnosis code E11 in the first window.
- T2D with complications: any of E11.2 (nephropathy), E11.3 (retinopathy), E11.4 (neuropathy) or E11.5 (peripheral circulatory complications, reported as diabetic foot).

**Comorbidities.** Defined by ICD-10 diagnosis codes:

| Comorbidity | ICD-10 codes |
|---|---|
| Hypertension | I10 |
| Dyslipidemia | E78 |
| Heart or coronary disease | I20–I25, I50 |
| Stroke or cerebrovascular disease | I60–I64, I69 |
| Any neoplasm | C00–D49 |

Obesity is BMI ≥30. BMI categories are <18.5, 18.5–24.9, 25–29.9 and ≥30.

**Comparison datasets (Table 2).**

- Ages are grouped as <18, 18–64 and ≥65, the groups reported by SIDIAP, CPRD and MIMIC-IV.
- The yearly COVID-19 files overlap. Records are deduplicated by `ID_REGISTRO`, keeping the most recent update. Each record is a suspected or confirmed case, not a unique patient.
- The cancer registry has no patient identifier. Each row is an incident case.

## License

The code is released under the [MIT License](LICENSE). The license covers this code only, not the datasets. Each dataset keeps its own access terms (see [Data](#data)).

## Contact

Arturo López-Pineda: arturolp@enesmorelia.unam.mx
