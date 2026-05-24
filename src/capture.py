import sys
import ctypes
import logging
import numpy as np
import cv2

logger = logging.getLogger("febbyBot")

# Garante que este módulo só funciona no Windows
if not sys.platform.startswith("win"):
    raise RuntimeError("O módulo capture.py exige Windows (pywin32).")

import win32gui
import win32ui
import win32con

# PrintWindow não está exposta no win32gui — chamamos via ctypes diretamente.
# PW_RENDERFULLCONTENT (flag=2) instrui o DWM a renderizar janelas em background.
_user32 = ctypes.windll.user32
_gdi32  = ctypes.windll.gdi32
PW_RENDERFULLCONTENT = 2


class WindowCapturer:
    """
    Realiza captura de tela diretamente do buffer GDI da janela do Tibia
    usando a API nativa do Windows (PrintWindow + GetWindowDC).

    Vantagens sobre o MSS:
    - Funciona com a janela em segundo plano (Alt+Tab ou coberta por outras janelas).
    - Coordenadas relativas à janela do jogo (não à tela física).
      O bot continua funcionando mesmo que você mova a janela do Tibia.
    - Necessita apenas que a janela NÃO esteja minimizada.
    """

    def __init__(self, window_title_keyword: str):
        """
        Args:
            window_title_keyword (str): Fragmento do título da janela a ser capturada.
                                        Ex: 'Tibia' encontrará 'Tibia - Febbynist'.
        """
        self.keyword = window_title_keyword
        self.hwnd = None
        self._find_window()
        logger.info(f"WindowCapturer inicializado para janela contendo: '{self.keyword}'")

    # ------------------------------------------------------------------
    # Busca de Janela
    # ------------------------------------------------------------------

    def _find_window(self):
        """
        Localiza o HWND da janela cujo título contém a keyword configurada.
        Filtra apenas janelas de nível superior com área visível real.
        Prioriza janelas cujo processo seja um executável do jogo.
        """
        import win32process

        candidates = []

        def _enum_callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            # Ignora janelas sem área (ex: janelas sistemáticas fantasmas)
            try:
                rect = win32gui.GetClientRect(hwnd)
                if (rect[2] - rect[0]) == 0 or (rect[3] - rect[1]) == 0:
                    return
            except Exception:
                return

            title = win32gui.GetWindowText(hwnd)
            if not title or self.keyword.lower() not in title.lower():
                return

            # Obtém o nome do executável do processo dono da janela
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                import psutil
                proc_name = psutil.Process(pid).name().lower()
            except Exception:
                proc_name = ""

            candidates.append((hwnd, title, proc_name))

        win32gui.EnumWindows(_enum_callback, None)

        if not candidates:
            raise RuntimeError(
                f"Nenhuma janela visível com '{self.keyword}' no título foi encontrada.\n"
                "  -> Verifique se o Tibia está aberto e não minimizado.\n"
                "  -> Ajuste 'window_title_keyword' no config.json para corresponder "
                "exatamente ao título da janela do jogo."
            )

        # Log de todos os candidatos para facilitar o diagnóstico
        if len(candidates) > 1:
            logger.warning(f"{len(candidates)} janelas encontradas com '{self.keyword}':")
            for i, (hwnd, title, proc) in enumerate(candidates):
                logger.warning(f"  [{i}] '{title}' (exe: {proc or 'desconhecido'}, hwnd={hwnd})")

            # Preferência: janelas cujo processo parece ser um cliente Tibia
            game_exes = {"tibia", "taleon", "otclient", "tibiann", "tibia.exe"}
            game_matches = [
                c for c in candidates
                if any(g in c[2] for g in game_exes)
            ]
            if game_matches:
                chosen = game_matches[0]
                logger.info(
                    f"Janela do jogo detectada automaticamente: '{chosen[1]}' "
                    f"(exe: {chosen[2] or 'desconhecido'}, hwnd={chosen[0]})"
                )
            else:
                # Nenhum executável de jogo reconhecido: usa o último candidato
                # (janelas de aplicações como IDEs tendem a ser listadas antes)
                chosen = candidates[-1]
                logger.warning(
                    f"Não foi possível identificar automaticamente a janela do jogo. "
                    f"Usando: '{chosen[1]}'. "
                    f"Se errado, ajuste 'window_title_keyword' no config.json."
                )
        else:
            chosen = candidates[0]

        self.hwnd, title, _ = chosen
        logger.info(f"Janela selecionada: '{title}' (hwnd={self.hwnd})")

    def refresh_window(self):
        """
        Re-busca o HWND caso o handle tenha se tornado inválido
        (ex: cliente reconectou ou foi reaberto).
        """
        try:
            if not win32gui.IsWindow(self.hwnd):
                logger.warning("Handle da janela inválido. Tentando re-localizar...")
                self._find_window()
        except Exception:
            self._find_window()

    # ------------------------------------------------------------------
    # Área de cliente (exclui barra de título e bordas)
    # ------------------------------------------------------------------

    def get_client_size(self):
        """Retorna (width, height) da área útil de cliente da janela."""
        left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
        return (right - left), (bottom - top)

    # ------------------------------------------------------------------
    # Captura principal via PrintWindow (background-capable)
    # ------------------------------------------------------------------

    def capture_window(self):
        """
        Captura a área de cliente inteira da janela do Tibia sem precisar
        que ela esteja em primeiro plano.

        Returns:
            np.ndarray: Imagem BGR da área de cliente do Tibia.

        Raises:
            RuntimeError: Se a janela estiver minimizada ou se a captura falhar.
        """
        # Verifica se a janela não está minimizada (renderização suspensa)
        if win32gui.IsIconic(self.hwnd):
            raise RuntimeError(
                "A janela do Tibia está MINIMIZADA. "
                "Restaure-a (pode ficar por baixo de outras janelas) para o bot funcionar."
            )

        # Garante que o handle ainda é válido
        self.refresh_window()

        width, height = self.get_client_size()
        if width == 0 or height == 0:
            raise RuntimeError("Tamanho da área de cliente é zero. A janela pode estar minimizada.")

        # --- Cria os device contexts em memória ---
        hwnd_dc = None
        mem_dc = None
        bitmap = None

        try:
            # DC da janela-alvo
            hwnd_dc = win32gui.GetWindowDC(self.hwnd)
            dc_obj = win32ui.CreateDCFromHandle(hwnd_dc)

            # DC compatível em memória
            mem_dc = dc_obj.CreateCompatibleDC()

            # Bitmap de destino
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(dc_obj, width, height)
            mem_dc.SelectObject(bitmap)

            # PrintWindow via ctypes (não exposta no win32gui).
            # PW_RENDERFULLCONTENT instrui o DWM a renderizar em background.
            result = _user32.PrintWindow(self.hwnd, mem_dc.GetSafeHdc(), PW_RENDERFULLCONTENT)

            if not result:
                logger.warning(
                    "PrintWindow(PW_RENDERFULLCONTENT) retornou False. "
                    "Tentando fallback sem flag..."
                )
                # Fallback para janelas GDI clássicas sem DWM
                result = _user32.PrintWindow(self.hwnd, mem_dc.GetSafeHdc(), 0)
                if not result:
                    raise RuntimeError("PrintWindow falhou. A janela pode estar inacessível.")

            # Converte o bitmap para array NumPy
            bmp_info = bitmap.GetInfo()
            bmp_bytes = bitmap.GetBitmapBits(True)

            img = np.frombuffer(bmp_bytes, dtype=np.uint8)
            img.shape = (bmp_info["bmHeight"], bmp_info["bmWidth"], 4)  # BGRA

            # Converte BGRA → BGR (OpenCV padrão)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            return img_bgr

        finally:
            # Liberação rigorosa de recursos GDI para evitar memory/handle leaks
            try:
                if bitmap:
                    # DeleteObject também não está em win32gui — usa gdi32 via ctypes
                    _gdi32.DeleteObject(bitmap.GetHandle())
            except Exception:
                pass
            try:
                if mem_dc:
                    mem_dc.DeleteDC()
            except Exception:
                pass
            try:
                if hwnd_dc:
                    win32gui.ReleaseDC(self.hwnd, hwnd_dc)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Recorte relativo (substitui capture_region do MSS)
    # ------------------------------------------------------------------

    def capture_region(self, region: dict):
        """
        Captura a janela inteira e recorta a sub-região relativa à área de cliente.

        Args:
            region (dict): {"left": int, "top": int, "width": int, "height": int}
                           Coordenadas relativas ao canto superior-esquerdo da área de cliente.

        Returns:
            np.ndarray: Sub-imagem BGR recortada da região solicitada.
        """
        full = self.capture_window()
        h_full, w_full = full.shape[:2]

        left   = region["left"]
        top    = region["top"]
        width  = region["width"]
        height = region["height"]

        # Garante limites (evita crash se a janela foi redimensionada)
        right  = min(left + width,  w_full)
        bottom = min(top  + height, h_full)

        if left >= w_full or top >= h_full:
            logger.error(
                f"Região {region} está fora dos limites da janela ({w_full}x{h_full}). "
                "Recalibre o bot com scratch/calibrate.py."
            )
            return np.zeros((height, width, 3), dtype=np.uint8)

        return full[top:bottom, left:right]

    # ------------------------------------------------------------------
    # Compatibilidade e limpeza
    # ------------------------------------------------------------------

    def close(self):
        """Sem recursos persistentes para liberar nesta implementação."""
        logger.info("WindowCapturer encerrado.")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# Alias de compatibilidade (módulos antigos que importem ScreenCapturer)
ScreenCapturer = WindowCapturer
