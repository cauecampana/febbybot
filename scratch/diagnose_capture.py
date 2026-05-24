"""
scratch/diagnose_capture.py

Diagnóstico de captura em segundo plano (Win32 API).

Execute este script para verificar se o WindowCapturer consegue capturar
a janela do Tibia mesmo quando ela está coberta por outras janelas.

Uso:
    py scratch/diagnose_capture.py
"""
import os
import sys
import time
import cv2

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from src.capture import WindowCapturer
import json


def main():
    print("="*60)
    print("     DIAGNÓSTICO DE CAPTURA EM SEGUNDO PLANO (Win32)")
    print("="*60)

    config_path = os.path.join(base_dir, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    keyword = config.get("window_title_keyword", "Tibia")
    print(f"\n[*] Buscando janela com palavra-chave: '{keyword}'")

    try:
        capturer = WindowCapturer(keyword)
        w, h = capturer.get_client_size()
        print(f"[+] Janela encontrada! Área de cliente: {w}x{h} px")
    except RuntimeError as e:
        print(f"\n[ERRO] {e}")
        return

    debug_dir = os.path.join(base_dir, "debug_previews")
    os.makedirs(debug_dir, exist_ok=True)

    print("\n[*] Capturando agora (a janela pode estar coberta por outras)...")
    print("    Você tem 3 segundos para cobri-la com outra janela se quiser testar!\n")

    for i in range(3, 0, -1):
        print(f"    Capturando em {i}...")
        time.sleep(1)

    try:
        frame = capturer.capture_window()
        capturer.close()
    except RuntimeError as e:
        print(f"\n[ERRO] Captura falhou: {e}")
        return

    out_path = os.path.join(debug_dir, "diagnose_capture.png")
    cv2.imwrite(out_path, frame)

    print(f"\n[+] Captura salva em: {out_path}")
    print("[+] Abra o arquivo acima e verifique se mostra o frame do Tibia corretamente.")
    print("    Se mostrar, o bot funcionará perfeitamente em segundo plano!")

    # Exibe a captura em janela do OpenCV por 5 segundos
    print("\n[*] Exibindo captura por 5 segundos (feche a janela para encerrar)...")
    cv2.imshow(f"Diagnóstico - {keyword} (Win32 Background Capture)", frame)
    cv2.waitKey(5000)
    cv2.destroyAllWindows()

    print("\n" + "="*60)
    print("                  DIAGNÓSTICO CONCLUÍDO")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
