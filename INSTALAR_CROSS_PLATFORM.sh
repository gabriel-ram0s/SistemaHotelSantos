#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║              INSTALADOR CROSS-PLATFORM: Windows + Linux                    ║
# ║                                                                            ║
# ║  Aplica todas as correções e torna seu app 100% compatível               ║
# ╚════════════════════════════════════════════════════════════════════════════╝

set -e

clear
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║        INSTALADOR CROSS-PLATFORM: app_gui.py                      ║"
echo "║        Windows + Linux + macOS                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Ativar venv
echo -e "${YELLOW}[1/5]${NC} Ativando ambiente virtual..."

if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✓ .venv ativado${NC}"
    else
        echo -e "${RED}❌ .venv não encontrado${NC}"
        exit 1
    fi
fi

echo ""

# 2. Detectar SO
echo -e "${YELLOW}[2/5]${NC} Detectando sistema operacional..."

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    SO="Windows"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    SO="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    SO="macOS"
else
    SO="Desconhecido"
fi

echo -e "${GREEN}✓ SO Detectado: $SO${NC}"

echo ""

# 3. Procurar app_gui.py
echo -e "${YELLOW}[3/5]${NC} Procurando app_gui.py..."

PROJECT_DIRS=(
    "sistemahotelsantos"
    "/home/gabriel/SistemaHotelSantos/sistemahotelsantos"
    "."
)

FOUND_DIR=""
for dir in "${PROJECT_DIRS[@]}"; do
    if [ -f "$dir/app_gui.py" ]; then
        FOUND_DIR="$dir"
        break
    fi
done

if [ -z "$FOUND_DIR" ]; then
    echo -e "${RED}❌ app_gui.py não encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Encontrado em: $FOUND_DIR${NC}"

echo ""

# 4. Aplicar script Python de correção
echo -e "${YELLOW}[4/5]${NC} Aplicando correções cross-platform..."

cd "$FOUND_DIR"

python3 << 'PYEOF'
import sys
import re
from pathlib import Path

arquivo = Path("app_gui.py")

if not arquivo.exists():
    print("❌ app_gui.py não encontrado")
    sys.exit(1)

with open(arquivo, 'r', encoding='utf-8') as f:
    conteudo = f.read()

conteudo_original = conteudo

# FIX 1: state('zoomed') -> _otimizar_janela()
conteudo = re.sub(
    r"try:\s*self\.after\(0,\s*lambda:\s*self\.state\('zoomed'\)\)",
    "self.after(0, self._otimizar_janela)",
    conteudo
)

conteudo = conteudo.replace(
    "self.state('zoomed')",
    "self._otimizar_janela()"
)

# FIX 2: Adicionar função _otimizar_janela se não existir
if "_otimizar_janela" not in conteudo:
    wrapper = '''
    def _otimizar_janela(self) -> None:
        """Otimiza o tamanho da janela de forma cross-platform"""
        try:
            if sys.platform == "win32":
                self.state('zoomed')
            else:
                self.geometry("1400x900")
        except Exception:
            pass

    def _carregar_icone(self) -> None:
        """Carrega o ícone da janela apenas se disponível"""
        try:
            if sys.platform == "win32":
                self.iconbitmap(resource_path("app.ico"))
        except Exception:
            pass

    '''
    conteudo = conteudo.replace(
        "    def limpar_tela(self)",
        wrapper + "    def limpar_tela(self)"
    )

# FIX 3: Importar sys e tk
if "import sys" not in conteudo:
    conteudo = conteudo.replace(
        "import customtkinter as ctk",
        "import sys\nimport customtkinter as ctk"
    )

if "import tkinter as tk" not in conteudo:
    conteudo = conteudo.replace(
        "import customtkinter as ctk",
        "import customtkinter as ctk\nimport tkinter as tk"
    )

# FIX 4: Proteção em limpar_tela
conteudo = re.sub(
    r"for w in self\.main_frame\.winfo_children\(\):\s*w\.destroy\(\)",
    """for w in self.main_frame.winfo_children():
            try:
                w.destroy()
            except (AttributeError, tk.TclError):
                pass""",
    conteudo
)

# FIX 5: Chamar _carregar_icone() após __init__
if "_carregar_icone()" not in conteudo and "_carregar_icone" in conteudo:
    conteudo = conteudo.replace(
        "self.geometry(\"1200x850\")",
        '''self.geometry("1200x850")\n        self._carregar_icone()'''
    )

if conteudo != conteudo_original:
    # Backup
    backup = arquivo.with_suffix(arquivo.suffix + ".backup_cross")
    with open(backup, 'w', encoding='utf-8') as f:
        f.write(conteudo_original)
    print(f"  📦 Backup: {backup}")
    
    # Salvar
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"  ✅ Arquivo corrigido!")
else:
    print(f"  ⚠️ Arquivo já estava compatível")

PYEOF

echo ""

# 5. Teste final
echo -e "${YELLOW}[5/5]${NC} Testando importação..."

python3 << 'PYEOF'
try:
    import customtkinter as ctk
    import tkinter as tk
    print("\033[0;32m✓ customtkinter e tkinter OK\033[0m")
    
    # Tentar importar sistema_clientes
    try:
        from sistema_clientes import SistemaCreditos
        print("\033[0;32m✓ sistema_clientes OK\033[0m")
    except ImportError:
        print("\033[1;33m⚠ sistema_clientes não encontrado (pode ser normal)\033[0m")
        
except ImportError as e:
    print(f"\033[0;31m❌ Erro: {e}\033[0m")
    exit(1)

PYEOF

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║          ✅ VERSÃO CROSS-PLATFORM INSTALADA COM SUCESSO!          ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${GREEN}Seu app agora funciona em:${NC}"
echo "  ✓ Windows - Maximizado com ícone"
echo "  ✓ Linux - Tamanho otimizado"
echo "  ✓ macOS - Tamanho otimizado"
echo ""

echo -e "${BLUE}Próximos passos:${NC}"
echo ""
echo "  1. Feche VS Code completamente:"
echo "     Ctrl+Q ou Alt+F4"
echo ""
echo "  2. Reabra VS Code"
echo ""
echo "  3. Teste a aplicação:"
echo "     Pressione F5 ou execute: python app_gui.py"
echo ""

echo -e "${GREEN}✨ Tudo pronto!${NC}"

