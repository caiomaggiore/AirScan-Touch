# Changelog - AirScan Control

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [1.0] - 2025-10-03

### Adicionado
- Sistema principal de controle de mouse via AirScan
- Sistema de calibração visual com interface em tela cheia
- 5 pontos de calibração nas extremidades da tela
- Sistema de cores intuitivo (verde/vermelho/amarelo)
- Pausa de 5 segundos entre pontos para reposicionamento
- Detecção de interrupção em 500ms sem dados
- Layout otimizado sem sobreposições
- Dados OSC discretos no canto superior direito
- Feedback visual completo com barras de progresso
- Instruções claras para cada estado
- Sistema robusto com validação rigorosa
- Ajuste automático para limites da tela
- Logs otimizados (500ms para coordenadas, 1s para warnings)
- Atalho de teclado Shift+C para calibração
- Arquivo de configuração JSON
- Documentação completa
- Scripts de instalação

### Funcionalidades Técnicas
- Servidor OSC na porta 8082
- Canais: /airscan/blob/6/x, /airscan/blob/6/y, /airscan/blob/6/z
- Mapeamento inteligente de coordenadas
- Validação de dados contínuos
- Sistema de estados robusto
- Tratamento de erros abrangente
- Limpeza automática de recursos

### Interface
- Overlay em tela cheia para calibração
- Pontos visuais com crosshair
- Barras de progresso animadas
- Status OSC em tempo real
- Coordenadas em tempo real
- Instruções contextuais
- Feedback de sucesso detalhado

### Arquivos
- `airscan_control.py` - Sistema principal
- `airscan_calibration.py` - Sistema de calibração
- `AirScan_Calibration_Data.json` - Dados de calibração
- `requirements.txt` - Dependências
- `install.bat` - Script de instalação
- `config.json` - Configurações
- `README.md` - Documentação
- `CHANGELOG.md` - Este arquivo

---

## Próximas Versões

### [1.1] - Planejado
- [ ] Melhorias de performance
- [ ] Configurações avançadas
- [ ] Suporte a múltiplas resoluções
- [ ] Calibração automática inteligente

### [1.2] - Planejado
- [ ] Interface gráfica para configurações
- [ ] Logs detalhados em arquivo
- [ ] Suporte a perfis de calibração
- [ ] Modo de teste

### [2.0] - Planejado
- [ ] Arquitetura modular
- [ ] Plugin system
- [ ] API REST
- [ ] Dashboard web
