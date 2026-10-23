#!/usr/bin/env bash
set -e

echo "==> Compilando frontend Angular..."
cd frontend
npm ci
npm run build
cd ..

echo "==> Instalando dependências Python..."
pip install -r backend/requirements.txt

echo "==> Rodando migrations..."
cd backend
python manage.py migrate --no-input

echo "==> Populando dados iniciais..."
python manage.py seed

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

echo "==> Build concluído!"
