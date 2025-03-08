#!/usr/bin/env bash
# exit on error
set -o errexit

# Instala dependências do sistema necessárias
apt-get update -y
apt-get install -y python3-dev gcc build-essential

# Atualiza pip e instala dependências Python
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt