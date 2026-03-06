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
from typing import Optional, Tuple, Callable
class UpdateManager:
    """Gerencia atualizações do aplicativo"""
    
    # Configuração - ALTERE CONFORME SEU REPOSITÓRIO
    GITHUB_REPO = "gabriel-ram0s/sistemahotelsantos"
    GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    def __init__(self):
        self.versao_atual = "5.0"  # Versão do aplicativo (Sincronizada)
        self.arquivo_versao = Path.home() / ".shs_version"
        self.carregar_versao()
    
    def carregar_versao(self):
        """Carrega versão salva ou usa padrão"""
        try:
            if self.arquivo_versao.exists():
                with open(self.arquivo_versao, 'r') as f:
                    data = json.load(f)
                    self.versao_atual = data.get('versao', '5.0') # Reativa a leitura, mantendo 5.0 como padrão
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
    
    def aplicar_atualizacao(self, url_download: str, versao_nova: str, progress_callback: Optional[Callable] = None) -> None:
        """
        Baixa o novo executável, cria um script para substituí-lo e reinicia o app.
        """
        def _task():
            try:
                is_windows = platform.system() == 'Windows'
                
                # Garante que estamos trabalhando com caminhos absolutos
                exec_path = os.path.abspath(sys.executable)
                exec_dir = os.path.dirname(exec_path)
                exec_name = os.path.basename(exec_path)
        
                # Define nomes para o arquivo temporário e o script de atualização
                temp_suffix = ".exe" if is_windows else ""
                temp_path = os.path.join(exec_dir, f"update_temp{temp_suffix}")
                
                # 1. Baixar o novo arquivo
                r = requests.get(url_download, stream=True, timeout=30)
                r.raise_for_status()
                
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(temp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = downloaded_size / total_size
                            progress_callback(progress, None)
            
                # 2. Criar script de atualização e executar
                if is_windows:
                    updater_path = os.path.join(exec_dir, "updater.bat")
                    bat_script = f"""
                    @echo off
                    echo Atualizando o sistema... Por favor, aguarde.
                    timeout /t 3 /nobreak > NUL
                    :retry
                    del "{exec_path}"
                    if exist "{exec_path}" (
                        echo Arquivo ainda em uso, tentando novamente em 2 segundos...
                        timeout /t 2 /nobreak > NUL
                        goto retry
                    )
                    ren "{temp_path}" "{exec_name}"
                    start "" "{exec_path}"
                    del "{updater_path}"
                    """
                    with open(updater_path, "w", encoding="utf-8") as bat:
                        bat.write(bat_script)
                    
                    if progress_callback: progress_callback(1.0, "finalizando")
                    subprocess.Popen(updater_path, shell=True, cwd=exec_dir, creationflags=subprocess.DETACHED_PROCESS)
                else: # Linux/Unix
                    updater_path = os.path.join(exec_dir, "updater.sh")
                    os.chmod(temp_path, 0o755)
                    
                    sh_script = f"""#!/bin/bash
                    echo "Atualizando..."
                    sleep 3
                    rm -f "{exec_path}"
                    mv "{temp_path}" "{exec_path}"
                    nohup "{exec_path}" >/dev/null 2>&1 &
                    rm -- "$0"
                    """
                    with open(updater_path, "w") as sh:
                        sh.write(sh_script)
                    os.chmod(updater_path, 0o755)
                    
                    if progress_callback: progress_callback(1.0, "finalizando")
                    subprocess.Popen(["/bin/bash", updater_path], cwd=exec_dir, start_new_session=True)

                self.salvar_versao(versao_nova)
                os._exit(0)
                
            except Exception as e:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
                raise Exception(f"Falha ao atualizar: {e}")
        
        threading.Thread(target=_task, daemon=True).start()
