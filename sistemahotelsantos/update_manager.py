"""
Módulo de Auto-Atualização
Verifica novas versões no GitHub e permite atualizar o aplicativo
"""

import sys
import os
import json
import subprocess
import platform
from pathlib import Path
from datetime import datetime
import threading
import requests
from tkinter import messagebox

class UpdateManager:
    """Gerencia atualizações do aplicativo"""
    
    # Configuração - ALTERE CONFORME SEU REPOSITÓRIO
    GITHUB_REPO = "gabriel-ram0s/sistemahotelsantos"
    GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    def __init__(self):
        self.versao_atual = "4.9.4"  # Versão do aplicativo (Sincronizada)
        self.arquivo_versao = Path.home() / ".shs_version"
        self.carregar_versao()
    
    def carregar_versao(self):
        """Carrega versão salva ou usa padrão"""
        try:
            if self.arquivo_versao.exists():
                with open(self.arquivo_versao, 'r') as f:
                    data = json.load(f)
                    # self.versao_atual = data.get('versao', '4.9.4') # Comentado para forçar versão do código
                    pass
        except Exception as e:
            print(f"⚠️ Erro ao carregar versão: {e}")
    
    def salvar_versao(self, versao):
        """Salva versão atual"""
        try:
            with open(self.arquivo_versao, 'w') as f:
                json.dump({
                    'versao': versao,
                    'data_atualizacao': datetime.now().isoformat()
                }, f)
        except Exception as e:
            print(f"⚠️ Erro ao salvar versão: {e}")
    
    def comparar_versoes(self, v1, v2):
        """
        Compara duas versões (v1.v2.v3)
        Retorna:
          -1 se v1 < v2
           0 se v1 == v2
           1 se v1 > v2
        """
        try:
            v1_parts = [int(x) for x in v1.split('.')]
            v2_parts = [int(x) for x in v2.split('.')]
            
            # Padronizar tamanho
            while len(v1_parts) < len(v2_parts):
                v1_parts.append(0)
            while len(v2_parts) < len(v1_parts):
                v2_parts.append(0)
            
            if v1_parts < v2_parts:
                return -1
            elif v1_parts > v2_parts:
                return 1
            else:
                return 0
        except:
            return 0
    
    def verificar_atualizacao(self, callback=None):
        """
        Verifica se há nova versão disponível
        callback(tem_atualizacao, versao_nova, url_download)
        """
        def _check():
            try:
                print(f"🔍 Verificando atualizações...")
                response = requests.get(self.GITHUB_API, timeout=5)
                
                if response.status_code != 200:
                    print(f"⚠️ Erro ao verificar: {response.status_code}")
                    if callback:
                        callback(False, None, None)
                    return
                
                data = response.json()
                versao_nova = data['tag_name'].lstrip('v')
                
                print(f"   Versão atual: {self.versao_atual}")
                print(f"   Versão remota: {versao_nova}")
                
                comparacao = self.comparar_versoes(self.versao_atual, versao_nova)
                
                if comparacao < 0:
                    # Encontrou versão mais nova
                    print(f"✅ Nova versão disponível: {versao_nova}")
                    
                    # Procurar asset correto
                    assets = data.get('assets', [])
                    url_download = None
                    
                    if platform.system() == "Windows":
                        for asset in assets:
                            if 'Windows' in asset['name']:
                                url_download = asset['browser_download_url']
                                break
                    else:
                        for asset in assets:
                            if 'Ubuntu' in asset['name']:
                                url_download = asset['browser_download_url']
                                break
                    
                    if url_download:
                        print(f"📥 Download disponível: {url_download}")
                        if callback:
                            callback(True, versao_nova, url_download)
                    else:
                        print("⚠️ Asset não encontrado para seu SO")
                        if callback:
                            callback(False, None, None)
                else:
                    print("✅ Você está na versão mais recente")
                    if callback:
                        callback(False, None, None)
                        
            except requests.exceptions.Timeout:
                print("⚠️ Timeout ao verificar atualizações")
                if callback:
                    callback(False, None, None)
            except Exception as e:
                print(f"❌ Erro ao verificar: {e}")
                if callback:
                    callback(False, None, None)
        
        # Executar em thread para não travar UI
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()
    
    def baixar_atualizar(self, versao_nova, url_download, callback=None):
        """Baixa e instala a atualização"""
        def _download():
            try:
                print(f"📥 Baixando {versao_nova}...")
                
                # Caminho para salvar
                if platform.system() == "Windows":
                    app_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.getcwd()
                    download_path = Path(app_path) / "SistemaHotelSantos.exe.new"
                else:
                    download_path = Path.home() / "SistemaHotelSantos.new"
                
                # Baixar arquivo
                response = requests.get(url_download, timeout=30, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                
                with open(download_path, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = (downloaded / total_size * 100) if total_size else 0
                            print(f"   {percent:.1f}% baixado")
                            if callback:
                                callback(percent)
                
                print(f"✅ Download concluído!")
                
                # Backup do atual
                if platform.system() == "Windows":
                    current_exe = Path(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.getcwd()) / "SistemaHotelSantos.exe"
                    backup_exe = current_exe.with_suffix('.exe.backup')
                    if current_exe.exists():
                        current_exe.rename(backup_exe)
                    download_path.rename(current_exe)
                else:
                    current_exe = Path.home() / "SistemaHotelSantos"
                    backup_exe = current_exe.with_suffix('.backup')
                    if current_exe.exists():
                        current_exe.rename(backup_exe)
                    download_path.rename(current_exe)
                    current_exe.chmod(0o755)
                
                # Salvar versão
                self.salvar_versao(versao_nova)
                
                print(f"✅ Atualização instalada!")
                messagebox.showinfo(
                    "Atualização Concluída",
                    f"Sistema atualizado para v{versao_nova}\n\n"
                    "Reinicie o aplicativo para as mudanças entrarem em efeito."
                )
                
            except Exception as e:
                print(f"❌ Erro ao baixar: {e}")
                messagebox.showerror("Erro na Atualização", f"Erro: {e}")
        
        thread = threading.Thread(target=_download, daemon=True)
        thread.start()


def verificar_atualizacao_ao_iniciar(root):
    """Verifica atualização ao iniciar o app"""
    manager = UpdateManager()
    
    def on_check(tem_update, versao_nova, url_download):
        if tem_update:
            resposta = messagebox.askyesno(
                "Nova Versão Disponível",
                f"Versão {versao_nova} disponível!\n\n"
                f"Deseja atualizar agora?"
            )
            
            if resposta:
                messagebox.showinfo(
                    "Atualizando",
                    "Baixando nova versão...\n"
                    "Isto pode levar alguns minutos."
                )
                manager.baixar_atualizar(versao_nova, url_download)
    
    # Verificar em background
    manager.verificar_atualizacao(callback=on_check)
