#!/usr/bin/env bash
# ==============================================================================
# Iniciar Carômetro Escolar com Backend, Frontend e HTTPS via Localtunnel
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "  Iniciando Carômetro Escolar"
echo "=========================================================="

# 1. Garante que o build de produção do frontend existe para o Django
if [ ! -f "$DIR/frontend/dist/frontend/browser/index.html" ]; then
    echo "Compilando frontend Angular pela primeira vez..."
    (cd "$DIR/frontend" && npm run build)
fi

# Lista de PIDs para encerrar ao sair
PIDS=()

cleanup() {
    echo ""
    echo "Encerrando Carômetro Escolar..."
    for pid in "${PIDS[@]}"; do
        kill -9 "$pid" 2>/dev/null || true
    done
    pkill -f "manage.py runserver 0.0.0.0:8000" 2>/dev/null || true
    pkill -f "ng serve" 2>/dev/null || true
    pkill -f "localtunnel.*sweet-hounds-flash" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 2. Inicia o backend Django na porta 8000
echo "Iniciando Backend (Django na porta 8000)..."
cd "$DIR/backend"
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
DJANGO_PID=$!
PIDS+=("$DJANGO_PID")

# 3. Inicia o frontend Angular na porta 4200 (servidor de desenvolvimento)
echo "Iniciando Frontend (Angular na porta 4200)..."
cd "$DIR/frontend"
npx ng serve --host 0.0.0.0 > /dev/null 2>&1 &
ANGULAR_PID=$!
PIDS+=("$ANGULAR_PID")

# 4. Aguarda os serviços ficarem online
echo "Aguardando inicialização dos serviços..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1 && curl -s http://127.0.0.1:4200/ > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Obtém a senha do túnel caso o localtunnel solicite na primeira tela
TUNNEL_PASSWORD=$(curl -s https://loca.lt/mytunnelpassword 2>/dev/null || echo "Consulte em https://loca.lt/mytunnelpassword")

echo ""
echo "=========================================================="
echo "  SISTEMA PRONTO PARA USO!"
echo "=========================================================="
echo "  Computador (Local):"
echo "    -> http://localhost:4200 (Frontend Angular)"
echo "    -> http://localhost:8000 (Django / Admin / API)"
echo ""
echo "  Celular (HTTPS):"
echo "    -> https://sweet-hounds-flash.loca.lt"
echo ""
echo "  IMPORTANTE PARA O CELULAR (Primeiro Acesso):"
echo "  Caso apareça uma tela do Localtunnel pedindo IP,"
echo "  digite: $TUNNEL_PASSWORD e clique em 'Continue'."
echo "=========================================================="
echo "Pressione Ctrl+C para encerrar todos os serviços."
echo ""

# 5. Inicia o túnel HTTPS apontando para a porta 8000 (que serve frontend e API unificados)
npx localtunnel --port 8000 --subdomain sweet-hounds-flash
