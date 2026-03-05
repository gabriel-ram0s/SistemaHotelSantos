#!/bin/bash

# =========================================================================
# copy_missing_files.sh
# Script para copiar logging_config.py e outros arquivos para o projeto
# =========================================================================

clear

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║     📋 COPIAR ARQUIVOS FALTANDO PARA SEU PROJETO                     ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Funções
show_success() {
    echo -e "${GREEN}✅${NC} $1"
}

show_error() {
    echo -e "${RED}❌${NC} $1"
}

show_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# =========================================================================
# PASSO 1: Identificar diretório do projeto
# =========================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ PASSO 1: Identificar Projeto${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

PROJECT_DIR="$HOME/SistemaHotelSantos/sistemahotelsantos"

if [ -d "$PROJECT_DIR" ]; then
    show_success "Projeto encontrado: $PROJECT_DIR"
else
    show_error "Projeto não encontrado em: $PROJECT_DIR"
    echo ""
    echo "Digite o caminho correto do seu projeto:"
    echo "  Exemplo: /home/gabriel/MeuProjeto"
    read -p "Caminho: " PROJECT_DIR
    
    if [ ! -d "$PROJECT_DIR" ]; then
        show_error "Diretório não existe: $PROJECT_DIR"
        exit 1
    fi
    show_success "Usando: $PROJECT_DIR"
fi

echo ""

# =========================================================================
# PASSO 2: Verificar arquivo faltando
# =========================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ PASSO 2: Verificar Arquivo Faltando${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ -f "$PROJECT_DIR/logging_config.py" ]; then
    show_info "logging_config.py já existe no projeto"
else
    show_error "logging_config.py NÃO ENCONTRADO"
fi

echo ""

# =========================================================================
# PASSO 3: Copiar arquivo
# =========================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ PASSO 3: Copiar Arquivo${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Copiar logging_config.py
if [ -f "logging_config.py" ]; then
    cp logging_config.py "$PROJECT_DIR/"
    show_success "logging_config.py copiado"
else
    show_error "logging_config.py não encontrado no diretório atual"
    echo ""
    show_info "Tente rodar este script do diretório onde está o arquivo"
    exit 1
fi

# Copiar ui_constants.py (se existir)
if [ -f "ui_constants.py" ]; then
    cp ui_constants.py "$PROJECT_DIR/"
    show_success "ui_constants.py copiado"
fi

# Copiar validadores.py (se existir)
if [ -f "validadores.py" ]; then
    cp validadores.py "$PROJECT_DIR/"
    show_success "validadores.py copiado"
fi

echo ""

# =========================================================================
# PASSO 4: Verificar resultado
# =========================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ PASSO 4: Verificar Resultado${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "Conteúdo da pasta $PROJECT_DIR:"
echo ""
ls -lh "$PROJECT_DIR" | grep -E "\.py$|\.ico$"

echo ""

# =========================================================================
# PASSO 5: Teste
# =========================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ PASSO 5: Teste Rápido${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "$PROJECT_DIR"

if [ -f ".venv/bin/python" ]; then
    show_info "Testando import de logging_config..."
    ".venv/bin/python" -c "from logging_config import setup_logging; print('✅ Import OK')" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        show_success "logging_config importa corretamente!"
    else
        show_error "Erro ao importar logging_config"
        show_info "Tente ativar o venv manualmente:"
        echo "   source .venv/bin/activate"
        echo "   python -c \"from logging_config import setup_logging\""
    fi
else
    show_info "venv não encontrado, pulando teste"
fi

echo ""

# =========================================================================
# RESUMO FINAL
# =========================================================================

clear

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║                  ✅ ARQUIVOS COPIADOS COM SUCESSO!                   ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "📁 Pasta do Projeto:"
echo "   $PROJECT_DIR"
echo ""

echo "📋 Arquivos Agora Presentes:"
ls "$PROJECT_DIR"/*.py 2>/dev/null | xargs -I {} basename {} | sed 's/^/   ✅ /'
echo ""

echo "🚀 Próximos Passos:"
echo "   1. cd $PROJECT_DIR"
echo "   2. source .venv/bin/activate (se não estiver ativado)"
echo "   3. python app_gui.py"
echo "   OU no VS Code: pressione F5"
echo ""

echo "═══════════════════════════════════════════════════════════════════════"
echo ""
