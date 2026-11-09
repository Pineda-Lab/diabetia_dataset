# DiabetIA: analysis code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Manuscript: in preparation](https://img.shields.io/badge/manuscript-in%20preparation-orange.svg)](#citation)
[![Project: DiabetIA](https://img.shields.io/badge/project-pinedalab.ai%2Fdiabetia-green.svg)](https://pinedalab.ai/diabetia/)

Code to reproduce the tables and figures of the manuscript (descriptive statistics and Technical Validation):

> López-Pineda A, Tripp J, Santana-Quinteros D, Flores-Garrido M, García-Velázquez LM, Figueroa-Mora KM, Alvarez-Aguilar C, Gómez-García A.
> **DiabetIA: An Open-Access Longitudinal Electronic Health Record Dataset for Diabetes Research from Mexico.** *(in preparation)*

DiabetIA is a de-identified longitudinal dataset of primary care electronic health records from six clinics of the Mexican Institute for Social Security (IMSS) in Michoacán, Mexico (2005–2020). It includes 136,674 adult patients.

This repository is part of the [DiabetIA project](https://pinedalab.ai/diabetia/) of the Pineda Lab, under the subproject *Flagship Project to Describe the Repository* (*Proyecto Insignia*). It contains **only code**. No patient-level data are included.

## What this code produces

Outputs are written to four subfolders of `results/` (not versioned): `manuscript/` (tables and figures of the main text), `supplementary/` (Supplementary Tables), `auxiliary/` (summaries and intermediate values) and `patients/` (candidate patients for Figure 2).

| Output | Manuscript | Script |
|---|---|---|
| `results/manuscript/table1.{csv,html}` | Table 1: demographic, clinical and baseline biochemical characteristics, stratified by type 2 diabetes status | `diabetia/table1.py` |
| `results/manuscript/table2.{csv,html}` | Table 2: comparison of DiabetIA with other clinical databases and registries | `diabetia/table2.py` |
| `results/manuscript/figure_patient.{pdf,png}` | Figure 2: longitudinal trajectory of one patient (diagnoses, BMI, blood pressure, glucose, prescriptions and visits) | `diabetia/figure_patient.R` |
| `results/manuscript/figure_validation.{pdf,png}` | Figure 3: distributions of the measurements and laboratory values | `diabetia/figure_validation.R` |
| `results/supplementary/table_s1.{csv,html}` | Supplementary Table S1: Table 1 with diagnoses present in any window of follow-up | `diabetia/table1.py` |
| `results/supplementary/table_s2.{csv,html}` | Supplementary Table S2: plausibility, recorded minimum and maximum values versus reference ranges and extreme values documented in the literature | `diabetia/validation.py` |
| `results/supplementary/table_s3.{csv,html}` | Supplementary Table S3: completeness of each variable by window, type 2 diabetes status and patient | `diabetia/completeness.py` |
| `results/supplementary/table_s7.{csv,html}` | Supplementary Table S7: internal consistency of dates, ages, diagnoses and window structure | `diabetia/consistency.py` |
| `results/supplementary/table_s8.{csv,html}` | Supplementary Table S8: temporal coverage by care unit | `diabetia/temporal.py` |
| `results/supplementary/table_s9.{csv,html}` | Supplementary Table S9: prevalence of T2D, hypertension and obesity compared with ENSANUT 2018 (Michoacán) | `diabetia/external.py` |
| `results/supplementary/figure_windows.{pdf,png}` | Supplementary Figure S1: design of the overlapping two-year windows (schematic, no patient data) | `diabetia/figure_windows.R` |
| `results/supplementary/figure_temporal.{pdf,png}` | Supplementary Figure S2: completeness of each variable by year of window start | `diabetia/figure_temporal.R` |

The `.html` files are formatted to be pasted into a word processor. The `.csv` files hold the same values. Supplementary Table S4 (reference ranges and extreme documented values, also in `diabetia/limits.csv`), Supplementary Table S5 (clinical categories and reference values) and Supplementary Table S6 (data records) are written directly in the Supplementary Material.

Auxiliary outputs used in the text and figures:

| Output | Content | Script |
|---|---|---|
| `results/auxiliary/summary_*.csv` | Harmonized summaries of each database, read by `table2.py` | `*/summary.py` |
| `results/auxiliary/figure_validation_stats.csv` | n, mean, SD, P25, median, P75 and values outside the plotted range for each variable of Figure 3 | `diabetia/figure_validation.R` |
| `results/auxiliary/temporal_coverage.csv` | Windows, patients and completeness of each variable by year of window start (data of Supplementary Figure S2) | `diabetia/temporal.py` |
| `results/auxiliary/reidentification_risk.csv` | k-anonymity of the quasi-identifiers (sex, date or year of birth, care unit, dates of first and last visit) | `diabetia/privacy.py` |
| `results/auxiliary/cohort_checks.csv` | Cohort description for Methods: windows per patient, follow-up between first and last visit, minimum ages | `diabetia/cohort.py` |
| `results/auxiliary/visit_counts.csv` | Visits summed over windows and lower bound without the overlap between successive windows | `diabetia/consistency.py` |

## Repository structure

```
.
├── diabetia/
│   ├── process.py        # Loads the DiabetIA tabular file and applies the cohort filter
│   ├── table1.py         # Table 1
│   ├── summary.py        # Harmonized summary of DiabetIA for Table 2
│   ├── table2.py         # Table 2 (computed columns + values reported in the literature)
│   ├── validation.py     # Technical Validation: plausibility of recorded values (Table S2)
│   ├── completeness.py   # Technical Validation: completeness of each variable (Table S3)
│   ├── consistency.py    # Technical Validation: internal consistency (Table S7)
│   ├── temporal.py       # Technical Validation: temporal coverage (Table S8, data for the temporal figure)
│   ├── limits.csv        # Reference ranges and extreme documented values (Tables S2 and S4, Figure 3)
│   ├── figure_patient.R     # Figure 2: trajectory of one patient (R, ggplot2)
│   ├── figure_validation.R  # Figure 3: distributions (R, ggplot2)
│   ├── external.py       # Technical Validation: comparison with ENSANUT 2018 (Table S9)
│   ├── privacy.py        # Re-identification risk (k-anonymity of quasi-identifiers)
│   ├── cohort.py         # Cohort description (windows per patient, follow-up, ages)
│   ├── figure_windows.R     # Supplementary Figure S1: window design (R, ggplot2)
│   ├── figure_temporal.R    # Supplementary Figure S2: temporal coverage (R, ggplot2)
│   └── run.py            # Runs the Python tables and checks above reading the dataset only once
├── covid_mx/
│   └── summary.py        # Harmonized summary of the Mexican COVID-19 open data
├── registro_cancer/
│   └── summary.py        # Harmonized summary of the Mexican National Cancer Registry
├── run_all.sh            # Runs the full pipeline in order
├── requirements.txt      # Pinned dependencies
└── LICENSE               # MIT License
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

Requires Python 3.9 or later. Figures 2 and 3 and Supplementary Figures S1 and S2 also need R (≥ 4.1) with `data.table`, `ggplot2`, `scales` and `wesanderson`; if `Rscript` is not found, `run_all.sh` skips them. Using a virtual environment is recommended:

```bash
git clone https://github.com/Pineda-Lab/diabetia-insignia.git
cd diabetia-insignia
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run_all.sh
```

`./run_all.sh summary` generates the descriptive tables (1, S1 and 2) and Figure 2, `./run_all.sh validation` the Technical Validation tables (S2, S3, S7–S9), the re-identification risk, the cohort description and figures, and `./run_all.sh` or `./run_all.sh all` everything. `run_all.sh` runs every step in order and skips the comparison datasets that are not present in `data/`. Table 2 is generated anyway, with "–" in their columns. Each script can also be run on its own:

```bash
python diabetia/run.py              # Tables 1, S1–S3 and S7–S9, DiabetIA summary, re-identification risk and cohort description
Rscript diabetia/figure_patient.R     # Figure 2 (reads the DiabetIA file again)
Rscript diabetia/figure_patient.R --top 3          # 3 best candidates: patients/figure_patient_<cx_curp>.{pdf,png} + patients/figure_patient_candidates.csv
Rscript diabetia/figure_patient.R --profiles       # one patient per clinical profile: patients/figure_patient_<profile>_<cx_curp>.{pdf,png}
Rscript diabetia/figure_patient.R <cx_curp> [...]  # specific patients: patients/figure_patient_<cx_curp>.{pdf,png}
Rscript diabetia/figure_validation.R  # Figure 3 (reads the DiabetIA file again)
Rscript diabetia/figure_windows.R     # Supplementary Figure S1 (schematic, no data needed)
Rscript diabetia/figure_temporal.R    # Supplementary Figure S2 (from results/auxiliary/temporal_coverage.csv)
python covid_mx/summary.py          # COVID-19 summary (reads ~3.5 GB; several GB of RAM)
python registro_cancer/summary.py   # Cancer registry summary
python diabetia/table2.py           # Table 2, from the summaries in results/auxiliary/
```

### Reproducibility

- Dependency versions are pinned in `requirements.txt`.
- The results in the manuscript were produced with Python 3.9.6 on macOS.
- The full pipeline takes a few minutes. Reading the COVID-19 files dominates the runtime and needs several GB of RAM.
- The scripts are deterministic: they involve no sampling or random seeds, so the same input files give the same tables.

## Definitions

These are the definitions implemented in the code. They are also stated in the table footnotes.

**Cohort.** The tabular release has 477,036 rows (two-year windows) from 137,131 patients. Patients without a care unit recorded in any of their windows (457 patients, "sparse or irregular visit patterns" in the manuscript) are excluded. This leaves 136,674 patients and 475,924 windows.

**Windows.** Each window has two years of follow-up (`x_start`–`x_end`) and one year for outcome assessment (`y_start`–`y_end`). Successive windows of a patient start one year apart, so consecutive windows overlap by one year. Because of this overlap, summing `count_cx_w` over windows counts most visits twice; `visit_counts.csv` reports that sum and a lower bound without the overlap. 61,154 windows (12.9%) have no visit (no care unit and no visit count) and no measurements; completeness (Table S3) and plausibility (Table S2) are computed over the 414,770 windows with a visit.

**Baseline.** Table 1 uses each patient's baseline window: the first window with at least one visit. All variables come from that same window (not the first non-missing value of each column):

- Age is `age_at_wx`, the age at the start of the window (`x_start`). The data dictionary describes it as the age at `x_end`, but the dates show it is the age at `x_start`.
- BMI is the median weight divided by the squared median height within the window.
- Vital signs and biochemical values are the within-window medians. Vital signs are summarized as mean (SD), because terminal digit preference makes their median and IQR uninformative; biochemical values as median (IQR). Both among patients with a recorded value.

**Groups (Table 1).**

- Type 2 diabetes (T2D): diagnosis code E11 in the baseline window.
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

**Patient trajectory (Figure 2).** Unless a `cx_curp` is given, the patient is selected automatically among those with ≥ 8 windows and BMI in ≥ 80% of them, maximizing the number of windows, a T2D diagnosis during follow-up, a chronic complication, windows with glucose and drug groups prescribed. To protect privacy, the figure shows no identifier or calendar dates: time is in years since the start of follow-up and age is given in a 5-year band. The identifier is only printed in the console.

**Technical Validation.** The checks follow the data quality framework of Kahn et al. (EGEMS 2016;4(1):1244).

- *Plausibility (Table S2, Figure 3):* each window's minimum and maximum are compared with the extreme values documented in the literature (`limits.csv`). Values beyond them are counted, not removed. Figure 3 shows the within-window medians with their median and interquartile range, limited to the 0.5th–99.5th percentiles.
- *Completeness (Table S3):* a variable is recorded in a window when its within-window median is not missing (BMI needs weight and height). Windows are grouped by the diagnoses recorded up to that window; diagnosis columns behave cumulatively.
- *Consistency (Table S7):* 25 rules on the order and length of the periods, age versus date of birth, care unit versus visits, sex-specific diagnoses (E28, E29), window numbering and spacing, and the year and age of T2D diagnosis.
- *Temporal coverage (Table S8, Supplementary Figure S2):* windows, patients and completeness by year of window start and by care unit.

**Comparison datasets (Table 2).**

- Ages are grouped as <18, 18–64 and ≥65, the groups reported by SIDIAP, CPRD and MIMIC-IV.
- The yearly COVID-19 files overlap. Records are deduplicated by `ID_REGISTRO`, keeping the most recent update. Each record is a suspected or confirmed case, not a unique patient.
- The cancer registry has no patient identifier. Each row is an incident case.

## Project status

| Component | Status |
|---|---|
| Table 1 (DiabetIA, stratified by T2D) | Done |
| Table 2 (comparison with other databases) | Done; MIMIC-IV currently uses published values |
| Technical Validation: plausibility, completeness, consistency and temporal coverage (Tables S2, S3, S7, S8; Figure 3; Supplementary Figure S2) | Done |
| Extreme limits for minimum weight, minimum heart rate and respiratory rate (`limits.csv`) | Pending clinical validation |

## Research team

- **Anel Gómez-García, PhD**: Biomedical Research Center of Michoacán (CIBIMI), Mexican Institute for Social Security (IMSS)
- **Arturo López-Pineda, PhD**: National School of Higher Studies, Morelia Campus (ENES Morelia), National Autonomous University of Mexico (UNAM); Amphora Health
- **Cleto Alvarez-Aguilar, MD, MS**: Faculty of Medical and Biological Sciences "Dr. Ignacio Chávez", Universidad Michoacana de San Nicolás de Hidalgo (UMSNH)
- **Karina M. Figueroa-Mora, PhD**: Faculty of Physical and Mathematical Sciences "Mat. Luis Manuel Rivera Gutiérrez", UMSNH
- **Marisol Flores-Garrido, PhD**: ENES Morelia, UNAM
- **Luis M. García-Velázquez, PhD**: ENES Morelia, UNAM

More about the project, its team and its other subprojects: <https://pinedalab.ai/diabetia/>.

## Citation

If you use this code, please cite the manuscript:

> López-Pineda A, Tripp J, Santana-Quinteros D, Flores-Garrido M, García-Velázquez LM, Figueroa-Mora KM, Alvarez-Aguilar C, Gómez-García A.
> DiabetIA: An Open-Access Longitudinal Electronic Health Record Dataset for Diabetes Research from Mexico. *In preparation.*

The full reference will be added here upon publication.

## Acknowledgements

- **Funding:** participating institutions, and the National Council of Science, Humanities and Technology (CONAHCyT) through FORDECyT under the National Strategic Programs (ProNacEs), registration number 10410.
- **Ethics:** the study was approved by the IMSS Ethics and Research Committees, protocol R-2018-785-051.

## Contributing and issues

Questions about the code, or problems reproducing the tables, can be reported through [GitHub Issues](https://github.com/Pineda-Lab/diabetia-insignia/issues). Questions about access to the DiabetIA dataset should go through ENI Salud (see [Data](#data)).

## License

The code is released under the [MIT License](LICENSE). The license covers this code only, not the datasets. Each dataset keeps its own access terms (see [Data](#data)).

## Contact

Arturo López-Pineda: arturolp@enesmorelia.unam.mx
