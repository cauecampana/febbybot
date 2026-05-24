import os
import sys
import numpy as np
import cv2

# Adiciona o diretório pai para importação do src
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from src.detector import BarDetector
from src.keyboard_handler import ActionHandler

def generate_mock_bar(percentage, bar_type="hp", width=150, height=12):
    """
    Gera uma imagem sintética representando uma barra de status do Tibia.
    O HP/Mana é preenchido da esquerda para a direita.
    - Se for HP:
      - Se HP > 50%: verde (BGR: [0, 220, 0])
      - Se 20% < HP <= 50%: amarelo (BGR: [0, 220, 220])
      - Se HP <= 20%: vermelho (BGR: [0, 0, 220])
    - Se for Mana:
      - Sempre azul (BGR: [220, 0, 0])
    O restante da barra é preenchido com cinza escuro (BGR: [40, 40, 40]).
    """
    # Inicializa imagem cinza escuro
    img = np.full((height, width, 3), 40, dtype=np.uint8)
    
    # Adiciona uma borda preta fina de 1 pixel (comum em UIs de jogos)
    img[0, :] = 10
    img[-1, :] = 10
    img[:, 0] = 10
    img[:, -1] = 10
    
    # Calcula largura útil (excluindo borda de 1px nas laterais)
    inner_width = width - 2
    filled_width = int(round(inner_width * (percentage / 100.0)))
    
    if filled_width > 0:
        if bar_type.lower() == "hp":
            # Cores de HP dinâmicas
            if percentage > 50:
                color = [0, 220, 0]       # Verde (BGR)
            elif percentage > 20:
                color = [0, 220, 220]     # Amarelo (BGR)
            else:
                color = [0, 0, 220]       # Vermelho (BGR)
        else:
            # Cor de Mana sempre Azul
            color = [220, 50, 50]      # Azul vibrante (BGR)
            
        # Preenche a barra da esquerda para a direita (dentro das bordas)
        img[1:height-1, 1:filled_width+1] = color
        
    return img

def run_tests():
    print("="*60)
    print("     TESTES E MOCKS AUTOMÁTICOS INTEGRADOS (HP & MANA)")
    print("="*60)
    
    # 1. Definir intervalos HSV (mesmos do config.json atualizado)
    hp_hsv_ranges = [
        {"min": [0, 100, 100], "max": [85, 255, 255]},
        {"min": [160, 100, 100], "max": [180, 255, 255]}
    ]
    mana_hsv_ranges = [
        {"min": [90, 100, 100], "max": [130, 255, 255]}
    ]
    
    hp_detector = BarDetector(hp_hsv_ranges, label="HP")
    mana_detector = BarDetector(mana_hsv_ranges, label="Mana")
    
    test_levels = [100.0, 75.0, 50.0, 20.0, 0.0]
    
    print("\n[*] 1. Validando BarDetector para HP...")
    all_passed = True
    os.makedirs(os.path.join(base_dir, "debug_previews"), exist_ok=True)
    
    for lvl in test_levels:
        mock_hp = generate_mock_bar(lvl, bar_type="hp")
        debug_path = os.path.join(base_dir, "debug_previews", f"mock_hp_debug_{int(lvl)}.png")
        detected = hp_detector.get_percentage(mock_hp, debug_save_path=debug_path)
        difference = abs(lvl - detected)
        
        if difference <= 2.0:
            print(f"  [PASS] HP Esperado: {lvl:>5}% | Detectado: {detected:>5}% | Desvio: {difference:.1f}%")
        else:
            print(f"  [FAIL] HP Esperado: {lvl:>5}% | Detectado: {detected:>5}% | Desvio: {difference:.1f}% (FORA DO LIMITE)")
            all_passed = False

    print("\n[*] 2. Validando BarDetector para MANA...")
    for lvl in test_levels:
        mock_mana = generate_mock_bar(lvl, bar_type="mana")
        debug_path = os.path.join(base_dir, "debug_previews", f"mock_mana_debug_{int(lvl)}.png")
        detected = mana_detector.get_percentage(mock_mana, debug_save_path=debug_path)
        difference = abs(lvl - detected)
        
        if difference <= 2.0:
            print(f"  [PASS] Mana Esperada: {lvl:>5}% | Detectada: {detected:>5}% | Desvio: {difference:.1f}%")
        else:
            print(f"  [FAIL] Mana Esperada: {lvl:>5}% | Detectada: {detected:>5}% | Desvio: {difference:.1f}% (FORA DO LIMITE)")
            all_passed = False
            
    if all_passed:
        print("\n[+] BarDetector passou em todos os testes de HP e Mana!")
    else:
        print("\n[!] BarDetector falhou em algum dos testes.")

    # 3. Testando o Módulo de Teclado
    print("\n[*] 3. Teste do ActionHandler com Hotkeys de HP e Mana...")
    try:
        handler = ActionHandler(method="keyboard")
        print("  [+] Pressionando 'F2' (cura de manutenção de HP)...")
        handler.press_hotkey("F2")
        print("  [+] Pressionando 'F3' (recarga de Mana)...")
        handler.press_hotkey("F3")
        print("  [+] Teclas enviadas com sucesso.")
    except Exception as e:
        print(f"  [FAIL] Falha no teste do ActionHandler: {e}")
        all_passed = False

    print("\n" + "="*60)
    print("                 FIM DOS TESTES INTEGRADOS")
    print("="*60 + "\n")
    return all_passed

if __name__ == "__main__":
    run_tests()
