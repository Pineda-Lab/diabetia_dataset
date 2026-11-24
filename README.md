# DiabetIA: analysis code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Manuscript: in preparation](https://img.shields.io/badge/manuscript-in%20preparation-orange.svg)](#citation)
[![Project: DiabetIA](https://img.shields.io/badge/project-pinedalab.ai%2Fdiabetia-green.svg)](https://pinedalab.ai/diabetia/)

Code to reproduce the tables and figures of the manuscript *DiabetIA: A Longitudinal Electronic Health Record Dataset for Diabetes Research from Mexico* (in preparation).

DiabetIA is a de-identified longitudinal dataset of primary care electronic health records from six family medicine units of the Mexican Institute of Social Security (IMSS) in Michoacán, Mexico (2005–2020), with 136,674 adult patients. This repository is part of the [DiabetIA project](https://pinedalab.ai/diabetia/) of the Pineda Lab (*Proyecto Insignia*). It contains **only code**; no patient-level data are included.

## How to run

Requires Python 3.9 or later. The figures also need R (≥ 4.1) with `data.table`, `ggplot2`, `scales` and `wesanderson`; without `Rscript`, `run_all.sh` skips them.

```bash
git clone https://github.com/Pineda-Lab/diabetia-insignia.git
cd diabetia-insignia
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run_all.sh              # everything; or ./run_all.sh summary | validation
```

`diabetia/run.py` reads the DiabetIA file once and writes all the Python tables. The R figures can be run on their own (`Rscript diabetia/figure_*.R`). `figure_patient.R` selects the patient of Figure 3 automatically, or accepts `--top N`, `--profiles` or patient identifiers to draw candidates in `results/patients/`. The comparison datasets are optional: if they are not in `data/`, their columns of Table 2 show "–".

The pipeline takes a few minutes (the COVID-19 files need several GB of RAM). Dependency versions are pinned in `requirements.txt`, and the scripts are deterministic. The manuscript results were produced with Python 3.9.6 on macOS.

## Data

Place the input files in `data/` (not versioned):

```
data/
├── diabetia/            hk_database.csv, data_dictionary.xlsx
├── covid-mx/            COVID19MEXICO*.csv (2020–2024)
└── registro-cancer/     Mexico-RegistroNacionalCancer2020.xlsx
```

| Dataset | Source and access |
|---|---|
| DiabetIA | National Informatics Ecosystem for Health (ENI Salud), <https://repositorio-salud.conacyt.mx/jspui/handle/1000/56>. Free download, without registration. |
| COVID-19 Open Data (Mexico) | Dirección General de Epidemiología, <https://www.gob.mx/salud/documentos/datos-abiertos-152127> |
| National Cancer Registry (Mexico) | Public information (transparency) request |

SIDIAP, CPRD Aurum and MIMIC-IV are not processed: their columns of Table 2 use the values published in their data descriptors (`LITERATURE` in `diabetia/table2.py`).

## Outputs

Results are written to `results/` (not versioned): `manuscript/` (figures named by their number, e.g. `figure_3_patient.png`; Figure 2 is the authors' diagram, `figure_2.svg`), `supplementary/`, `auxiliary/` (intermediate values cited in the text) and `patients/` (candidates for Figure 3).

| Manuscript | Script |
|---|---|
| Table 1 and Supplementary Table S1: characteristics by type 2 diabetes status | `diabetia/table1.py` |
| Table 2: comparison with other clinical databases and registries | `diabetia/table2.py` (summaries from `*/summary.py`) |
| Figure 1: selection of the cohort (attrition) | `diabetia/figure_attrition.R` |
| Figure 3: trajectory of one patient | `diabetia/figure_patient.R` |
| Figure 4: distributions of measurements and laboratory values | `diabetia/figure_validation.R` |
| Supplementary Table S2: plausibility | `diabetia/validation.py` |
| Supplementary Table S3: completeness | `diabetia/completeness.py` |
| Supplementary Table S7: internal consistency | `diabetia/consistency.py` |
| Supplementary Table S8 and Supplementary Figure S2: temporal coverage | `diabetia/temporal.py`, `diabetia/figure_temporal.R` |
| Supplementary Table S9: comparison with ENSANUT 2018 (Michoacán) | `diabetia/external.py` |
| Supplementary Figure S1: design of the windows | `diabetia/figure_windows.R` |
| Re-identification risk (k-anonymity) and cohort description | `diabetia/privacy.py`, `diabetia/cohort.py` |

The `.html` tables are formatted to be pasted into a word processor; the `.csv` files hold the same values. Supplementary Tables S4–S6 (extreme values, clinical categories and data records) are written directly in the Supplementary Material; the extreme values are also in `diabetia/limits.csv`. Code comments are in Spanish; variable names and outputs are in English.

## Definitions

- **Cohort.** The tabular release has 477,036 windows from 137,131 patients. The 457 patients without a care unit in any window are excluded, which leaves 136,674 patients and 475,924 windows.
- **Windows.** Two years of follow-up (`x_start`–`x_end`) and one outcome year (`y_start`–`y_end`). Successive windows start one year apart, so they overlap by one year. The 61,154 windows without a visit have no measurements; completeness and plausibility use the 414,770 windows with a visit.
- **Baseline (Table 1).** The first window with at least one visit. Age is `age_at_wx`, the age at `x_start`. BMI is the median weight over the squared median height. Vital signs are mean (SD) and biochemical values median (IQR) of the within-window medians.
- **Diagnoses.** ICD-10 codes recorded in the window: type 2 diabetes E11; complications E11.2–E11.5 (nephropathy, retinopathy, neuropathy, peripheral circulatory complications); hypertension I10; dyslipidemia E78; heart disease I20–I25, I50; stroke I60–I64, I69; neoplasms C00–D49. Obesity is BMI ≥30.
- **Figure 3.** The patient is chosen automatically among those with long follow-up and complete anthropometry. The figure shows no identifier or calendar dates, and age is given in a 5-year band.
- **Technical Validation.** Follows Kahn et al. (EGEMS 2016;4(1):1244): plausibility, completeness, consistency (25 rules) and temporal coverage. Values beyond the extreme limits (`diabetia/limits.csv`, Supplementary Table S4) are counted, not removed.
- **Comparison datasets.** Ages are grouped as <18, 18–64 and ≥65. COVID-19 records are deduplicated by `ID_REGISTRO` and are cases, not patients; the cancer registry has no patient identifier.

## Privacy

DiabetIA is de-identified but not anonymous: it keeps exact dates of birth and of care to allow longitudinal analyses. Users must not attempt to re-identify patients or to link the data with other sources. Outputs that list individual patients (`results/patients/`) are for internal use and must not be shared.

## Research team

- **Arturo López-Pineda, PhD**: Amphora Health; ENES Morelia, National Autonomous University of Mexico (UNAM)
- **Joaquin Tripp, BS, MS**: Amphora Health
- **Daniel Santana-Quinteros, BS, MS**: Amphora Health; Center for Mathematical Sciences (CCM), UNAM
- **Marisol Flores-Garrido, PhD**: ENES Morelia, UNAM
- **Luis M. García-Velázquez, PhD**: ENES Morelia, UNAM
- **Karina M. Figueroa-Mora, PhD**: Faculty of Physical and Mathematical Sciences "Mat. Luis Manuel Rivera Gutiérrez", UMSNH
- **Anel Gómez-García, PhD** (corresponding author): CIBIMI, Mexican Institute of Social Security (IMSS)
- **Cleto Alvarez-Aguilar, MD, MS** (corresponding author): Faculty of Medical and Biological Sciences "Dr. Ignacio Chávez", UMSNH

## Citation

If you use this code, please cite the manuscript (the full reference will be added upon publication):

> López-Pineda A, Tripp J, Santana-Quinteros D, Flores-Garrido M, García-Velázquez LM, Figueroa-Mora KM, Alvarez-Aguilar C, Gómez-García A. DiabetIA: A Longitudinal Electronic Health Record Dataset for Diabetes Research from Mexico. *In preparation.*

## Acknowledgements

Funded by the participating institutions and by CONAHCyT (now SECIHTI) through FORDECyT, National Strategic Programs (ProNacEs), registration 10410. Approved by the IMSS Ethics and Research Committees, protocol R-2018-785-051.

## License and contact

The code is released under the [MIT License](LICENSE); the datasets keep their own access terms. Questions about the code: [GitHub Issues](https://github.com/Pineda-Lab/diabetia-insignia/issues). Access to DiabetIA: ENI Salud. Contact: Dr. Arturo López-Pineda, arturolp@enesmorelia.unam.mx.
