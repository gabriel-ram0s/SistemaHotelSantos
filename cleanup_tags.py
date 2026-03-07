#!/usr/bin/env python3
"""
cleanup_tags.py - Limpar tags antigas e começar com v6.0.7
"""

import subprocess
import sys


class Colors:
    HEADER = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def disable():
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')


if sys.platform == 'win32':
    Colors.disable()


def run(cmd, shell=False):
    """Executa comando"""
    result = subprocess.run(cmd, capture_output=True, text=True, shell=shell)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def main():
    print_header("🧹 Limpeza de Tags - Preparando para v6.0.7+")
    
    # 1. Listar todas as tags
    print(f"{Colors.BOLD}Tags locais:{Colors.ENDC}")
    code, output, _ = run(['git', 'tag'])
    if output:
        tags = output.split('\n')
        for i, tag in enumerate(tags[-10:], 1):  # Últimas 10
            print(f"  {i}. {tag}")
    else:
        print("  Nenhuma tag encontrada")
    
    print(f"\n{Colors.BOLD}Tags remotas (GitHub):{Colors.ENDC}")
    code, output, _ = run(['git', 'ls-remote', '--tags', 'origin'])
    if output:
        remote_tags = [line.split('/')[-1] for line in output.split('\n') if 'v' in line]
        remote_tags = sorted(set(remote_tags))
        for i, tag in enumerate(remote_tags[-10:], 1):  # Últimas 10
            print(f"  {i}. {tag}")
    
    # 2. Confirmar limpeza
    print(f"\n{Colors.WARNING}{Colors.BOLD}⚠️  AVISO:{Colors.ENDC}")
    print("Você está prestes a deletar TODAS as tags antigas.")
    print("Isso afetará o GitHub mas não afetará seu código.")
    
    confirmacao = input(f"\n{Colors.BOLD}Deseja continuar? (s/n): {Colors.ENDC}").strip().lower()
    if confirmacao != 's':
        print_error("Operação cancelada")
        return
    
    # 3. Deletar todas as tags locais
    print_header("Deletando tags locais")
    code, output, _ = run(['git', 'tag'])
    if output:
        tags = output.split('\n')
        for tag in tags:
            if tag.strip():
                code, _, err = run(['git', 'tag', '-d', tag.strip()])
                if code == 0:
                    print_success(f"Deletada localmente: {tag}")
                else:
                    print_error(f"Erro ao deletar: {tag}")
    
    # 4. Deletar todas as tags remotas no GitHub
    print_header("Deletando tags remotas (GitHub)")
    code, output, _ = run(['git', 'ls-remote', '--tags', 'origin'])
    if output:
        for line in output.split('\n'):
            if 'v' in line:
                tag = line.split('/')[-1]
                if tag.strip():
                    code, _, err = run(['git', 'push', 'origin', '--delete', tag.strip()])
                    if code == 0:
                        print_success(f"Deletada no GitHub: {tag}")
                    else:
                        print_warning(f"Não foi possível deletar: {tag}")
    
    print_header("✨ Limpeza Concluída!")
    print(f"{Colors.OKGREEN}")
    print("Próximos passos:")
    print("1. Faça suas alterações")
    print("2. Execute: python release_novo.py")
    print("   ou")
    print("   git add .")
    print("   git commit -m 'Versão 6.0.7: Descrição'")
    print("   git tag v6.0.7")
    print("   git push origin main")
    print("   git push --tags")
    print(f"{Colors.ENDC}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_error("\nOperação cancelada")
        sys.exit(0)
    except Exception as e:
        print_error(f"Erro: {e}")
        sys.exit(1)
