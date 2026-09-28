#!/usr/bin/env bash

set -euo pipefail

DESTINO="paquete"
SALIDA="lambda_iot.zip"

cd "$(dirname "$0")"
rm -rf "$DESTINO" "$SALIDA"
mkdir -p "$DESTINO"

echo "Instalando dependencias..."
pip install \
  --target "$DESTINO" \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --only-binary=:all: \
  --upgrade \
  pymysql==1.1.1 \
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
