# AirScan Control v1.0

Sistema de controle de mouse via AirScan com calibração automática e interface visual intuitiva.

## 🚀 Funcionalidades

### Sistema Principal (airscan_control.py)
- **Controle de mouse** via coordenadas OSC do AirScan
- **Calibração automática** com 5 pontos de referência
- **Mapeamento inteligente** de coordenadas AirScan para tela
- **Logs otimizados** (500ms para coordenadas, 1s para warnings)
- **Atalho de teclado** Shift+C para iniciar calibração
- **Ajuste automático** para limites da tela

### Sistema de Calibração (airscan_calibration.py)
- **Interface visual** em tela cheia com overlay
- **5 pontos de calibração** nas extremidades da tela
- **Sistema de cores intuitivo**:
  - 🟢 **VERDE**: Pronto para receber dados
  - 🔴 **VERMELHO**: Coletando dados (5s contínuos)
  - 🟡 **AMARELO**: Pausa/reposicionamento (5s)
- **Detecção de interrupção** (500ms sem dados = reset)
- **Pausa entre pontos** para reposicionamento
- **Feedback visual completo** com barras de progresso
- **Dados OSC discretos** no canto superior direito

## 📁 Estrutura de Arquivos

```
AirScan_v1.0/
├── airscan_control.py      # Sistema principal de controle
├── airscan_calibration.py  # Sistema de calibração visual
├── AirScan_Calibration_Data.json   # Dados de calibração salvos
└── README.md              # Esta documentação
```

## 🛠️ Instalação

### Dependências
```bash
pip install python-osc pyautogui keyboard
```

### Execução
```bash
# Iniciar sistema principal
python airscan_control.py

# Calibração (ou pressione Shift+C no sistema principal)
python airscan_calibration.py
```

## 🎯 Como Usar

### 1. Iniciar Sistema
```bash
python airscan_control.py
```
- Sistema inicia servidor OSC na porta 8082
- Carrega dados de calibração automaticamente
- Mostra status de calibração ativa

### 2. Calibração
- Pressione **Shift+C** durante execução do sistema
- Ou execute diretamente: `python airscan_calibration.py`
- Siga as instruções na tela:
  1. **Ponto VERDE**: Posicione a mão e aguarde detecção
  2. **Ponto VERMELHO**: Mantenha a mão firme por 5 segundos
  3. **Ponto AMARELO**: Vá para o próximo ponto
  4. Repita para todos os 5 pontos

### 3. Controle de Mouse
- Após calibração, o sistema mapeia automaticamente
- Coordenadas AirScan são convertidas para posições da tela
- Cliques são detectados via canal Z do OSC

## ⚙️ Configuração

### Portas OSC
- **Porta padrão**: 8082
- **Canais**: /airscan/blob/6/x, /airscan/blob/6/y, /airscan/blob/6/z

### Pontos de Calibração
- **TOP_LEFT**: (0, 0) - Canto superior esquerdo
- **TOP_RIGHT**: (1920, 0) - Canto superior direito  
- **BOTTOM_RIGHT**: (1920, 1080) - Canto inferior direito
- **BOTTOM_LEFT**: (0, 1080) - Canto inferior esquerdo
- **CENTER**: (960, 540) - Centro da tela

### Parâmetros Ajustáveis
- **Duração de coleta**: 5 segundos contínuos
- **Pausa entre pontos**: 5 segundos
- **Threshold de interrupção**: 500ms
- **Intervalo de logs**: 500ms (coordenadas), 1s (warnings)

## 📊 Dados de Calibração

O arquivo `AirScan_Calibration_Data.json` contém:
```json
{
  "points": {
    "TOP_LEFT": {
      "screen": {"x": 0, "y": 0},
      "airscan": {"x": 87.51, "y": 367.58}
    },
    // ... outros pontos
  },
  "screen": {"width": 1920, "height": 1080},
  "airscan": {"width": 1920, "height": 1080, "port": 8082}
}
```

## 🔧 Solução de Problemas

### Problemas Comuns
1. **Porta em uso**: Feche outros processos usando a porta 8082
2. **Calibração inválida**: Execute nova calibração com Shift+C
3. **Dados não salvos**: Verifique permissões de escrita na pasta
4. **Interrupção frequente**: Verifique estabilidade do sinal AirScan

### Logs Importantes
- `[INFO]`: Status normal do sistema
- `[WARNING]`: Avisos sobre calibração
- `[ERROR]`: Erros que precisam atenção
- `[CALIBRAÇÃO]`: Status do processo de calibração

## 🎉 Melhorias da v1.0

- ✅ **Sistema de cores intuitivo** (verde/vermelho/amarelo)
- ✅ **Pausa entre pontos** para reposicionamento
- ✅ **Detecção de interrupção** inteligente
- ✅ **Layout otimizado** sem sobreposições
- ✅ **Pontos nas extremidades** da tela
- ✅ **Feedback visual completo** com progresso
- ✅ **Dados OSC discretos** no canto
- ✅ **Instruções claras** para cada estado
- ✅ **Sistema robusto** com validação rigorosa

## 📝 Changelog

### v1.0 (2025-10-03)
- Versão inicial estável
- Sistema de calibração visual completo
- Controle de mouse via AirScan
- Interface otimizada e funcional
- Documentação completa

---

**Desenvolvido para Accenture Innovation Hub**  
**Touch-Airscan Project**
