#!/bin/bash
# =========================================================================
# install_dependencies_ubuntu.sh
# Script para Ubuntu que resolve o erro PEP 668 automaticamente
# Basta rodar: bash install_dependencies_ubuntu.sh
# =========================================================================

clear

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   Instalando Dependências (Ubuntu) - PEP 668 Resolvido ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Verificar se venv existe
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "❌ ERRO: Ambiente virtual não encontrado!"
    echo ""
    echo "📌 Crie com: python3 -m venv venv"
    echo ""
    read -p "Pressione ENTER para sair..."
    exit 1
fi

# Ativar venv
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

if [ $? -ne 0 ]; then
    echo "❌ Erro ao ativar venv!"
    read -p "Pressione ENTER para sair..."
    exit 1
fi

echo ""
echo "✅ Ambiente Virtual ativado!"
echo ""
echo "📦 Instalando dependências (com --break-system-packages)..."
echo ""

# Atualizar pip (importante!)
echo "1/2: Atualizando pip..."
pip install --break-system-packages --upgrade pip

# Instalar todas as dependências com o flag necessário
echo ""
echo "2/2: Instalando bibliotecas (Ubuntu PEP 668)..."
pip install --break-system-packages -r sistemahotelsantos/requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erro durante instalação!"
    echo ""
    echo "💡 Tente manualmente:"
    echo "   pip install --break-system-packages -r requirements.txt"
    echo ""
    read -p "Pressione ENTER para sair..."
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   ✅ Instalação Concluída com Sucesso!                ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📌 Próximos passos:"
echo "   1. Rode testes: python test_all_modules.py"
echo "   2. Rode app: python app_gui.py"
echo ""
echo "✨ Tudo pronto para começar!"
echo ""

read -p "Pressione ENTER para fechar..."
