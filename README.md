# AirScan Control v1.1

Sistema de controle de mouse via AirScan com calibração multi-nível e interface moderna.

## 🚀 Novidades da v1.1

### ✨ Sistema Multi-Nível de Calibração
- **3 níveis de precisão** disponíveis
- **Seleção interativa** com mouse
- **Interface moderna** com design atualizado
- **Pontos otimizados** para cada nível

### 🎯 Níveis de Calibração

#### 🟢 BÁSICO (5 pontos)
- **Pontos**: Cantos + Centro
- **Tempo**: ~25 segundos
- **Precisão**: Boa para uso geral
- **Ideal para**: Uso diário, apresentações

#### 🟡 AVANÇADO (9 pontos)
- **Pontos**: Cantos + Bordas + Centro
- **Tempo**: ~45 segundos
- **Precisão**: Excelente precisão
- **Ideal para**: Trabalho profissional, design

#### 🔴 PROFISSIONAL (13 pontos)
- **Pontos**: Cantos + Bordas + Quartos + Centro
- **Tempo**: ~65 segundos
- **Precisão**: Precisão máxima
- **Ideal para**: Aplicações críticas, precisão extrema

## 🎨 Interface Modernizada

### Design Atualizado
- **Fundo escuro** (#1a1a1a) para melhor visibilidade
- **Cores vibrantes** com tema verde/azul
- **Pontos com glow** para melhor visibilidade
- **Barras de progresso** mais largas e visíveis
- **Tipografia moderna** com hierarquia clara

### Experiência do Usuário
- **Seleção visual** de níveis com mouse
- **Feedback imediato** em todas as ações
- **Instruções contextuais** para cada estado
- **Progresso visual** detalhado
- **Transições suaves** entre estados

## 📁 Estrutura de Arquivos

```
AirScan_v1.1/
├── airscan_control.py           # Sistema principal (v1.0)
├── airscan_calibration.py       # Sistema de calibração (v1.0)
├── airscan_calibration_v1.1.py  # Sistema de calibração v1.1
├── AirScan_Calibration_Data_v1.1.json   # Dados de calibração
└── README.md                    # Esta documentação
```

## 🛠️ Instalação

### Dependências
```bash
pip install python-osc pyautogui keyboard
```

### Execução
```bash
# Sistema principal (v1.0)
python airscan_control.py

# Calibração v1.1 (nova)
python airscan_calibration_v1.1.py
```

## 🎯 Como Usar

### 1. Iniciar Sistema
```bash
python airscan_control.py
```

### 2. Calibração v1.1
```bash
python airscan_calibration_v1.1.py
```

### 3. Seleção de Nível
1. **Interface de seleção** aparece automaticamente
2. **Clique no nível** desejado com o mouse
3. **Sistema inicia** calibração do nível escolhido
4. **Siga as instruções** na tela

### 4. Processo de Calibração
- **Ponto VERDE**: Posicione a mão e aguarde detecção
- **Ponto VERMELHO**: Mantenha a mão firme por 5 segundos
- **Ponto AMARELO**: Vá para o próximo ponto
- **Repita** para todos os pontos do nível escolhido

## ⚙️ Configuração

### Níveis de Calibração

#### Básico (5 pontos)
```
TOP_LEFT     TOP_RIGHT
     CENTER
BOTTOM_LEFT  BOTTOM_RIGHT
```

#### Avançado (9 pontos)
```
TOP_LEFT     TOP_CENTER     TOP_RIGHT
LEFT_CENTER  CENTER         RIGHT_CENTER
BOTTOM_LEFT  BOTTOM_CENTER  BOTTOM_RIGHT
```

#### Profissional (13 pontos)
```
TOP_LEFT     TOP_LEFT_QUARTER  TOP_CENTER     TOP_RIGHT_QUARTER  TOP_RIGHT
LEFT_CENTER  CENTER            CENTER         CENTER             RIGHT_CENTER
BOTTOM_LEFT  BOTTOM_LEFT_QUARTER BOTTOM_CENTER BOTTOM_RIGHT_QUARTER BOTTOM_RIGHT
```

### Parâmetros
- **Duração de coleta**: 5 segundos contínuos
- **Pausa entre pontos**: 5 segundos
- **Threshold de interrupção**: 500ms
- **Porta OSC**: 8082

## 📊 Dados de Calibração v1.1

O arquivo `AirScan_Calibration_Data_v1.1.json` agora inclui:
```json
{
  "points": {
    "TOP_LEFT": {
      "screen": {"x": 0, "y": 0},
      "airscan": {"x": 87.51, "y": 367.58}
    }
  },
  "screen": {"width": 1920, "height": 1080},
  "airscan": {"width": 1920, "height": 1080, "port": 8082},
  "calibration_level": "basic",
  "calibration_version": "1.1",
  "total_points": 5
}
```

## 🎨 Melhorias Visuais

### Cores e Temas
- **Fundo**: #1a1a1a (escuro profissional)
- **Verde**: #00ff88 (AirScan brand)
- **Vermelho**: #ff4444 (coletando)
- **Amarelo**: #ffaa00 (pausa)
- **Azul**: #44aaff (informações)
- **Branco**: #ffffff (texto principal)

### Elementos Visuais
- **Pontos com glow** para melhor visibilidade
- **Crosshair** mais espesso e visível
- **Barras de progresso** mais largas
- **Caixas de seleção** com bordas coloridas
- **Tipografia** hierárquica e legível

## 🔧 Compatibilidade

### Versões
- **v1.0**: Sistema principal mantido
- **v1.1**: Nova calibração multi-nível
- **Compatibilidade**: Total entre versões

### Migração
- **Dados v1.0**: Funcionam na v1.1
- **Dados v1.1**: Funcionam na v1.0
- **Upgrade**: Automático e transparente

## 🚀 Próximas Versões

### v1.2 (Planejado)
- [ ] Interface gráfica para configurações
- [ ] Perfis de calibração personalizados
- [ ] Modo de teste sem calibração
- [ ] Logs detalhados em arquivo

### v2.0 (Planejado)
- [ ] Arquitetura modular
- [ ] Plugin system
- [ ] API REST
- [ ] Dashboard web

## 📝 Changelog

### v1.1 (2025-10-03)
- ✨ Sistema multi-nível de calibração
- 🎨 Interface moderna com design atualizado
- 🎯 3 níveis: Básico (5), Avançado (9), Profissional (13)
- 🖱️ Seleção interativa com mouse
- 🎨 Cores e temas modernizados
- 📊 Dados de calibração expandidos
- 🔧 Compatibilidade total com v1.0

---

**Desenvolvido para Accenture Innovation Hub**  
**Touch-Airscan Project v1.1**
