"""
Módulo de Auto-Atualização
Carrega versão do GitHub
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
from version import __version__

class UpdateManager:
    def __init__(self):
        self.versao_atual = __version__


class UpdateManager:
    """Gerencia atualizações do aplicativo"""
    
    GITHUB_REPO = "gabriel-ram0s/sistemahotelsantos"
    GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    def __init__(self):
        self.versao_atual = self._obter_versao()
        self.arquivo_versao = Path.home() / ".shs_version"
        self.carregar_versao()
    
    def _obter_versao(self) -> str:
        """
        Obtém versão da tag do git ou do arquivo de configuração.
        Ordem de busca:
        1. Variável de ambiente BUILD_VERSION (definida no GitHub Actions)
        2. Tag git local
        3. Arquivo .shs_version
        4. Padrão: 0.0.0
        """
        # 1. Variável de ambiente (usada em builds via GitHub Actions)
        version = os.getenv('BUILD_VERSION')
        if version:
            return version
        
        # 2. Tag git mais recente
        try:
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().lstrip('v')
        except:
            pass
        
        # 3. Arquivo local
        arquivo = Path.home() / ".shs_version"
        if arquivo.exists():
            try:
                with open(arquivo, 'r') as f:
                    data = json.load(f)
                    return data.get('versao', '0.0.0')
            except:
                pass
        
        # 4. Padrão
        return "0.0.0"
    
    def carregar_versao(self):
        """Carrega versão salva ou usa padrão"""
        try:
            if self.arquivo_versao.exists():
                with open(self.arquivo_versao, 'r') as f:
                    data = json.load(f)
                    self.versao_atual = data.get('versao', self.versao_atual)
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
        """Compara duas versões (v1.v2.v3)"""
        try:
            v1_parts = [int(x) for x in v1.split('.')]
            v2_parts = [int(x) for x in v2.split('.')]
            
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
    
    def verificar_atualizacao(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Verifica se há nova versão disponível"""
        try:
            print(f"🔍 Verificando atualizações...")
            response = requests.get(self.GITHUB_API, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            versao_nova = data['tag_name'].lstrip('v')
            
            print(f"   Versão atual: {self.versao_atual}")
            print(f"   Versão remota: {versao_nova}")
            
            comparacao = self.comparar_versoes(self.versao_atual, versao_nova)
            
            if comparacao < 0:
                print(f"✅ Nova versão disponível: {versao_nova}")
                
                assets = data.get('assets', [])
                url_download = None
                
                os_identifier = "Windows" if platform.system() == "Windows" else "Ubuntu"
                for asset in assets:
                    if os_identifier in asset['name']:
                        url_download = asset['browser_download_url']
                        break
                
                if url_download:
                    print(f"📥 Download disponível: {url_download}")
                    return True, versao_nova, url_download
                else:
                    print(f"⚠️ Nova versão {versao_nova} encontrada, mas sem build para {os_identifier}.")
                    return False, None, None
            else:
                print("✅ Você está na versão mais recente.")
                return False, None, None
                    
        except requests.exceptions.Timeout:
            raise Exception("Tempo esgotado ao verificar atualizações.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro de rede: {e}")
        except Exception as e:
            print(f"❌ Erro: {e}")
            raise e
    
    def aplicar_atualizacao(self, url_download: str, versao_nova: str, 
                           progress_callback: Optional[Callable] = None) -> None:
        """Baixa e aplica atualização"""
        def _task():
            try:
                is_windows = platform.system() == 'Windows'
                exec_path = os.path.abspath(sys.executable)
                exec_dir = os.path.dirname(exec_path)
                exec_name = os.path.basename(exec_path)
        
                temp_suffix = ".exe" if is_windows else ""
                temp_path = os.path.join(exec_dir, f"update_temp{temp_suffix}")
                
                # Baixar
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
            
                # Criar script de atualização
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
                    
                    if progress_callback: 
                        progress_callback(1.0, "finalizando")
                    subprocess.Popen(updater_path, shell=True, cwd=exec_dir, 
                                   creationflags=subprocess.DETACHED_PROCESS)
                else:
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
                    
                    if progress_callback: 
                        progress_callback(1.0, "finalizando")
                    subprocess.Popen(["/bin/bash", updater_path], cwd=exec_dir, 
                                   start_new_session=True)

                self.salvar_versao(versao_nova)
                os._exit(0)
                
            except Exception as e:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
                raise Exception(f"Falha ao atualizar: {e}")
        
        threading.Thread(target=_task, daemon=True).start()