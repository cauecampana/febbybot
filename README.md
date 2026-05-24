# 🧙 febbyBot — Tibia OT Visual Bot

Bot visual de alta performance para servidores **Tibia OT**, desenvolvido em Python.  
Monitora a barra de HP e Mana em tempo real via **captura de janela nativa (Win32 API)** e executa curas automáticas com múltiplas regras configuráveis — tudo sem leitura de memória ou injeção de código.

---

## ✨ Funcionalidades

- ✅ **Cura automática de HP** com múltiplos níveis de prioridade (ex: Exura a 85%, Exura Gran a 40%)
- ✅ **Recarga automática de Mana** (ex: Mana Potion a 70%)
- ✅ **Captura de janela em segundo plano** — funciona com Alt+Tab ou janela coberta
- ✅ **Coordenadas relativas à janela** — mova o Tibia livremente sem recalibrar
- ✅ **Cooldowns individuais** por regra, respeitando o exhaustion nativo do Tibia
- ✅ **Cura de HP e Mana paralela** — spells e poções disparam de forma independente
- ✅ **Calibração visual integrada** — seleciona HP e Mana na mesma captura
- ✅ **Suporte a DirectInput** (scancodes de hardware) para máxima compatibilidade com clientes Tibia
- ✅ **Logs detalhados** no terminal e em arquivo `bot.log`
- ✅ **Pausar / Retomar** com `HOME` | **Parar** com `END`

---

## 🗂️ Estrutura do Projeto

```text
febbyBot/
├── config.json              # Todas as configurações (janela, regiões, hotkeys, regras)
├── requirements.txt         # Dependências Python
├── main.py                  # Ponto de entrada do bot
│
├── src/
│   ├── config.py            # Carregamento e validação das configurações
│   ├── capture.py           # Captura de janela em segundo plano via Win32 API
│   ├── detector.py          # Detecção de HP/Mana por filtragem HSV (OpenCV)
│   ├── keyboard_handler.py  # Envio de teclas (alto nível + DirectInput nativo)
│   └── bot.py               # Engine principal de decisão e loop de cura
│
└── scratch/
    ├── calibrate.py         # Ferramenta gráfica de calibração (HP e Mana)
    ├── diagnose_capture.py  # Diagnóstico de captura em segundo plano
    └── test_bot.py          # Suite de testes com mocks de imagens sintéticas
```

---

## ⚙️ Pré-requisitos

- **Python 3.10+** (testado com Python 3.14)
- **Windows 10 / 11**
- Tibia OT rodando em modo **janela** (não minimizado)
- Terminal executado como **Administrador** (necessário para envio de hotkeys globais)

---

## 🚀 Instalação

```bash
# 1. Clone ou baixe o projeto
cd c:\Users\cauec\OneDrive\Documentos\febbyBot

# 2. Instale as dependências
py -m pip install -r requirements.txt
```

---

## 🎯 Como Usar

### Passo 1 — Calibração (primeira vez ou ao mudar de personagem/resolução)

```bash
py scratch/calibrate.py
```

1. Deixe a janela do Tibia **aberta** (pode estar por baixo do terminal).
2. Pressione `ENTER` — o script captura o frame do jogo automaticamente.
3. Selecione a **barra de HP** com o mouse → pressione `ENTER`.
4. Selecione a **barra de Mana** com o mouse → pressione `ENTER`.
5. As coordenadas são salvas em `config.json` automaticamente.

> 💡 **Não precisa de Alt+Tab!** A captura é feita diretamente via Win32 API.

---

### Passo 2 — Executar o bot

```bash
# Como Administrador (necessário para hotkeys globais dentro do jogo)
py main.py
```

O HUD em tempo real será exibido no terminal:
```
[HUD] HP: 87.3% | MANA: 65.1% | Status: ATIVO
[AÇÃO - HP] Cura Leve (Manutenção) Ativada! HP: 84.5% <= 85% | Tecla F2
[AÇÃO - MANA] Usar Mana Potion Ativada! Mana: 68.2% <= 70% | Tecla F3
```

| Tecla  | Ação                       |
|--------|----------------------------|
| `HOME` | Pausar / Retomar o bot     |
| `END`  | Encerrar o bot com segurança |

---

## 📝 Configuração (`config.json`)

```json
{
  "window_title_keyword": "Tibia",
  "hp_bar_region":   { "left": 100, "top": 40, "width": 150, "height": 12 },
  "mana_bar_region": { "left": 260, "top": 40, "width": 150, "height": 12 },
  "loop_delay_seconds": 0.05,
  "input_method": "keyboard",

  "hsv_ranges": [
    { "min": [0, 100, 100],   "max": [85, 255, 255]  },
    { "min": [160, 100, 100], "max": [180, 255, 255] }
  ],
  "mana_hsv_ranges": [
    { "min": [90, 100, 100], "max": [130, 255, 255] }
  ],

  "healing_rules": [
    { "name": "Cura Urgente",     "max_hp_percentage": 40, "hotkey": "F1", "cooldown_ms": 1000 },
    { "name": "Cura Manutenção",  "max_hp_percentage": 85, "hotkey": "F2", "cooldown_ms": 500  }
  ],
  "mana_rules": [
    { "name": "Mana Potion", "max_mana_percentage": 70, "hotkey": "F3", "cooldown_ms": 1000 }
  ]
}
```

