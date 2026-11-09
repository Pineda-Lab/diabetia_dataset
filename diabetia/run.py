"""Lee hk_database.csv una sola vez y genera las tablas de DiabetIA.

Uso: python diabetia/run.py [--only summary|validation]
  summary     Tablas 1 y S1 (estadística descriptiva) y el resumen para la Tabla 2.
  validation  Technical Validation: Tablas S2 (plausibilidad), S3 (completitud), S7 (consistencia)
              S8 (cobertura temporal) y S9 (comparación con la ENSANUT), riesgo de reidentificación (k-anonimato)
              y descripción de la cohorte (ventanas, seguimiento y edad).
Sin --only se generan todas.
"""

import argparse

from cohort import write_cohort
from completeness import write_completeness
from consistency import write_consistency
from external import write_external
from privacy import write_privacy
from process import load_data, process
from summary import write_summary
from table1 import write_table1
from temporal import write_temporal
from validation import write_validation


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera las tablas de DiabetIA leyendo la base una sola vez.")
    parser.add_argument("--only", choices=["summary", "validation"], help="genera solo un grupo de tablas")
    args = parser.parse_args()

    df = process(load_data())
    if args.only in (None, "summary"):
        write_table1(df)
        write_summary(df)
    if args.only in (None, "validation"):
        write_validation(df)
        write_completeness(df)
        write_consistency(df)
        write_temporal(df)
        write_privacy(df)
        write_external(df)
        write_cohort(df)


if __name__ == "__main__":
    main()
