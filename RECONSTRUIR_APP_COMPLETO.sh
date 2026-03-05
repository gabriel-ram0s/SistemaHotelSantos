#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║              RECONSTRUIR APP COM ESTILO E MÓDULOS COMPLETOS               ║
# ║                                                                            ║
# ║  Este script copia a versão reconstruída e testa a aplicação              ║
# ╚════════════════════════════════════════════════════════════════════════════╝

set -e

clear
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║        RECONSTRUINDO APP COM ESTILO E MÓDULOS COMPLETOS            ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Ativar venv
echo -e "${YELLOW}[1/4]${NC} Ativando ambiente virtual..."

if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✓ .venv ativado${NC}"
    else
        echo -e "${RED}❌ .venv não encontrado${NC}"
        echo "Execute primeiro: python3 -m venv .venv"
        exit 1
    fi
fi

echo ""

# 2. Procurar diretório do projeto
echo -e "${YELLOW}[2/4]${NC} Procurando diretório do projeto..."

PROJECT_DIRS=(
    "$PWD/sistemahotelsantos"
    "/home/gabriel/SistemaHotelSantos/sistemahotelsantos"
    "./sistemahotelsantos"
)

FOUND_DIR=""
for dir in "${PROJECT_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        FOUND_DIR="$dir"
        echo -e "${GREEN}✓ Encontrado: $dir${NC}"
        break
    fi
done

if [ -z "$FOUND_DIR" ]; then
    echo -e "${RED}❌ Diretório do projeto não encontrado${NC}"
    echo ""
    echo "Procurei em:"
    for dir in "${PROJECT_DIRS[@]}"; do
        echo "  $dir"
    done
    exit 1
fi

echo ""

# 3. Copiar arquivos
echo -e "${YELLOW}[3/4]${NC} Copiando arquivos reconstruídos..."

# Backup do arquivo antigo
if [ -f "$FOUND_DIR/app_gui.py" ]; then
    cp "$FOUND_DIR/app_gui.py" "$FOUND_DIR/app_gui.py.backup"
    echo -e "${GREEN}✓ Backup criado: app_gui.py.backup${NC}"
fi

# Copiar novo arquivo
cp "$(dirname "$0")/app_gui_reconstruido.py" "$FOUND_DIR/app_gui.py"
echo -e "${GREEN}✓ app_gui.py atualizado${NC}"

# Garantir que os módulos existem
for module in logging_config.py ui_constants.py validadores.py; do
    if [ ! -f "$FOUND_DIR/$module" ]; then
        echo -e "${YELLOW}⚠ Copiando $module...${NC}"
        cp "$(dirname "$0")/$module" "$FOUND_DIR/" 2>/dev/null || echo "⚠ $module não encontrado"
    fi
done

echo ""

# 4. Testar
echo -e "${YELLOW}[4/4]${NC} Testando aplicação..."

cd "$FOUND_DIR"

python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    import customtkinter as ctk
    from logging_config import logger
    from ui_constants import COLORS, FONTS, WINDOW
    from validadores import Validadores
    
    print("\n  ✓ customtkinter")
    print("  ✓ logging_config")
    print("  ✓ ui_constants")
    print("  ✓ validadores")
    print("\n✅ Todos os módulos importados com sucesso!")
    
except ImportError as e:
    print(f"\n❌ Erro ao importar: {e}")
    sys.exit(1)

PYEOF

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║              ✅ APP RECONSTRUÍDO COM SUCESSO!                     ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${GREEN}Arquivos atualizados:${NC}"
echo "  ✓ app_gui.py (versão completa com estilo)"
echo "  ✓ logging_config.py"
echo "  ✓ ui_constants.py"
echo "  ✓ validadores.py"
echo ""

echo -e "${GREEN}🚀 Próximos passos:${NC}"
echo ""
echo "  1. Ainda está no terminal? Feche o terminal"
echo "  2. Abra VS Code novamente (Ctrl+K para recarregar)"
echo "  3. Pressione F5 para executar"
echo ""
echo "  OU execute no terminal:"
echo "  python app_gui.py"
echo ""

echo -e "${BLUE}📝 Recursos da aplicação:${NC}"
echo "  ✓ Dashboard com estatísticas"
echo "  ✓ Gerenciamento de clientes com validação"
echo "  ✓ Módulos para quartos, reservas, configurações"
echo "  ✓ Sistema de logging completo"
echo "  ✓ Persistência de dados em JSON"
echo "  ✓ Interface com estilo profissional"
echo ""

echo -e "${YELLOW}💡 Se a app não abrir:${NC}"
echo "  1. Verifique se o venv está ativado"
echo "  2. Execute: python app_gui.py (no terminal)"
echo "  3. Verifique os logs em logs/"
echo ""
