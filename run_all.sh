#!/usr/bin/env bash
# Ejecuta en orden el procesamiento y genera las tablas y figuras del paper en results/
# (manuscript/, supplementary/, auxiliary/ y patients/). Las figuras del manuscrito llevan su número:
# figure_1_attrition, figure_3_patient y figure_4_validation (la Figura 2, figure_2.svg, es el diagrama de los autores).
#
# Uso: ./run_all.sh [summary|validation|all]
#   summary     Estadística descriptiva: Tablas 1, S1 y 2 (incluye las bases de comparación), Figuras 1 (atrición)
#               y 3 (trayectoria de un paciente) y Figura S1 (requiere R).
#   validation  Technical Validation: Tablas S2, S3, S7, S8 y S9, riesgo de reidentificación, Figura 4 y Figura S2
#               (requiere R).
#   all         Todo lo anterior (opción por defecto).
# Si falta data/diabetia/hk_database.csv, se descarga primero de ENI Salud con download_data.sh.
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
    summary|validation|all)
        if [ ! -f data/diabetia/hk_database.csv ]; then
            echo "==> Falta data/diabetia/hk_database.csv; se descarga de ENI Salud"
            ./download_data.sh
        fi
        ;;
esac

case "$MODE" in
    summary)
        run diabetia/run.py --only summary
        summary_tables
        run_r diabetia/figure_attrition.R
        run_r diabetia/figure_patient.R
        run_r diabetia/figure_windows.R
        ;;
    validation)
        run diabetia/run.py --only validation
        run_r diabetia/figure_validation.R
        run_r diabetia/figure_temporal.R
        ;;
    all)
        run diabetia/run.py
        summary_tables
        run_r diabetia/figure_attrition.R
        run_r diabetia/figure_patient.R
        run_r diabetia/figure_validation.R
        run_r diabetia/figure_temporal.R
        run_r diabetia/figure_windows.R
        ;;
    -h|--help)
        sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
        exit 0
        ;;
    *)
        echo "Opción no válida: $MODE (usa summary, validation o all)" >&2
        exit 1
        ;;
esac

echo
echo "Listo. Resultados en results/"
