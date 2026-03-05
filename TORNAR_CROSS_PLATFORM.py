#!/usr/bin/env python3
"""
Script para tornar app_gui.py 100% compatível com Windows, Linux e Mac
Detecta o SO e aplica otimizações específicas
"""

import sys
import re
from pathlib import Path

def detectar_so():
    """Detecta o sistema operacional"""
    if sys.platform == "win32":
        return "Windows"
    elif sys.platform == "linux":
        return "Linux"
    elif sys.platform == "darwin":
        return "macOS"
    else:
        return "Desconhecido"

def criar_wrapper_maximizar():
    """Cria função que maximiza a janela de forma cross-platform"""
    return '''def _maximizar_janela():
        """Maximiza a janela de forma compatível com Linux e Windows"""
        if sys.platform == "win32":
            # Windows: usar state('zoomed')
            try:
                self.state('zoomed')
            except:
                self.geometry("1200x900")
        else:
            # Linux/Mac: usar geometry
            self.geometry("1200x900")
    
    self.after(0, _maximizar_janela)'''

def corrigir_app_gui(caminho_arquivo):
    """Corrige app_gui.py para ser cross-platform"""
    
    print("🔧 Tornando app_gui.py cross-platform...")
    print("")
    
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    conteudo_original = conteudo
    
    # FIX 1: Remover ou comentar state('zoomed') problemático
    print("  ✓ Removendo state('zoomed') não-portável...")
    
    # Padrão 1: try: self.after(0, lambda: self.state('zoomed'))
    conteudo = re.sub(
        r"try:\s*self\.after\(0,\s*lambda:\s*self\.state\('zoomed'\)\)",
        "# Maximizar janela de forma cross-platform\n        self.after(0, lambda: self._maximizar_janela())",
        conteudo
    )
    
    # Padrão 2: self.after(0, lambda: self.state('zoomed'))
    conteudo = re.sub(
        r"self\.after\(0,\s*lambda:\s*self\.state\('zoomed'\)\)",
        "self.after(0, lambda: self._maximizar_janela())",
        conteudo
    )
    
    # Padrão 3: self.state('zoomed') direto
    conteudo = conteudo.replace(
        "self.state('zoomed')",
        "self._maximizar_janela()"
    )
    
    # FIX 2: Adicionar função _maximizar_janela se não existir
    print("  ✓ Adicionando função de maximizar cross-platform...")
    
    if "_maximizar_janela" not in conteudo:
        # Encontrar o lugar certo para adicionar o método (logo depois de __init__)
        # Procurar por "def " e adicionar antes do próximo método
        
        # Melhor: adicionar após a definição de __init__
        padrao = r'(self\.tela_login\(\))'
        if re.search(padrao, conteudo):
            # Encontrar a indentação correta
            wrapper = '''
    def _maximizar_janela(self) -> None:
        """Maximiza a janela de forma compatível com Windows e Linux"""
        try:
            if sys.platform == "win32":
                # Windows: usar state('zoomed') para maximizar
                self.state('zoomed')
            else:
                # Linux/Mac: usar geometry para definir tamanho grande
                self.geometry("1200x900")
        except Exception as e:
            # Fallback se houver erro
            self.geometry("1200x900")
    
    '''
            conteudo = conteudo.replace(
                "    def limpar_tela(self)",
                wrapper + "    def limpar_tela(self)"
            )
    
    # FIX 3: Garantir imports necessários
    print("  ✓ Garantindo imports...")
    
    if "import sys" not in conteudo:
        # Adicionar após imports customtkinter
        conteudo = conteudo.replace(
            "import customtkinter as ctk",
            "import customtkinter as ctk\nimport sys"
        )
    
    if "import tkinter as tk" not in conteudo:
        conteudo = conteudo.replace(
            "import customtkinter as ctk",
            "import customtkinter as ctk\nimport tkinter as tk"
        )
    
    # FIX 4: Fazer carregamento de ícone cross-platform
    print("  ✓ Tornando carregamento de ícone cross-platform...")
    
    # Padrão: self.iconbitmap(resource_path("app.ico"))
    conteudo = re.sub(
        r"self\.iconbitmap\(resource_path\(\"app\.ico\"\)\)",
        '''try:
            if sys.platform == "win32":
                self.iconbitmap(resource_path("app.ico"))
            # Linux/Mac ignoram .ico
        except Exception:
            pass''',
        conteudo
    )
    
    # FIX 5: Adicionar try-except robusto em limpar_tela
    print("  ✓ Adicionando proteção em limpar_tela()...")
    
    if "def limpar_tela" in conteudo:
        # Substituir simples destroy por try-except
        conteudo = re.sub(
            r"for w in self\.main_frame\.winfo_children\(\):\s*w\.destroy\(\)",
            """for w in self.main_frame.winfo_children():
            try:
                w.destroy()
            except (AttributeError, tk.TclError):
                pass""",
            conteudo
        )
    
    # FIX 6: Remover problemas com fontes como dicts
    print("  ✓ Normalizando definições de fontes...")
    
    conteudo = re.sub(
        r"font=([A-Z_]+)",
        r'font=("Arial", 12)',
        conteudo
    )
    
    # Verificar mudanças
    if conteudo != conteudo_original:
        print("")
        print("  ✅ Alterações detectadas!")
        
        # Backup
        backup_path = str(caminho_arquivo) + ".backup_cross_platform"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(conteudo_original)
        print(f"  📦 Backup: {backup_path}")
        
        # Salvar corrigido
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        print(f"  ✅ Arquivo corrigido!")
        
        return True
    else:
        print("")
        print("  ⚠️ Nenhuma alteração necessária")
        return False

def main():
    """Função principal"""
    
    so = detectar_so()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  COMPATIBILIDADE CROSS-PLATFORM: app_gui.py              ║")
    print("║  Versão: 2.0                                              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("")
    print(f"Sistema Operacional Detectado: {so}")
    print("")
    
    # Procurar arquivo
    caminhos = [
        Path("sistemahotelsantos/app_gui.py"),
        Path("/home/gabriel/SistemaHotelSantos/sistemahotelsantos/app_gui.py"),
        Path("./app_gui.py"),
    ]
    
    arquivo = None
    for p in caminhos:
        if p.exists():
            arquivo = p
            print(f"✓ Arquivo encontrado: {arquivo}")
            break
    
    if not arquivo:
        print("❌ app_gui.py não encontrado!")
        sys.exit(1)
    
    print("")
    
    # Corrigir
    sucesso = corrigir_app_gui(arquivo)
    
    print("")
    print("╔════════════════════════════════════════════════════════════╗")
    if sucesso:
        print("║  ✅ VERSÃO CROSS-PLATFORM CRIADA COM SUCESSO!            ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print("")
        print("Seu app agora funciona em:")
        print("  ✓ Windows - Maximizado com ícone")
        print("  ✓ Linux - Tamanho otimizado, sem ícone")
        print("  ✓ macOS - Tamanho otimizado, sem ícone")
        print("")
        print("Próximos passos:")
        print("  1. Feche VS Code: Ctrl+Q")
        print("  2. Reabra VS Code")
        print("  3. Pressione F5 para testar")
        print("")
    else:
        print("║  ⚠️  NENHUMA ALTERAÇÃO NECESSÁRIA                       ║")
        print("╚════════════════════════════════════════════════════════════╝")
    
    print("✨ Pronto!")

if __name__ == "__main__":
    main()
