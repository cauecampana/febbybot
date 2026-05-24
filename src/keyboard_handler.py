import sys
import time
import logging
import keyboard

logger = logging.getLogger("febbyBot")

# Detecção de Sistema Operacional e imports condicionais do Windows
IS_WINDOWS = sys.platform.startswith("win")

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes
    
    # Estruturas necessárias para a API SendInput do Windows (DirectInput)
    # Referência: https://docs.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-input
    
    ULONG_PTR = ctypes.c_ulong if ctypes.sizeof(ctypes.c_void_p) == 4 else ctypes.c_uint64
    
    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR)
        ]
        
    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR)
        ]
        
    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD)
        ]
        
    class INPUT_UNION(ctypes.Union):
        _fields_ = [
            ("ki", KEYBDINPUT),
            ("mi", MOUSEINPUT),
            ("hi", HARDWAREINPUT)
        ]
        
    class INPUT(ctypes.Structure):
        _fields_ = [
            ("type", wintypes.DWORD),
            ("u", INPUT_UNION)
        ]

    # Constantes do SendInput
    INPUT_KEYBOARD = 1
    KEYEVENTF_SCANCODE = 0x0008
    KEYEVENTF_KEYUP = 0x0002

    # Dicionário de DirectInput Scancodes para as principais hotkeys usadas em jogos (Windows)
    # Mapeia strings de teclas amigáveis para scancodes de DirectInput de hardware
    DIRECTINPUT_SCANCODES = {
        "F1": 0x3B, "F2": 0x3C, "F3": 0x3D, "F4": 0x3E,
        "F5": 0x3F, "F6": 0x40, "F7": 0x41, "F8": 0x42,
        "F9": 0x43, "F10": 0x44, "F11": 0x57, "F12": 0x58,
        "1": 0x02, "2": 0x03, "3": 0x04, "4": 0x05, "5": 0x06,
        "6": 0x07, "7": 0x08, "8": 0x09, "9": 0x0A, "0": 0x0B,
        "Q": 0x10, "W": 0x11, "E": 0x12, "R": 0x13, "T": 0x14,
        "A": 0x1E, "S": 0x1F, "D": 0x20, "F": 0x21, "G": 0x22,
        "Z": 0x2C, "X": 0x2D, "C": 0x2E, "V": 0x2F, "B": 0x30,
        "SPACE": 0x39, "ENTER": 0x1C, "ESC": 0x01
    }


class ActionHandler:
    """
    Gerencia o envio de hotkeys e cliques de forma robusta e otimizada.
    Suporta o envio padrão via biblioteca 'keyboard' e o envio alternativo
    de baixo nível via Windows 'DirectInput' (ctypes) para máxima compatibilidade.
    """
    def __init__(self, method="keyboard"):
        """
        Args:
            method (str): "keyboard" para usar o módulo python keyboard,
                          "directinput" para usar DirectInput nativo do Windows.
        """
        self.method = method.lower()
        if self.method == "directinput" and not IS_WINDOWS:
            logger.warning("DirectInput só é suportado no Windows. Revertendo para método 'keyboard'.")
            self.method = "keyboard"
            
        logger.info(f"ActionHandler inicializado utilizando o método: '{self.method}'")

    def press_hotkey(self, hotkey):
        """
        Pressiona e solta uma hotkey de forma assíncrona com latência mínima.
        
        Args:
            hotkey (str): Nome da tecla (ex: "F1", "F2", "1", "Q")
        """
        hotkey_upper = hotkey.upper()
        
        if self.method == "directinput" and IS_WINDOWS:
            self._press_directinput(hotkey_upper)
        else:
            self._press_keyboard_module(hotkey)

    def _press_keyboard_module(self, hotkey):
        """Envia tecla usando o módulo de alto nível 'keyboard'."""
        try:
            keyboard.send(hotkey)
            logger.debug(f"Hotkey '{hotkey}' enviada via módulo keyboard.")
        except Exception as e:
            logger.error(f"Erro ao pressionar hotkey '{hotkey}' via módulo keyboard: {e}")

    def _press_directinput(self, hotkey):
        """Envia tecla de baixo nível usando DirectInput Scancodes no Windows."""
        scancode = DIRECTINPUT_SCANCODES.get(hotkey)
        if scancode is None:
            logger.warning(f"Hotkey '{hotkey}' não possui mapeamento DirectInput. Tentando via módulo keyboard.")
            self._press_keyboard_module(hotkey)
            return

        try:
            # 1. Pressiona a tecla
            extra = ctypes.c_ulong(0)
            ii_ = INPUT_UNION()
            ii_.ki = KEYBDINPUT(0, scancode, KEYEVENTF_SCANCODE, 0, ctypes.addressof(extra))
            input_down = INPUT(INPUT_KEYBOARD, ii_)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(input_down), ctypes.sizeof(input_down))
            
            # Pequeno delay para o jogo reconhecer o evento físico
            time.sleep(0.02)
            
            # 2. Solta a tecla
            ii_up = INPUT_UNION()
            ii_up.ki = KEYBDINPUT(0, scancode, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, ctypes.addressof(extra))
            input_up = INPUT(INPUT_KEYBOARD, ii_up)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(input_up), ctypes.sizeof(input_up))
            
            logger.debug(f"Hotkey '{hotkey}' (0x{scancode:02X}) enviada via DirectInput.")
        except Exception as e:
            logger.error(f"Erro ao pressionar hotkey '{hotkey}' via DirectInput: {e}")
            # Fallback rápido se falhar por algum motivo de ctypes
            self._press_keyboard_module(hotkey)
