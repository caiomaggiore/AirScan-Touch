# Changelog - AirScan Control

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [1.1] - 2025-10-03

### Adicionado
- Sistema multi-nível de calibração
- Interface moderna com design atualizado
- 3 níveis: Básico (5), Avançado (9), Profissional (13)
- Seleção interativa com mouse
- Cores e temas modernizados
- Pontos com glow para melhor visibilidade
- Barras de progresso mais largas
- Tipografia hierárquica
- Compatibilidade total com v1.0

### Melhorado
- Design da interface com tema escuro
- Cores vibrantes e profissionais
- Experiência do usuário mais intuitiva
- Feedback visual aprimorado
- Layout mais organizado e limpo

### Técnico
- Sistema de seleção de níveis
- Geração dinâmica de pontos de calibração
- Dados de calibração expandidos
- Configurações por nível
- Estrutura modular para futuras expansões

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

---

## Próximas Versões

### [1.2] - Planejado
- [ ] Interface gráfica para configurações
- [ ] Perfis de calibração personalizados
- [ ] Modo de teste sem calibração
- [ ] Logs detalhados em arquivo
- [ ] Suporte a múltiplas resoluções

### [2.0] - Planejado
- [ ] Arquitetura modular
- [ ] Plugin system
- [ ] API REST
- [ ] Dashboard web
- [ ] Suporte multi-dispositivo
