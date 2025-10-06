# AirScan Control Project

Sistema de controle de mouse via AirScan com calibração visual e interface moderna.

## 📁 Estrutura do Projeto

```
Touch-Airscan/
├── _old/                          # Arquivos antigos e temporários
├── AirScan_v1.0/                  # Versão 1.0 - Estável
│   ├── AirScan_Control_v1.0.py    # Sistema principal
│   ├── AirScan_Calibration_v1.0.py # Sistema de calibração
│   ├── AirScan_Calibration_Data.json # Dados de calibração
│   ├── README.md                  # Documentação v1.0
│   ├── CHANGELOG.md               # Histórico de mudanças
│   ├── requirements.txt           # Dependências
│   └── install.bat               # Script de instalação
└── AirScan_v1.1/                  # Versão 1.1 - Modernizada
    ├── AirScan_Control_v1.1.py    # Sistema principal
    ├── AirScan_Calibration_v1.1.py # Sistema de calibração multi-nível
    ├── AirScan_Calibration_Data.json # Dados de calibração
    ├── AirScan_Config_v1.1.json   # Configurações v1.1
    ├── README.md                  # Documentação v1.1
    ├── CHANGELOG.md               # Histórico de mudanças
    ├── requirements.txt           # Dependências
    └── install.bat               # Script de instalação
```

## 🚀 Versões Disponíveis

### 📦 AirScan v1.0 - Estável
- **Sistema básico** com 5 pontos de calibração
- **Interface funcional** e robusta
- **Ideal para**: Uso diário, apresentações
- **Tempo de calibração**: ~25 segundos

### 🎯 AirScan v1.1 - Modernizada
- **Sistema multi-nível** com 3 opções de calibração
- **Interface moderna** com design atualizado
- **Níveis disponíveis**:
  - 🟢 **Básico** (5 pontos, ~25s)
  - 🟡 **Avançado** (9 pontos, ~45s)
  - 🔴 **Profissional** (13 pontos, ~65s)

## 🛠️ Instalação Rápida

### v1.0
```bash
cd AirScan_v1.0
install.bat
python AirScan_Control_v1.0.py
```

### v1.1 (Recomendado)
```bash
cd AirScan_v1.1
install.bat
python AirScan_Control_v1.1.py
```

## 🎯 Como Usar

### 1. Iniciar Sistema
```bash
python AirScan_Control_v1.1.py
```

### 2. Calibração
```bash
python AirScan_Calibration_v1.1.py
```

### 3. Seleção de Nível (v1.1)
1. **Interface de seleção** aparece automaticamente
2. **Clique no nível** desejado (Básico/Avançado/Profissional)
3. **Siga as instruções** na tela

## ⚙️ Configuração

### Dependências
```bash
pip install python-osc pyautogui keyboard
```

### Portas OSC
- **Porta padrão**: 8082
- **Canais**: /airscan/blob/6/x, /airscan/blob/6/y, /airscan/blob/6/z

### Arquivos de Dados
- **Calibração**: `AirScan_Calibration_Data.json`
- **Configuração**: `AirScan_Config_v1.1.json` (v1.1)

## 📊 Níveis de Calibração (v1.1)

### 🟢 Básico (5 pontos)
```
TOP_LEFT     TOP_RIGHT
     CENTER
BOTTOM_LEFT  BOTTOM_RIGHT
```

### 🟡 Avançado (9 pontos)
```
TOP_LEFT     TOP_CENTER     TOP_RIGHT
LEFT_CENTER  CENTER         RIGHT_CENTER
BOTTOM_LEFT  BOTTOM_CENTER  BOTTOM_RIGHT
```

### 🔴 Profissional (13 pontos)
```
TOP_LEFT     TOP_LEFT_QUARTER  TOP_CENTER     TOP_RIGHT_QUARTER  TOP_RIGHT
LEFT_CENTER  CENTER            CENTER         CENTER             RIGHT_CENTER
BOTTOM_LEFT  BOTTOM_LEFT_QUARTER BOTTOM_CENTER BOTTOM_RIGHT_QUARTER BOTTOM_RIGHT
```

## 🔧 Compatibilidade

### Versões
- **v1.0**: Sistema básico e estável
- **v1.1**: Sistema modernizado com múltiplos níveis
- **Compatibilidade**: Total entre versões

### Dados
- **Arquivos de calibração** funcionam entre versões
- **Upgrade transparente** e automático
- **Migração** sem perda de dados

## 📝 Changelog

### v1.1 (2025-10-03)
- ✨ Sistema multi-nível de calibração
- 🎨 Interface moderna com design atualizado
- 🎯 3 níveis: Básico (5), Avançado (9), Profissional (13)
- 🖱️ Seleção interativa com mouse
- 🎨 Cores e temas modernizados

### v1.0 (2025-10-03)
- 🚀 Versão inicial estável
- 🎯 Sistema de calibração visual
- 🔧 Controle de mouse via AirScan
- 📊 5 pontos de calibração
- 🎨 Interface funcional

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

## 🏆 Conquistas

- ✅ **Sistema completo** e funcional
- ✅ **Múltiplas versões** organizadas
- ✅ **Documentação completa** para cada versão
- ✅ **Compatibilidade total** entre versões
- ✅ **Estrutura organizada** e padronizada
- ✅ **Nomes padronizados** para todos os arquivos

---

**Desenvolvido para Accenture Innovation Hub**  
**Touch-Airscan Project**

*Versões organizadas e prontas para uso!*