### Parâmetros Principais

| Campo                   | Descrição                                                                 |
|-------------------------|---------------------------------------------------------------------------|
| `window_title_keyword`  | Fragmento do título da janela do Tibia (ex: `"Tibia"`, `"Taleon"`)       |
| `hp_bar_region`         | Coordenadas relativas da barra de HP na janela do jogo                   |
| `mana_bar_region`       | Coordenadas relativas da barra de Mana na janela do jogo                 |
| `loop_delay_seconds`    | Intervalo do ciclo de detecção (padrão: `0.05` = 20 ciclos/segundo)      |
| `input_method`          | `"keyboard"` (padrão) ou `"directinput"` (scancodes de hardware)         |
| `hsv_ranges`            | Faixas HSV da cor da barra de HP (verde/amarelo/vermelho)                |
| `mana_hsv_ranges`       | Faixas HSV da cor da barra de Mana (azul)                                |
| `healing_rules`         | Lista de regras de cura de HP (ordenadas por prioridade automaticamente) |
| `mana_rules`            | Lista de regras de recarga de Mana                                       |

### Adicionando mais regras de cura

Basta adicionar entradas à lista `healing_rules` ou `mana_rules`:

```json
"healing_rules": [
  { "name": "Crítico",     "max_hp_percentage": 20,  "hotkey": "F1", "cooldown_ms": 1000 },
  { "name": "Baixo",       "max_hp_percentage": 50,  "hotkey": "F2", "cooldown_ms": 800  },
  { "name": "Manutenção",  "max_hp_percentage": 85,  "hotkey": "F3", "cooldown_ms": 500  }
]
```

O bot ordena as regras automaticamente — a mais urgente (menor %) sempre tem prioridade.

---

## 🔬 Arquitetura Técnica

### Captura em Segundo Plano (Win32 API)
O módulo `src/capture.py` utiliza `PrintWindow` com a flag `PW_RENDERFULLCONTENT`, que instrui o DWM (Desktop Window Manager) do Windows a renderizar a janela do Tibia em um buffer de memória, mesmo que ela esteja completamente coberta por outras janelas.

**Resultado:** Latência de captura de **2–4ms**, sem necessitar que a janela esteja em foco. A janela apenas não pode ser **minimizada** (o Windows suspende a renderização de janelas minimizadas).

### Detecção por Filtragem HSV (OpenCV)
O módulo `src/detector.py` implementa a classe `BarDetector`, usada tanto para HP quanto para Mana:
1. Converte a imagem BGR → HSV (mais estável que RGB para detecção de cores).
2. Aplica máscaras binárias para os intervalos de cor configurados.
3. Varre as colunas da esquerda para a direita para encontrar o limite de preenchimento.
4. Calcula a porcentagem com precisão de **< 1% de desvio**.

### Envio de Teclas Dual (keyboard + DirectInput)
O módulo `src/keyboard_handler.py` suporta dois métodos:
- `keyboard` (padrão): Envio via API de alto nível do Windows.
- `directinput`: Envio via `ctypes.windll.user32.SendInput` com scancodes de hardware, útil para clientes que filtram inputs sintéticos.

---

## 🛠️ Ferramentas Auxiliares

### Diagnóstico de Captura
```bash
py scratch/diagnose_capture.py
```
Verifica se a captura em segundo plano está funcionando corretamente. Cobre a janela do Tibia com o navegador durante os 3 segundos de contagem — se o frame capturado mostrar o jogo, tudo funciona perfeitamente!

### Suite de Testes
```bash
py scratch/test_bot.py
```
Executa testes automatizados com imagens sintéticas de barras de HP e Mana, validando a precisão do detector sem necessitar o jogo aberto.

---

## ⚠️ Avisos

- O bot deve ser executado em um terminal **como Administrador** para que o envio de hotkeys funcione dentro do jogo.
- **Não minimize** a janela do Tibia — o Windows suspende a renderização de janelas minimizadas.
- As coordenadas de HP e Mana no `config.json` são **relativas à janela do jogo**. Você pode mover a janela livremente. Apenas recalibre se **redimensionar** significativamente o cliente.
- Este bot utiliza apenas captura visual externa. Não lê memória, não injeta DLLs e não modifica arquivos do jogo.

---

## 📜 Licença

Projeto de uso pessoal. Use com responsabilidade e de acordo com as regras do servidor OT que você joga.
