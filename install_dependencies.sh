#!/bin/bash
# =========================================================================
# install_dependencies.sh
# Script para instalar todas as dependências automaticamente
# Basta rodar: bash install_dependencies.sh
# =========================================================================

clear

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   Instalando Dependências do Projeto...                ║"
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
echo "📦 Instalando dependências..."
echo ""

# Atualizar pip (importante!)
echo "1/2: Atualizando pip..."
python -m pip install --upgrade pip

# Instalar todas as dependências
echo ""
echo "2/2: Instalando bibliotecas..."
pip install customtkinter tkcalendar fpdf2 requests pytest pytest-cov

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Erro durante instalação!"
    echo ""
    echo "💡 Tente:"
    echo "   python -m pip install --upgrade pip"
    echo "   pip install customtkinter"
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
