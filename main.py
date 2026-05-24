import os
import sys
import logging
import ctypes

def is_admin():
    """Verifica se o script está rodando com privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        # Se não for Windows, assume True para não quebrar
        return True

def setup_logging():
    """Configura o sistema de logs para o console e arquivo."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Pasta raiz do projeto
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(base_dir, "bot.log")
    
    # Configuração básica do logging do python
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduz ruídos de logs de bibliotecas externas se houver
    logging.getLogger("mss").setLevel(logging.WARNING)

def main():
    setup_logging()
    logger = logging.getLogger("febbyBot")
    
    # Alerta sobre privilégios de Administrador no Windows
    if sys.platform.startswith("win") and not is_admin():
        print("\n" + "!" * 60)
        print(" [AVISO] O script NÃO está rodando como Administrador!")
        print(" O Tibia costuma bloquear envio de teclas de programas comuns.")
        print(" Para que as hotkeys de cura funcionem dentro do jogo,")
        print(" execute este terminal (Prompt ou PowerShell) como Administrador.")
        print("!" * 60 + "\n")
        logger.warning("Executando sem privilégios de Administrador. Envio de teclas pode falhar.")

    logger.info("Iniciando febbyBot...")
    
    try:
        # Importa localmente para garantir que o logging já está configurado
        from src.bot import BotEngine
        
        # Cria a engine e roda
        engine = BotEngine()
        engine.run()
        
    except FileNotFoundError as e:
        logger.critical(f"Erro ao iniciar o bot. Arquivo não encontrado: {e}")
        print("\n[ERRO CRÍTICO] Verifique se o arquivo config.json está na raiz do projeto.")
    except Exception as e:
        logger.critical(f"Erro inesperado no bot: {e}", exc_info=True)
        print(f"\n[ERRO CRÍTICO] Ocorreu um erro inesperado: {e}")
        print("Consulte o arquivo 'bot.log' para ver a pilha de chamadas detalhada.")

if __name__ == "__main__":
    main()
