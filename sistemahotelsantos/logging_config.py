"""
logging_config.py
Configura logging centralizado para toda a aplicação
Salva logs em arquivo e exibe no console conforme necessário
"""

import logging
import os
from datetime import datetime


def setup_logging(name: str, log_dir: str = "logs", level=logging.DEBUG) -> logging.Logger:
    """
    Configura logger para um módulo específico.
    
    Args:
        name: Nome do logger (geralmente __name__)
        log_dir: Diretório onde salvar logs
        level: Nível mínimo de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado
    
    Exemplo:
        >>> logger = setup_logging(__name__)
        >>> logger.info("Aplicação iniciada")
        >>> logger.error("Erro crítico", exc_info=True)
    """
    
    # Criar diretório de logs se não existir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Criar logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar múltiplos handlers se já configurado
    if logger.handlers:
        return logger
    
    # Caminhos de arquivo
    timestamp = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{name.split('.')[-1]}_{timestamp}.log")
    error_file = os.path.join(log_dir, f"{name.split('.')[-1]}_{timestamp}_errors.log")
    
    # =========================================================================
    # HANDLER 1: Arquivo de Log Geral (INFO e acima)
    # =========================================================================
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # HANDLER 2: Arquivo de Erros (ERROR e acima)
    error_handler = logging.FileHandler(error_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    
    # =========================================================================
    # HANDLER 3: Console (WARNING e acima)
    # =========================================================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # =========================================================================
    # FORMATADORES
    # =========================================================================
    # Formato padrão: DATA - HORA - MÓDULO - NÍVEL - MENSAGEM
    standard_format = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Formato estendido para erros: inclui informações de stack trace
    detailed_format = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # =========================================================================
    # APLICAR FORMATADORES
    # =========================================================================
    file_handler.setFormatter(standard_format)
    error_handler.setFormatter(detailed_format)
    console_handler.setFormatter(standard_format)
    
    # =========================================================================
    # ADICIONAR HANDLERS AO LOGGER
    # =========================================================================
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger


# =========================================================================
# NÍVEIS DE LOGGING (Como usar)
# =========================================================================
# logger.debug("Informação detalhada para diagnóstico")
# logger.info("Confirmação de que tudo funciona normalmente")
# logger.warning("Aviso: algo inesperado aconteceu")
# logger.error("Erro sério: falha em realizar operação")
# logger.critical("Erro crítico: sistema pode quebrar")


# =========================================================================
# EXEMPLO DE USO
# =========================================================================
if __name__ == "__main__":
    # Configurar logger
    logger = setup_logging(__name__)
    
    # Usar logger
    logger.debug("Debug - Informação detalhada")
    logger.info("Info - Operação normal")
    logger.warning("Warning - Algo inesperado")
    logger.error("Error - Falha em operação")
    
    # Com exception info
    try:
        resultado = 10 / 0
    except Exception as e:
        logger.error("Erro ao dividir por zero", exc_info=True)
    
    print("\n✅ Logs salvos em: ./logs/")
