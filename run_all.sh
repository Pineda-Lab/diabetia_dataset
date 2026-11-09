#!/usr/bin/env bash
# Ejecuta en orden todo el procesamiento y genera las tablas del paper en results/.
# Uso: ./run_all.sh
# Las bases de comparación que no estén en data/ se omiten; table2.py deja su columna con "–".

set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

run() {
    echo
    echo "==> $1"
    "$PYTHON" "$1"
}

run_if_data() {
    if [ -e "$2" ]; then
        run "$1"
    else
        echo
        echo "==> Se omite $1: no se encontró $2"
    fi
}

run diabetia/run.py
run_if_data covid_mx/summary.py data/covid-mx
run_if_data registro_cancer/summary.py data/registro-cancer/Mexico-RegistroNacionalCancer2020.xlsx
run diabetia/table2.py

echo
echo "Listo. Resultados en results/"
