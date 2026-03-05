#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║           SOLUÇÃO DEFINITIVA: distutils + customtkinter Python 3.12        ║
# ║                                                                            ║
# ║  Este script faz limpeza completa e reinstalação da customtkinter         ║
# ╚════════════════════════════════════════════════════════════════════════════╝

set -e

clear
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║     SOLUÇÃO DEFINITIVA: distutils + customtkinter (Python 3.12)    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Verificar venv
echo -e "${YELLOW}[1/6]${NC} Procurando ambiente virtual..."

if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✓ .venv ativado${NC}"
    else
        echo -e "${RED}❌ .venv não encontrado!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Venv já ativo: $VIRTUAL_ENV${NC}"
fi

echo ""

# 2. Verificar Python
echo -e "${YELLOW}[2/6]${NC} Verificando Python..."
PY_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python $PY_VERSION${NC}"

echo ""

# 3. Atualizar pip
echo -e "${YELLOW}[3/6]${NC} Atualizando pip..."
python -m pip install --upgrade pip --quiet 2>/dev/null
echo -e "${GREEN}✓ pip atualizado${NC}"

echo ""

# 4. Instalar setuptools
echo -e "${YELLOW}[4/6]${NC} Instalando setuptools..."
python -m pip install --upgrade setuptools --quiet 2>/dev/null
echo -e "${GREEN}✓ setuptools instalado${NC}"

echo ""

# 5. Desinstalar customtkinter antigo
echo -e "${YELLOW}[5/6]${NC} Removendo customtkinter antigo..."
python -m pip uninstall customtkinter -y --quiet 2>/dev/null || true
echo -e "${GREEN}✓ customtkinter removido${NC}"

echo ""

# 6. Instalar customtkinter novo
echo -e "${YELLOW}[6/6]${NC} Instalando customtkinter compatível..."
python -m pip install customtkinter --quiet 2>/dev/null

if python -c "import customtkinter; print(customtkinter.__version__)" 2>/dev/null; then
    VERSION=$(python -c "import customtkinter; print(customtkinter.__version__)")
    echo -e "${GREEN}✓ customtkinter $VERSION instalado${NC}"
else
    echo -e "${RED}❌ Erro na instalação${NC}"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                  ✅ PROBLEMA COMPLETAMENTE RESOLVIDO!             ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Testar import
echo -e "${BLUE}Testando import...${NC}"
echo ""

python3 << 'PYEOF'
try:
    import customtkinter as ctk
    print("\033[0;32m✓ customtkinter importado com sucesso!\033[0m")
    print(f"\033[0;32m✓ Versão: {ctk.__version__}\033[0m")
    print("\033[0;32m✓ Sem erros de distutils!\033[0m")
except Exception as e:
    print(f"\033[0;31m❌ Erro: {e}\033[0m")
    exit(1)
PYEOF

echo ""
echo -e "${GREEN}🚀 Próximos passos:${NC}"
echo ""
echo "   1. Execute:"
echo -e "      ${YELLOW}python app_gui.py${NC}"
echo ""
echo "   2. Ou no VS Code: Pressione ${YELLOW}F5${NC}"
echo ""
echo -e "${GREEN}Seu app deve funcionar agora! ✨${NC}"
