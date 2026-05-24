import os
import sys
import json
import cv2
import numpy as np
import time

# Adiciona o diretório pai ao path para importar os módulos da src
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from src.capture import WindowCapturer
from src.detector import BarDetector


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    print("="*65)
    print("    CALIBRAÇÃO INTEGRADA (HP & MANA) - Win32 Background Mode")
    print("="*65)
    print("[*] A janela do Tibia pode estar POR BAIXO de outras janelas.")
    print("[*] NÃO precisa de Alt+Tab! O bot captura de fundo automaticamente.")
    print("[*] Certifique-se apenas de que a janela NÃO está MINIMIZADA.")
    print("[*] Instruções:")
    print("  1. Abra o Tibia OT (pode deixá-lo por baixo do terminal).")
    print("  2. Ao pressionar ENTER, o script capturará a janela do jogo diretamente.")
    print("  3. Uma janela gráfica exibirá o frame do Tibia.")
    print("     Selecione a BARRA DE HP (arraste o mouse), confirme com ENTER.")
    print("  4. A janela reabrirá para a BARRA DE MANA.")
    print("     Selecione-a e confirme com ENTER.")
    print("  5. As coordenadas são relativas à janela do Tibia —")
    print("     você pode mover o jogo livremente sem recalibrar!")
    print("="*65)

    config_path = os.path.join(base_dir, "config.json")
    if not os.path.exists(config_path):
        print("[ERRO] config.json não encontrado.")
        return

    config_data = load_config(config_path)
    keyword = config_data.get("window_title_keyword", "Tibia")

    input(f"\nPressione [ENTER] para capturar a janela '{keyword}'...")

    # 1. Captura o frame atual da janela do Tibia (em segundo plano)
    print(f"\n[*] Localizando e capturando janela contendo '{keyword}'...")
    try:
        capturer = WindowCapturer(keyword)
        w, h = capturer.get_client_size()
        print(f"[+] Janela encontrada! Tamanho da área de cliente: {w}x{h} pixels.")
        frame = capturer.capture_window()
        capturer.close()
    except RuntimeError as e:
        print(f"\n[ERRO] {e}")
        return

    # 2. Salva um snapshot da janela capturada para diagnóstico
    debug_dir = os.path.join(base_dir, "debug_previews")
    os.makedirs(debug_dir, exist_ok=True)
    snapshot_path = os.path.join(debug_dir, "calibration_window_snapshot.png")
    cv2.imwrite(snapshot_path, frame)
    print(f"[+] Snapshot salvo em: {snapshot_path}")

    # 3. Selecionar ROI da barra de HP
    print("\n[*] Janela abrindo: Selecione a BARRA DE HP.")
    win_hp = "1/2  Selecione a BARRA DE HP (arraste o mouse e confirme com ENTER)"
    roi_hp = cv2.selectROI(win_hp, frame, showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()

    left_hp, top_hp, width_hp, height_hp = roi_hp
    if width_hp == 0 or height_hp == 0:
        print("[!] Seleção de HP cancelada. Abortando calibração.")
        return
    print(f"    -> HP  : left={left_hp}, top={top_hp}, width={width_hp}, height={height_hp}")

    # 4. Selecionar ROI da barra de MANA
    print("\n[*] Janela abrindo: Selecione a BARRA DE MANA.")
    win_mana = "2/2  Selecione a BARRA DE MANA (arraste o mouse e confirme com ENTER)"
    roi_mana = cv2.selectROI(win_mana, frame, showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()

    left_mana, top_mana, width_mana, height_mana = roi_mana
    if width_mana == 0 or height_mana == 0:
        print("[!] Seleção de Mana cancelada. Abortando calibração.")
        return
    print(f"    -> Mana: left={left_mana}, top={top_mana}, width={width_mana}, height={height_mana}")

    # 5. Salva as coordenadas no config.json
    config_data["hp_bar_region"]   = {"left": int(left_hp),   "top": int(top_hp),
                                       "width": int(width_hp),  "height": int(height_hp)}
    config_data["mana_bar_region"] = {"left": int(left_mana), "top": int(top_mana),
                                       "width": int(width_mana),"height": int(height_mana)}
    save_config(config_path, config_data)
    print("\n[+] Coordenadas salvas em config.json com sucesso!")

    # 6. Gera prévias diagnósticas com o cálculo de HP/Mana
    print("\n[*] Gerando prévias de diagnóstico...")
    try:
        hp_img   = frame[top_hp:top_hp+height_hp,     left_hp:left_hp+width_hp]
        mana_img = frame[top_mana:top_mana+height_mana, left_mana:left_mana+width_mana]

        hp_detector   = BarDetector(config_data["hsv_ranges"],      label="HP")
        mana_detector = BarDetector(config_data["mana_hsv_ranges"], label="Mana")

        hp_prev_path   = os.path.join(debug_dir, "calibration_hp_preview.png")
        mana_prev_path = os.path.join(debug_dir, "calibration_mana_preview.png")

        pct_hp   = hp_detector.get_percentage(hp_img,   debug_save_path=hp_prev_path)
        pct_mana = mana_detector.get_percentage(mana_img, debug_save_path=mana_prev_path)

        print(f"  [+] HP detectado   : {pct_hp}%  ->  {hp_prev_path}")
        print(f"  [+] Mana detectada : {pct_mana}% ->  {mana_prev_path}")
        print("\n  Abra as imagens acima para verificar se a máscara de cores está correta.")
        print("  O HP/Mana preenchido aparece em BRANCO; o fundo vazio aparece em PRETO.")
    except Exception as e:
        print(f"[AVISO] Falha ao gerar prévia de diagnóstico: {e}")

    print("\n" + "="*65)
    print("                CALIBRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("  Dica: A janela do Tibia pode ficar coberta por outras janelas.")
    print("  Apenas NÃO a minimize para o bot continuar funcionando!")
    print("="*65 + "\n")


if __name__ == "__main__":
    main()
