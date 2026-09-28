#!/usr/bin/env bash

set -euo pipefail

DESTINO="paquete"
SALIDA="lambda_iot.zip"

cd "$(dirname "$0")"
rm -rf "$DESTINO" "$SALIDA"
mkdir -p "$DESTINO"

echo "Instalando dependencias..."
# Se invoca pip como módulo de Python: en macOS el ejecutable `pip` a secas
# suele no existir fuera de un entorno virtual.
#
# `cryptography` es obligatorio aunque no se importe en el código: MySQL 8
# autentica con `caching_sha2_password`, y PyMySQL delega en esa librería el
# cifrado RSA del intercambio. Sin ella la conexión falla al autenticar.
#
# --platform y --only-binary fuerzan a descargar las ruedas compiladas para
# Linux x86_64, que es donde corre Lambda, en lugar de las del Mac.
python3 -m pip install \
  --target "$DESTINO" \
  --platform manylinux2014_x86_64 \
  --python-version 3.12 \
  --implementation cp \
  --only-binary=:all: \
  --upgrade \
  pymysql==1.1.1 \
  cryptography==44.0.0 \
  --quiet

echo "Copiando el código de la función..."
cp lambda_function.py "$DESTINO/"

echo "Comprimiendo..."
cd "$DESTINO"
zip -r "../$SALIDA" . -x '*.pyc' '*__pycache__*' > /dev/null
cd ..
rm -rf "$DESTINO"

echo
echo "Listo: $(pwd)/$SALIDA ($(du -h "$SALIDA" | cut -f1))"
echo "Súbelo desde la consola de Lambda en 'Upload from > .zip file'."
