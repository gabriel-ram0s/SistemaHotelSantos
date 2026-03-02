import sys
import os
import re

def update_file(file_path, pattern, replacement):
    """Lê um arquivo, substitui um padrão e o reescreve."""
    if not os.path.exists(file_path):
        print(f"Aviso: Arquivo '{file_path}' não encontrado, pulando atualização.")
        return
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = re.sub(pattern, replacement, content)

        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Versão atualizada com sucesso em '{file_path}'.")
        else:
            print(f"Padrão de versão não encontrado em '{file_path}'. Nenhuma alteração feita.")
    except Exception as e:
        print(f"ERRO ao atualizar '{file_path}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    new_version = os.environ.get("NEW_VERSION")
    if not new_version:
        print("ERRO: Variável de ambiente NEW_VERSION não definida.")
        sys.exit(1)

    update_file('sistemahotelsantos/sistema_clientes.py', r'self.versao_atual\s*=\s*\"[^\"]*\"', f'self.versao_atual = "{new_version}"')
    update_file('setup.iss', r'#define MyAppVersion\s+\"[^\"]*\"', f'#define MyAppVersion "{new_version}"')