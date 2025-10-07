# 🚨 Comandos de Emergência - AirScan

## Encerramento Forçado de Todos os Processos

Se os sistemas AirScan não estiverem respondendo aos comandos normais (ESC, Ctrl+C, Ctrl+Q), use:

### Windows:
```bash
# Método 1: Script Python (RECOMENDADO)
python kill_airscan.py

# Método 2: PowerShell
# Matar processos na porta 8030
netstat -ano | findstr :8030
taskkill /F /PID <PID_ENCONTRADO>

# Matar todos os processos Python
taskkill /F /IM python.exe
```

### Linux/Mac:
```bash
# Método 1: Script Python (RECOMENDADO)
python3 kill_airscan.py

# Método 2: Terminal
# Matar processos na porta 8030
fuser -k 8030/udp

# Matar processos AirScan
pkill -9 -f AirScan
```

---

## Comandos Normais de Encerramento

### AirScan_Control.py
- **Ctrl+Q**: Encerramento normal
- **Ctrl+C**: Encerramento via sinal (no console)

### AirScan_Calibration.py
- **ESC**: Cancelar calibração e encerrar
- **Fechar janela (X)**: Cancelar calibração

---

## Verificar se Porta está em Uso

### Windows:
```bash
netstat -ano | findstr :8030
```

### Linux/Mac:
```bash
lsof -i :8030
```

---

## Reiniciar Sistema do Zero

```bash
# 1. Encerrar todos os processos
python kill_airscan.py

# 2. Aguardar 2 segundos
# (Windows: timeout /t 2)
# (Linux/Mac: sleep 2)

# 3. Iniciar sistema de controle
python AirScan_Control.py
```

---

## Problemas Comuns

### Problema: "Porta 8030 está em uso"
**Solução:**
```bash
python kill_airscan.py
```

### Problema: "Múltiplas janelas de calibração abrem"
**Solução:**
- ESC para fechar todas
- Aguardar processos encerrarem
- Usar `python kill_airscan.py` se necessário

### Problema: "Sistema não responde a Ctrl+C"
**Solução:**
```bash
# Windows
taskkill /F /IM python.exe

# Linux/Mac
pkill -9 -f AirScan
```

### Problema: "Calibração trava/não fecha com ESC"
**Solução:**
```bash
python kill_airscan.py
```

---

## Logs e Debugging

Para verificar se há processos rodando:

### Windows:
```bash
tasklist | findstr python.exe
```

### Linux/Mac:
```bash
ps aux | grep python | grep AirScan
```

