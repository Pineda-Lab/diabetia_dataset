#!/usr/bin/env bash
# Ejecuta en orden el procesamiento y genera las tablas y figuras del paper en results/
# (manuscript/, supplementary/, auxiliary/ y patients/).
#
# Uso: ./run_all.sh [summary|validation|all]
#   summary     Estadística descriptiva: Tablas 1, S1 y 2 (incluye las bases de comparación) y Figura 2
#               (trayectoria de un paciente; requiere R).
#   validation  Technical Validation: Tablas S2, S3, S7 y S8 y figuras (requiere R).
#   all         Todo lo anterior (opción por defecto).
# Las bases de comparación que no estén en data/ se omiten; table2.py deja su columna con "–".

set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
MODE="${1:-all}"

run() {
    echo
    echo "==> $*"
    "$PYTHON" "$@"
}

run_if_data() {
    if [ -e "$2" ]; then
        run "$1"
    else
        echo
        echo "==> Se omite $1: no se encontró $2"
    fi
}

run_r() {
    echo
    if command -v Rscript >/dev/null 2>&1; then
        echo "==> $1"
        Rscript "$1"
    else
        echo "==> Se omite $1: no se encontró Rscript"
    fi
}

summary_tables() {
    run_if_data covid_mx/summary.py data/covid-mx
    run_if_data registro_cancer/summary.py data/registro-cancer/Mexico-RegistroNacionalCancer2020.xlsx
    run diabetia/table2.py
}

case "$MODE" in
    summary)
        run diabetia/run.py --only summary
        summary_tables
        run_r diabetia/figure_patient.R
        ;;
    validation)
        run diabetia/run.py --only validation
        run_r diabetia/figure_validation.R
        run_r diabetia/figure_temporal.R
        ;;
    all)
        run diabetia/run.py
        summary_tables
        run_r diabetia/figure_patient.R
        run_r diabetia/figure_validation.R
        run_r diabetia/figure_temporal.R
        ;;
    -h|--help)
        sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'
        exit 0
        ;;
    *)
        echo "Opción no válida: $MODE (usa summary, validation o all)" >&2
        exit 1
        ;;
esac

echo
echo "Listo. Resultados en results/"
