#!/usr/bin/env python3
"""
Script para encerramento forçado dos sistemas AirScan
Mata todos os processos Python que estão usando a porta 8030
"""

import subprocess
import sys
import os

AIRSCAN_PORT = 8030

def kill_processes_using_port(port):
    """Kill all processes using the specified port"""
    print(f"[KILL] Procurando processos usando porta {port}...")
    killed_count = 0
    
    try:
        if os.name == 'nt':  # Windows
            # Find processes using the port
            result = subprocess.run(
                ['netstat', '-ano'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            pids_to_kill = set()
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'UDP' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids_to_kill.add(pid)
            
            # Kill all processes using the port
            for pid in pids_to_kill:
                try:
                    subprocess.run(['taskkill', '/F', '/PID', pid], 
                                 capture_output=True, timeout=3)
                    print(f"[KILL] Processo {pid} finalizado")
                    killed_count += 1
                except:
                    print(f"[WARNING] Não foi possível finalizar processo {pid}")
                    
            if not pids_to_kill:
                print(f"[KILL] Nenhum processo encontrado usando porta {port}")
                
        else:  # Linux/Mac
            result = subprocess.run(['fuser', '-k', f'{port}/udp'], 
                         capture_output=True, timeout=3)
            print(f"[KILL] Processos usando porta {port} finalizados")
            killed_count = 1
            
    except Exception as e:
        print(f"[ERROR] Erro ao finalizar processos na porta {port}: {e}")
    
    return killed_count

def kill_python_airscan_processes():
    """Kill all Python processes related to AirScan"""
    print("[KILL] Procurando processos Python do AirScan...")
    killed_count = 0
    
    try:
        if os.name == 'nt':  # Windows
            # Find Python processes
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Get current process PID to avoid killing ourselves
            current_pid = str(os.getpid())
            
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if 'python.exe' in line:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        pid = parts[1].strip('"')
                        if pid != current_pid and pid.isdigit():
                            try:
                                subprocess.run(['taskkill', '/F', '/PID', pid],
                                             capture_output=True, timeout=3)
                                print(f"[KILL] Processo Python {pid} finalizado")
                                killed_count += 1
                            except:
                                pass
        else:  # Linux/Mac
            result = subprocess.run(['pkill', '-9', '-f', 'AirScan'],
                                  capture_output=True, timeout=3)
            print("[KILL] Processos Python do AirScan finalizados")
            killed_count = 1
            
    except Exception as e:
        print(f"[ERROR] Erro ao finalizar processos Python: {e}")
    
    return killed_count

def main():
    """Main function"""
    print("=" * 60)
    print("AIRSCAN - ENCERRAMENTO FORÇADO DE PROCESSOS")
    print("=" * 60)
    print("")
    
    # Kill processes using the port
    port_killed = kill_processes_using_port(AIRSCAN_PORT)
    
    print("")
    
    # Kill Python processes
    python_killed = kill_python_airscan_processes()
    
    print("")
    print("=" * 60)
    print(f"RESULTADO:")
    print(f"  • Processos na porta {AIRSCAN_PORT}: {port_killed} finalizados")
    print(f"  • Processos Python AirScan: {python_killed} finalizados")
    print("=" * 60)
    print("")
    print("✅ Todos os processos AirScan foram encerrados!")
    print("")

if __name__ == "__main__":
    main()

