#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║                     FIX: ModuleNotFoundError logging_config                ║
# ║                                                                            ║
# ║  Resolve: ModuleNotFoundError: No module named 'logging_config'           ║
# ╚════════════════════════════════════════════════════════════════════════════╝

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

clear
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           FIX: ModuleNotFoundError logging_config              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Verificar se estamos no diretório correto
echo -e "${YELLOW}[1/5]${NC} Verificando estrutura do projeto..."

PROJECT_DIR=$(pwd)
PYTHON_DIR="$PROJECT_DIR/sistemahotelsantos"

if [ ! -d "$PYTHON_DIR" ]; then
    echo -e "${RED}❌ Erro: Não encontrei o diretório 'sistemahotelsantos'${NC}"
    echo -e "${YELLOW}Execute este script na raiz do seu projeto!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Estrutura ok${NC}"
echo ""

# 2. Verificar se logging_config.py existe
echo -e "${YELLOW}[2/5]${NC} Procurando logging_config.py..."

if [ -f "$PYTHON_DIR/logging_config.py" ]; then
    echo -e "${GREEN}✓ logging_config.py já existe${NC}"
else
    echo -e "${YELLOW}⚠ logging_config.py não encontrado. Criando...${NC}"
    
    cat > "$PYTHON_DIR/logging_config.py" << 'EOF'
"""
Módulo de configuração de logging para o sistema.
Centraliza toda a configuração de logs da aplicação.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logging(log_level=logging.INFO):
    """
    Configura o sistema de logging da aplicação.
    
    Args:
        log_level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: Logger configurado para usar em toda a aplicação
    """
    
    # Criar diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Nome do arquivo de log com data
    log_filename = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Configurar o logger
    logger = logging.getLogger("SistemaHotelSantos")
    logger.setLevel(log_level)
    
    # Se logger já tem handlers, retorna ele
    if logger.handlers:
        return logger
    
    # Formato do log
    log_format = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging iniciado - Nível: {logging.getLevelName(log_level)}")
    
    return logger


# Logger global para usar em qualquer lugar
logger = setup_logging()
EOF
    
    echo -e "${GREEN}✓ logging_config.py criado com sucesso${NC}"
fi

echo ""

# 3. Verificar se __init__.py existe
echo -e "${YELLOW}[3/5]${NC} Verificando __init__.py..."

if [ ! -f "$PYTHON_DIR/__init__.py" ]; then
    echo -e "${YELLOW}⚠ __init__.py não encontrado. Criando...${NC}"
    touch "$PYTHON_DIR/__init__.py"
    echo -e "${GREEN}✓ __init__.py criado${NC}"
else
    echo -e "${GREEN}✓ __init__.py já existe${NC}"
fi

echo ""

# 4. Verificar venv
echo -e "${YELLOW}[4/5]${NC} Verificando ambiente virtual..."

if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ Ambiente virtual encontrado${NC}"
    
    # Ativar venv
    source .venv/bin/activate
    echo -e "${GREEN}✓ Ambiente virtual ativado${NC}"
else
    echo -e "${YELLOW}⚠ Ambiente virtual não encontrado${NC}"
    echo -e "${YELLOW}Criando ambiente virtual...${NC}"
    
    python3 -m venv .venv
    source .venv/bin/activate
    
    echo -e "${GREEN}✓ Ambiente virtual criado e ativado${NC}"
fi

echo ""

# 5. Testar import
echo -e "${YELLOW}[5/5]${NC} Testando se logging_config pode ser importado..."

cd "$PYTHON_DIR"

python3 << 'PYEOF'
try:
    from logging_config import setup_logging, logger
    print("\033[0;32m✓ logging_config importado com sucesso!\033[0m")
    print(f"\033[0;32m✓ Logger configurado: {logger.name}\033[0m")
except ImportError as e:
    print(f"\033[0;31m❌ Erro ao importar: {e}\033[0m")
    exit(1)
PYEOF

cd - > /dev/null

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    ✓ PROBLEMA RESOLVIDO!                      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}Próximos passos:${NC}"
echo ""
echo "1. Ative o ambiente virtual:"
echo -e "   ${YELLOW}source .venv/bin/activate${NC}"
echo ""
echo "2. Execute seu código:"
echo -e "   ${YELLOW}python sistema_clientes.py${NC}"
echo ""
echo "3. Ou no VS Code pressione F5"
echo ""

echo -e "${BLUE}📝 Resumo:${NC}"
echo -e "   ${GREEN}✓${NC} logging_config.py criado/verificado"
echo -e "   ${GREEN}✓${NC} __init__.py verificado"
echo -e "   ${GREEN}✓${NC} Ambiente virtual confirmado"
echo -e "   ${GREEN}✓${NC} Import testado com sucesso"
echo ""

echo -e "${GREEN}Tudo pronto! 🚀${NC}"
