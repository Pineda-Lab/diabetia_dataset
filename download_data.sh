#!/usr/bin/env bash
# Descarga DiabetIA (versión del 17 de agosto de 2023) y su diccionario de datos desde el repositorio ENI Salud
# (https://repositorio-salud.conacyt.mx/jspui/handle/1000/296) a data/diabetia/, y verifica que los archivos
# sean los mismos con los que se generaron los resultados del manuscrito (SHA-256).
# Los archivos que ya existen y son válidos no se vuelven a descargar.
#
# Uso: ./download_data.sh
# Las bases de comparación (datos abiertos COVID-19 y Registro Nacional de Cáncer) se obtienen aparte (ver README).

set -euo pipefail
cd "$(dirname "$0")"

BASE="https://repositorio-salud.conacyt.mx/jspui/bitstream/1000/296"
DIR="data/diabetia"
CSV_SHA256="64ca90e8f480592182855b08754d514540b800e8f4a4394d018ea4802328e98e"
DICT_SHA256="17c6c5e0fcd3e67459711c933c612f90bfbd61d8601093fe23adf2a9ced288ba"

sha256() {
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi
}

valid() {  # archivo y SHA-256 esperado
    [ -f "$1" ] && [ "$(sha256 "$1")" = "$2" ]
}

mkdir -p "$DIR"

if valid "$DIR/data_dictionary.xlsx" "$DICT_SHA256"; then
    echo "==> $DIR/data_dictionary.xlsx ya está descargado"
else
    echo "==> Descargando el diccionario de datos"
    curl -fL --retry 3 -o "$DIR/data_dictionary.xlsx" "$BASE/4/data_dictionary.xlsx"
    valid "$DIR/data_dictionary.xlsx" "$DICT_SHA256" || { echo "El diccionario no coincide con la versión esperada" >&2; exit 1; }
fi

if valid "$DIR/hk_database.csv" "$CSV_SHA256"; then
    echo "==> $DIR/hk_database.csv ya está descargado"
else
    echo "==> Descargando DiabetIA (73 MB comprimido, 876 MB descomprimido)"
    tmp=$(mktemp -d)
    trap 'rm -rf "$tmp"' EXIT
    curl -fL --retry 3 -o "$tmp/hk_database.zip" "$BASE/5/hk_database_17ago2023.zip"
    unzip -o -q "$tmp/hk_database.zip" hk_database.csv -d "$DIR"
    valid "$DIR/hk_database.csv" "$CSV_SHA256" || { echo "hk_database.csv no coincide con la versión esperada" >&2; exit 1; }
fi

echo
echo "Listo. DiabetIA está en $DIR/"
