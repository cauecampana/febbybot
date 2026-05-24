import cv2
import numpy as np
import logging

logger = logging.getLogger("febbyBot")

class BarDetector:
    """
    Processa imagens de barras de status (HP, Mana, etc.) do Tibia usando OpenCV e NumPy.
    Calcula o percentual de preenchimento utilizando filtragem HSV e máscaras de cores.
    """
    def __init__(self, hsv_ranges, label="Bar"):
        """
        Inicializa o detector com os limites HSV configurados.
        
        Args:
            hsv_ranges (list): Lista de dicionários contendo {"min": [H,S,V], "max": [H,S,V]}
            label (str): Rótulo identificador do tipo de barra (ex: "HP", "Mana") para logs/debug
        """
        self.hsv_ranges = hsv_ranges
        self.label = label
        logger.info(f"Módulo BarDetector ({self.label}) inicializado com sucesso.")

    def get_percentage(self, img_bgr, debug_save_path=None):
        """
        Calcula a porcentagem preenchida na imagem da barra capturada.
        
        Args:
            img_bgr (np.ndarray): Imagem da barra em BGR.
            debug_save_path (str, optional): Caminho para salvar uma imagem de debug (se fornecido).
            
        Returns:
            float: Porcentagem preenchida (de 0.0 a 100.0).
        """
        try:
            if img_bgr is None or img_bgr.size == 0:
                logger.error(f"BarDetector ({self.label}) recebeu uma imagem inválida ou vazia.")
                return 0.0

            # 1. Converter de BGR para HSV
            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            height, width = hsv.shape[:2]

            # 2. Criar máscara binária combinando os intervalos HSV configurados
            mask = np.zeros((height, width), dtype=np.uint8)
            for range_data in self.hsv_ranges:
                lower = np.array(range_data["min"], dtype=np.uint8)
                upper = np.array(range_data["max"], dtype=np.uint8)
                
                # Cria a máscara para a faixa atual
                current_mask = cv2.inRange(hsv, lower, upper)
                # Combina via OR lógico
                mask = cv2.bitwise_or(mask, current_mask)

            # 3. Calcular a porcentagem com base nas colunas ativas
            # Exige que pelo menos 15% dos pixels da coluna correspondam à cor configurada
            threshold_pixels_per_col = max(1, int(height * 0.15))
            col_sums = np.sum(mask > 0, axis=0)
            columns_active = col_sums >= threshold_pixels_per_col

            # Encontrar o índice da coluna ativa mais à direita
            active_indices = np.where(columns_active)[0]
            
            if len(active_indices) == 0:
                percentage = 0.0
            else:
                # O Tibia preenche da esquerda para a direita.
                # A porcentagem é a razão entre o último índice ativo detectado e a largura total da barra.
                max_active_col = np.max(active_indices) + 1
                percentage = (max_active_col / width) * 100.0

            # Garantir limite rígido entre 0% e 100%
            percentage = max(0.0, min(100.0, percentage))

            # 4. Salvar imagem para depuração visual se um caminho for fornecido
            if debug_save_path:
                self._save_debug_image(img_bgr, mask, percentage, debug_save_path)

            return round(percentage, 1)

        except Exception as e:
            logger.error(f"Erro no processamento da detecção de {self.label}: {e}")
            return 0.0

    def get_hp_percentage(self, img_bgr, debug_save_path=None):
        """Wrapper de compatibilidade retrátil para get_percentage."""
        return self.get_percentage(img_bgr, debug_save_path)

    def _save_debug_image(self, original, mask, percentage, path):
        """Gera e salva uma imagem combinada do print original e da máscara para ajudar na calibração."""
        try:
            # Converte a máscara binária para 3 canais BGR para empilhar
            mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            
            # Adiciona texto com a porcentagem na imagem original
            img_text = original.copy()
            cv2.putText(
                img_text, 
                f"{self.label}: {percentage:.1f}%", 
                (5, min(15, img_text.shape[0] - 2)), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.4, 
                (0, 255, 0) if self.label == "HP" else (255, 255, 0), 
                1
            )
            
            # Empilha verticalmente
            combined = np.vstack((img_text, mask_bgr))
            cv2.imwrite(path, combined)
        except Exception as e:
            logger.error(f"Erro ao salvar imagem de debug do detector de {self.label}: {e}")


# Alias de Compatibilidade Retrátil
HPDetector = BarDetector
