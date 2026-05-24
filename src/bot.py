import time
import sys
import logging
from src.config import ConfigManager
from src.capture import WindowCapturer
from src.detector import BarDetector
from src.keyboard_handler import ActionHandler

logger = logging.getLogger("febbyBot")

class BotEngine:
    """
    O cérebro do bot. Integra captura em segundo plano da janela do Tibia via Win32 API,
    dupla detecção (HP e Mana) com coordenadas relativas à janela,
    e envio de ações independentes de forma paralela e de altíssima performance.
    """
    def __init__(self, config_path=None):
        self.config_manager = ConfigManager(config_path)
        self.capturer = WindowCapturer(self.config_manager.window_title_keyword)
        
        # Inicializa dois detectores genéricos independentes
        self.hp_detector = BarDetector(self.config_manager.hsv_ranges, label="HP")
        self.mana_detector = BarDetector(self.config_manager.mana_hsv_ranges, label="Mana")
        
        # Lê a configuração de input_method do config.json
        input_method = self.config_manager.config_data.get("input_method", "keyboard")
        self.action_handler = ActionHandler(method=input_method)
        
        self.running = False
        self.paused = False
        
        # Dicionários de cooldowns separados
        self.cooldowns = {}
        
        # Ordena regras de HP ascendentemente (menor HP = maior prioridade)
        self._hp_rules = sorted(
            self.config_manager.healing_rules, 
            key=lambda x: x["max_hp_percentage"]
        )
        
        # Ordena regras de Mana ascendentemente (menor Mana = maior prioridade)
        self._mana_rules = sorted(
            self.config_manager.mana_rules, 
            key=lambda x: x["max_mana_percentage"]
        )
        
        # Teclas de controle global do Bot
        self.pause_hotkey = "home"
        self.stop_hotkey = "end"
        
        logger.info(f"Engine estruturada de cura paralela:")
        logger.info(f"  -> Regras de HP ({len(self._hp_rules)}):")
        for r in self._hp_rules:
            logger.info(f"     * [{r['name']}]: HP <= {r['max_hp_percentage']}% | Hotkey: {r['hotkey']} | Cooldown: {r['cooldown_ms']}ms")
        logger.info(f"  -> Regras de Mana ({len(self._mana_rules)}):")
        for r in self._mana_rules:
            logger.info(f"     * [{r['name']}]: Mana <= {r['max_mana_percentage']}% | Hotkey: {r['hotkey']} | Cooldown: {r['cooldown_ms']}ms")

    def run(self):
        """Inicia o loop principal do bot."""
        self.running = True
        self.paused = False
        
        print("\n" + "="*50)
        print("    TIBIA OT VISUAL BOT - HP & MANA ACTIVE")
        print("="*50)
        print(f"[*] Atalho [{self.pause_hotkey.upper()}]: Pausar / Retomar")
        print(f"[*] Atalho [{self.stop_hotkey.upper()}]: Parar bot e Fechar")
        print("="*50 + "\n")
        
        # Instala listeners para as teclas de controle usando a lib keyboard
        import keyboard
        
        def toggle_pause():
            self.paused = not self.paused
            state = "PAUSADO" if self.paused else "ATIVO"
            logger.info(f"Bot alternado para o estado: {state}")
            if self.paused:
                print("\n[BOT PAUSADO]")
            else:
                print("\n[BOT RETOMADO]")

        def stop_bot():
            self.running = False
            logger.info("Solicitação de parada recebida.")

        keyboard.add_hotkey(self.pause_hotkey, toggle_pause)
        keyboard.add_hotkey(self.stop_hotkey, stop_bot)
        
        # Variáveis para controle de taxa de atualização de logs no console
        last_log_time = 0
        
        try:
            while self.running:
                # 1. Se estiver pausado, aguarda um pouco e continua o loop
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # 2. Captura regiões de HP e Mana separadamente
                roi_hp = self.capturer.capture_region(self.config_manager.hp_bar_region)
                roi_mana = self.capturer.capture_region(self.config_manager.mana_bar_region)
                
                # 3. Detecta as porcentagens
                current_hp = self.hp_detector.get_percentage(roi_hp)
                current_mana = self.mana_detector.get_percentage(roi_mana)
                
                # 4. Exibe as porcentagens no terminal em tempo real em uma única linha
                current_time = time.time()
                if current_time - last_log_time >= 0.1:
                    sys.stdout.write(f"\r[HUD] HP: {current_hp:.1f}% | MANA: {current_mana:.1f}% | Status: ATIVO   ")
                    sys.stdout.flush()
                    last_log_time = current_time
                
                # 5. Avalia de forma paralela e independente as regras de HP e de Mana
                self._evaluate_hp_rules(current_hp, current_time)
                self._evaluate_mana_rules(current_mana, current_time)
                
                # 6. Aguarda o intervalo do ciclo
                time.sleep(self.config_manager.loop_delay_seconds)
                
        except KeyboardInterrupt:
            logger.info("Bot interrompido manualmente pelo terminal.")
        finally:
            self.cleanup()

    def _evaluate_hp_rules(self, current_hp, current_time):
        """Avalia regras de cura de HP e executa a de maior prioridade."""
        for rule in self._hp_rules:
            if current_hp <= rule["max_hp_percentage"]:
                rule_name = rule["name"]
                hotkey = rule["hotkey"]
                cooldown_sec = rule["cooldown_ms"] / 1000.0
                
                if rule_name not in self.cooldowns:
                    self.cooldowns[rule_name] = 0.0
                
                if current_time >= self.cooldowns[rule_name]:
                    self.cooldowns[rule_name] = current_time + cooldown_sec
                    self.action_handler.press_hotkey(hotkey)
                    
                    print(f"\n[AÇÃO - HP] {rule_name} Ativada! HP: {current_hp:.1f}% <= {rule['max_hp_percentage']}% | Tecla {hotkey}")
                    logger.info(f"Cura de HP executada: {rule_name} (Tecla {hotkey}, HP {current_hp:.1f}%)")
                    break

    def _evaluate_mana_rules(self, current_mana, current_time):
        """Avalia regras de cura de Mana e executa a de maior prioridade (Fluxo paralelo)."""
        for rule in self._mana_rules:
            if current_mana <= rule["max_mana_percentage"]:
                rule_name = rule["name"]
                hotkey = rule["hotkey"]
                cooldown_sec = rule["cooldown_ms"] / 1000.0
                
                if rule_name not in self.cooldowns:
                    self.cooldowns[rule_name] = 0.0
                
                if current_time >= self.cooldowns[rule_name]:
                    self.cooldowns[rule_name] = current_time + cooldown_sec
                    self.action_handler.press_hotkey(hotkey)
                    
                    print(f"\n[AÇÃO - MANA] {rule_name} Ativada! Mana: {current_mana:.1f}% <= {rule['max_mana_percentage']}% | Tecla {hotkey}")
                    logger.info(f"Cura de Mana executada: {rule_name} (Tecla {hotkey}, Mana {current_mana:.1f}%)")
                    break

    def cleanup(self):
        """Libera recursos com segurança."""
        print("\n\nEncerrando o bot e liberando recursos...")
        self.capturer.close()
        import keyboard
        try:
            keyboard.remove_hotkey(self.pause_hotkey)
            keyboard.remove_hotkey(self.stop_hotkey)
        except Exception:
            pass
        logger.info("BotEngine finalizado com segurança.")
        print("Bot desligado.")
