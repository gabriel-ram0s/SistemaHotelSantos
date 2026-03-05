#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                  DIAGNÓSTICO E RECONSTRUÇÃO DO APP                        ║
# ║                                                                            ║
# ║  Verifica módulos, estilo e carrega tudo corretamente                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝

set -e

clear
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║              DIAGNÓSTICO: App Sem Estilo/Módulos                   ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Procurar projeto
echo -e "${YELLOW}[1/5]${NC} Procurando projeto..."

PROJECT_DIRS=(
    "$PWD/sistemahotelsantos"
    "/home/gabriel/SistemaHotelSantos/sistemahotelsantos"
    "/home/gabriel/SistemaHotelSantos"
    "./sistemahotelsantos"
)

FOUND_DIR=""
for dir in "${PROJECT_DIRS[@]}"; do
    if [ -d "$dir" ] && [ -f "$dir/app_gui.py" ]; then
        FOUND_DIR="$dir"
        break
    fi
done

if [ -z "$FOUND_DIR" ]; then
    echo -e "${RED}❌ Projeto não encontrado!${NC}"
    echo ""
    echo "Procurei em:"
    for dir in "${PROJECT_DIRS[@]}"; do
        echo "  ✗ $dir"
    done
    echo ""
    echo -e "${YELLOW}Execute este script no diretório do projeto${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Projeto encontrado: $FOUND_DIR${NC}"

echo ""

# 2. Listar módulos
echo -e "${YELLOW}[2/5]${NC} Verificando módulos..."

echo "Arquivos Python:"
cd "$FOUND_DIR"
find . -maxdepth 1 -name "*.py" -type f | sort | while read file; do
    size=$(wc -l < "$file")
    echo -e "  ${GREEN}✓${NC} $file ($size linhas)"
done

echo ""

# 3. Testar imports
echo -e "${YELLOW}[3/5]${NC} Testando imports..."

python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

modules_to_test = [
    'logging_config',
    'ui_constants',
    'validadores',
    'customtkinter',
]

print("")
for module in modules_to_test:
    try:
        __import__(module)
        print(f"  ✓ {module}")
    except ImportError as e:
        print(f"  ✗ {module} - {e}")

PYEOF

echo ""

# 4. Verificar dependências
echo -e "${YELLOW}[4/5]${NC} Verificando dependências..."

python3 -m pip list 2>/dev/null | grep -E "customtkinter|tkcalendar|fpdf2" | while read line; do
    pkg_name=$(echo "$line" | awk '{print $1}')
    pkg_version=$(echo "$line" | awk '{print $2}')
    echo -e "  ${GREEN}✓${NC} $pkg_name ($pkg_version)"
done

echo ""

# 5. Resumo
echo -e "${YELLOW}[5/5]${NC} Análise concluída"

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                      PRÓXIMOS PASSOS                              ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${BLUE}Opção 1: Executar app atual${NC}"
echo "  python app_gui.py"
echo ""

echo -e "${BLUE}Opção 2: Reconstruir app com estilo${NC}"
echo "  bash RECONSTRUIR_APP_COMPLETO.sh"
echo ""

echo -e "${BLUE}Opção 3: Debugar módulos${NC}"
echo "  python -c \"import app_gui; print('Loaded')\""
echo ""
