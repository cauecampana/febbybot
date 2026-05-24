import os
import json
import logging

logger = logging.getLogger("febbyBot")

class ConfigManager:
    """
    Gerencia o carregamento, salvamento e validação das configurações do bot.
    """
    def __init__(self, config_path=None):
        if config_path is None:
            # Por padrão, assume que config.json está na raiz do projeto
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config.json")
            
        self.config_path = config_path
        self.config_data = {}
        self.load()

    def load(self):
        """Carrega as configurações a partir do arquivo JSON."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Arquivo de configuração não encontrado em: {self.config_path}. Criando com padrões.")
            self.create_default()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config_data = json.load(f)
            self.validate()
            logger.info("Configurações carregadas com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            raise

    def save(self):
        """Salva as configurações atuais de volta para o arquivo JSON."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            logger.info("Configurações salvas com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")

    def create_default(self):
        """Cria um arquivo de configuração padrão se ele não existir."""
        self.config_data = {
            "window_title_keyword": "Tibia",
            "hp_bar_region": {
                "left": 100,
                "top": 100,
                "width": 150,
                "height": 12
            },
            "mana_bar_region": {
                "left": 260,
                "top": 100,
                "width": 150,
                "height": 12
            },
            "loop_delay_seconds": 0.05,
            "input_method": "keyboard",
            "hsv_ranges": [
                {"min": [0, 100, 100], "max": [85, 255, 255]},
                {"min": [160, 100, 100], "max": [180, 255, 255]}
            ],
            "mana_hsv_ranges": [
                {"min": [90, 100, 100], "max": [130, 255, 255]}
            ],
            "healing_rules": [
                {
                    "name": "Cura de Emergência (Urgente)",
                    "max_hp_percentage": 40,
                    "hotkey": "F1",
                    "cooldown_ms": 1000
                },
                {
                    "name": "Cura Leve (Manutenção)",
                    "max_hp_percentage": 85,
                    "hotkey": "F2",
                    "cooldown_ms": 500
                }
            ],
            "mana_rules": [
                {
                    "name": "Usar Mana Potion",
                    "max_mana_percentage": 70,
                    "hotkey": "F3",
                    "cooldown_ms": 1000
                }
            ]
        }
        self.save()

    def validate(self):
        """Valida a estrutura e os tipos de dados da configuração."""
        # 0. Validar Window Title Keyword
        win_keyword = self.config_data.get("window_title_keyword")
        if not win_keyword or not isinstance(win_keyword, str):
            raise ValueError("window_title_keyword deve ser uma string não vazia.")

        # 1. Validar HP Region
        region_hp = self.config_data.get("hp_bar_region")
        if not region_hp or not all(k in region_hp for k in ["left", "top", "width", "height"]):
            raise ValueError("hp_bar_region precisa ter left, top, width e height.")
        for k in ["left", "top", "width", "height"]:
            if not isinstance(region_hp[k], int) or region_hp[k] < 0:
                raise ValueError(f"O valor de hp_bar_region.{k} deve ser um inteiro maior ou igual a zero.")

        # 2. Validar Mana Region
        region_mana = self.config_data.get("mana_bar_region")
        if not region_mana or not all(k in region_mana for k in ["left", "top", "width", "height"]):
            raise ValueError("mana_bar_region precisa ter left, top, width e height.")
        for k in ["left", "top", "width", "height"]:
            if not isinstance(region_mana[k], int) or region_mana[k] < 0:
                raise ValueError(f"O valor de mana_bar_region.{k} deve ser um inteiro maior ou igual a zero.")

        # 3. Validar Loop Delay
        delay = self.config_data.get("loop_delay_seconds")
        if not isinstance(delay, (int, float)) or delay <= 0:
            raise ValueError("loop_delay_seconds deve ser um número maior que zero.")

        # 4. Validar HSV Ranges do HP
        hsv_ranges = self.config_data.get("hsv_ranges", [])
        if not isinstance(hsv_ranges, list):
            raise ValueError("hsv_ranges precisa ser uma lista.")
        for r in hsv_ranges:
            if "min" not in r or "max" not in r:
                raise ValueError("Cada range de hsv_ranges deve conter 'min' e 'max'.")
            if len(r["min"]) != 3 or len(r["max"]) != 3:
                raise ValueError("Os valores de 'min' e 'max' de HP HSV devem ter exatamente 3 elementos [H, S, V].")

        # 5. Validar HSV Ranges do Mana
        mana_hsv_ranges = self.config_data.get("mana_hsv_ranges", [])
        if not isinstance(mana_hsv_ranges, list):
            raise ValueError("mana_hsv_ranges precisa ser uma lista.")
        for r in mana_hsv_ranges:
            if "min" not in r or "max" not in r:
                raise ValueError("Cada range de mana_hsv_ranges deve conter 'min' e 'max'.")
            if len(r["min"]) != 3 or len(r["max"]) != 3:
                raise ValueError("Os valores de 'min' e 'max' de Mana HSV devem ter exatamente 3 elementos [H, S, V].")

        # 6. Validar Healing Rules (HP)
        rules_hp = self.config_data.get("healing_rules", [])
        if not isinstance(rules_hp, list):
            raise ValueError("healing_rules precisa ser uma lista.")
        for rule in rules_hp:
            required = ["name", "max_hp_percentage", "hotkey", "cooldown_ms"]
            if not all(k in rule for k in required):
                raise ValueError(f"Cada regra de cura de HP deve conter os campos: {required}")
            if not isinstance(rule["max_hp_percentage"], (int, float)) or not (0 <= rule["max_hp_percentage"] <= 100):
                raise ValueError("max_hp_percentage deve ser um número entre 0 e 100.")
            if not isinstance(rule["cooldown_ms"], int) or rule["cooldown_ms"] < 0:
                raise ValueError("cooldown_ms deve ser um inteiro não-negativo.")

        # 7. Validar Mana Rules
        rules_mana = self.config_data.get("mana_rules", [])
        if not isinstance(rules_mana, list):
            raise ValueError("mana_rules precisa ser uma lista.")
        for rule in rules_mana:
            required = ["name", "max_mana_percentage", "hotkey", "cooldown_ms"]
            if not all(k in rule for k in required):
                raise ValueError(f"Cada regra de Mana deve conter os campos: {required}")
            if not isinstance(rule["max_mana_percentage"], (int, float)) or not (0 <= rule["max_mana_percentage"] <= 100):
                raise ValueError("max_mana_percentage deve ser um número entre 0 e 100.")
            if not isinstance(rule["cooldown_ms"], int) or rule["cooldown_ms"] < 0:
                raise ValueError("cooldown_ms deve ser um inteiro não-negativo.")

    @property
    def hp_bar_region(self):
        return self.config_data["hp_bar_region"]

    @property
    def mana_bar_region(self):
        return self.config_data["mana_bar_region"]

    @property
    def loop_delay_seconds(self):
        return self.config_data["loop_delay_seconds"]

    @property
    def hsv_ranges(self):
        return self.config_data["hsv_ranges"]

    @property
    def mana_hsv_ranges(self):
        return self.config_data["mana_hsv_ranges"]

    @property
    def healing_rules(self):
        return self.config_data["healing_rules"]

    @property
    def mana_rules(self):
        return self.config_data["mana_rules"]

    @property
    def window_title_keyword(self):
        return self.config_data.get("window_title_keyword", "Tibia")
