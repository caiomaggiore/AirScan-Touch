from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server
import pyautogui
import json
import subprocess
import sys
import os
import time
import threading
from threading import Event
from collections import deque
import socket
import signal

# Disable PyAutoGUI failsafe
pyautogui.FAILSAFE = False

# Screen dimensions
screen_width, screen_height = pyautogui.size()

# ====================================
# CONFIGURAÇÃO DO AIRSCAN
# ====================================
AIRSCAN_MODE = "Arena"  # Opções: "Arena" ou "Cave"
AIRSCAN_PORT = 8030

# Configurações de Performance
MOUSE_UPDATE_RATE = 60  # Hz - Taxa de atualização do mouse (60Hz recomendado)
SMOOTHING_SAMPLES = 5   # Número de amostras para média móvel (3-10 recomendado)
MOUSE_RELEASE_DELAY = 0.3  # segundos - Delay antes de soltar o mouse (grace period)
POSITION_STABILIZE_DELAY = 0.1  # segundos - Delay para estabilizar posição antes do clique
STABILITY_RADIUS = 15  # pixels - Raio de tolerância para considerar posição estável
STABILITY_TIME = 0.1  # segundos - Tempo que deve permanecer dentro do raio para estabilizar

# Configurações padrão por modo
MODE_CONFIG = {
    "Arena": {
        "blob_id": 5,
        "width": 1920,
        "height": 1080
    },
    "Cave": {
        "blob_id": 6,
        "width": 1920,
        "height": 1080
    }
}

# Carrega configuração do modo selecionado
if AIRSCAN_MODE not in MODE_CONFIG:
    print(f"[ERROR] Modo '{AIRSCAN_MODE}' inválido! Use 'Arena' ou 'Cave'")
    sys.exit(1)

CURRENT_CONFIG = MODE_CONFIG[AIRSCAN_MODE]
BLOB_ID = CURRENT_CONFIG["blob_id"]
DEFAULT_AIRSCAN_WIDTH = CURRENT_CONFIG["width"]
DEFAULT_AIRSCAN_HEIGHT = CURRENT_CONFIG["height"]

print(f"[INFO] Modo selecionado: {AIRSCAN_MODE} (Blob {BLOB_ID})")

class AirScanControl:
    def __init__(self):
        self.server = None
        self.running = True
        self.shutdown_event = Event()
        self.norm_x = None
        self.norm_y = None
        self.calibration_data = self.load_calibration()
        self.calibration_process = None
        self.calibration_complete = Event()
        self.last_log_time = 0
        self.log_interval = 0.5  # 500ms
        self.last_warning_time = 0
        self.warning_interval = 1.0  # 1 segundo
        
        # Throttling configurável (padrão 60Hz = ~16.67ms)
        self.last_update_time = 0
        self.update_interval = 1.0 / MOUSE_UPDATE_RATE
        
        # Suavização por média móvel configurável
        self.smoothing_window = SMOOTHING_SAMPLES
        self.x_history = deque(maxlen=self.smoothing_window)
        self.y_history = deque(maxlen=self.smoothing_window)
        
        # Sistema de detecção de dados (touch screen)
        self.last_data_time = 0  # Última vez que recebeu dados X/Y
        self.data_timeout = MOUSE_RELEASE_DELAY  # 0.3s sem dados = mouseUp
        self.mouse_pressed = False
        self.watchdog_timer = None  # Timer para detectar falta de dados
        self.initial_position_set = False  # Flag para evitar arrasto inicial
        
        # Sistema de estabilização por raio
        self.stable_position = None  # Posição estável atual (x, y)
        self.stability_start_time = 0  # Quando começou a estabilização
        self.is_position_stable = False  # Flag se posição está estável
        
        # Setup signal handlers for graceful shutdown
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"\n[INFO] Sinal {signum} recebido. Encerrando sistema...")
            self.shutdown_event.set()
            self.running = False
        
        # Handle Ctrl+C (SIGINT) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    def is_port_in_use(self, port):
        """Check if a port is in use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.bind(('0.0.0.0', port))
                return False
        except OSError:
            return True
    
    def wait_for_port_free(self, port, timeout=10):
        """Wait for port to become free"""
        print(f"[INFO] Aguardando porta {port} ficar livre...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if not self.is_port_in_use(port):
                print(f"[INFO] Porta {port} está livre!")
                return True
            time.sleep(0.5)
        
        print(f"[WARNING] Timeout aguardando porta {port} ficar livre")
        return False
    
    def kill_processes_using_port(self, port):
        """Kill processes using the specified port"""
        try:
            if os.name == 'nt':  # Windows
                # Find processes using the port
                result = subprocess.run(
                    ['netstat', '-ano'], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'UDP' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            try:
                                subprocess.run(['taskkill', '/F', '/PID', pid], 
                                             capture_output=True, timeout=5)
                                print(f"[INFO] Processo {pid} usando porta {port} finalizado")
                            except:
                                pass
            else:  # Linux/Mac
                subprocess.run(['fuser', '-k', f'{port}/udp'], 
                             capture_output=True, timeout=5)
                print(f"[INFO] Processos usando porta {port} finalizados")
                
        except Exception as e:
            print(f"[WARNING] Erro ao finalizar processos na porta {port}: {e}")
    
    def load_calibration(self):
        """Load calibration data from file"""
        default_config = {
            "points": {},
            "screen": {"width": screen_width, "height": screen_height},
            "airscan": {
                "width": DEFAULT_AIRSCAN_WIDTH,
                "height": DEFAULT_AIRSCAN_HEIGHT,
                "port": AIRSCAN_PORT
            }
        }
        
        try:
            with open('AirScan_Calibration_Data.json', 'r') as f:
                data = json.load(f)
                if "points" in data and data["points"]:
                    print(f"[INFO] Dados de calibração carregados: {len(data['points'])} pontos")
                    return data
                print("[WARNING] Arquivo de calibração encontrado, mas sem pontos válidos.")
        except FileNotFoundError:
            print("[INFO] Nenhum arquivo de calibração encontrado. Usando configuração padrão.")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Erro ao decodificar arquivo de calibração: {e}")
        except Exception as e:
            print(f"[ERROR] Erro inesperado ao carregar calibração: {e}")
        
        return default_config
    
    def map_range(self, value, in_min, in_max, out_min, out_max):
        """Map a value from one range to another"""
        if in_max == in_min:
            return out_min
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
    def get_calibrated_coordinates(self, x, y):
        """Convert AirScan coordinates to screen coordinates using calibration data"""
        if not self.calibration_data.get("points"):
            current_time = time.time()
            if current_time - self.last_warning_time >= self.warning_interval:
                print("[WARNING] Nenhum dado de calibração disponível. Usando mapeamento padrão.")
                self.last_warning_time = current_time
            return self.get_default_coordinates(x, y)
        
        try:
            x_values = [p["airscan"]["x"] for p in self.calibration_data["points"].values()]
            y_values = [p["airscan"]["y"] for p in self.calibration_data["points"].values()]
            
            if not x_values or not y_values:
                current_time = time.time()
                if current_time - self.last_warning_time >= self.warning_interval:
                    print("[WARNING] Dados de calibração vazios. Usando mapeamento padrão.")
                    self.last_warning_time = current_time
                return self.get_default_coordinates(x, y)
            
            min_x, max_x = min(x_values), max(x_values)
            min_y, max_y = min(y_values), max(y_values)
            
            # Validate ranges
            if min_x == max_x or min_y == max_y:
                current_time = time.time()
                if current_time - self.last_warning_time >= self.warning_interval:
                    print("[WARNING] Dados de calibração inválidos (ranges iguais). Usando mapeamento padrão.")
                    self.last_warning_time = current_time
                return self.get_default_coordinates(x, y)
            
            screen_x = self.map_range(x, min_x, max_x, 0, screen_width)
            screen_y = self.map_range(y, min_y, max_y, 0, screen_height)
            
            # Clamp coordinates to screen bounds
            screen_x = max(0, min(screen_width, screen_x))
            screen_y = max(0, min(screen_height, screen_y))
            
            return (int(screen_x), int(screen_y))
            
        except (KeyError, ValueError, TypeError) as e:
            print(f"[ERROR] Erro no mapeamento de calibração: {e}")
            return self.get_default_coordinates(x, y)
        except Exception as e:
            print(f"[ERROR] Erro inesperado no mapeamento: {e}")
            return self.get_default_coordinates(x, y)
    
    def get_default_coordinates(self, x, y):
        """Get default coordinate mapping without calibration"""
        return (
            int((x / DEFAULT_AIRSCAN_WIDTH) * screen_width),
            int((y / DEFAULT_AIRSCAN_HEIGHT) * screen_height)
        )
    
    def update_mouse_position(self):
        """Update mouse position based on AirScan coordinates with throttling and smoothing"""
        if self.norm_x is not None and self.norm_y is not None:
            try:
                current_time = time.time()
                
                # Atualiza timestamp de última recepção de dados
                self.last_data_time = current_time
                
                # Reinicia watchdog timer
                self.reset_watchdog_timer()
                
                # Throttling: limita taxa de atualização
                if current_time - self.last_update_time < self.update_interval:
                    return  # Ignora esta atualização para manter taxa configurada
                
                self.last_update_time = current_time
                
                # Obter coordenadas calibradas
                pixel_x, pixel_y = self.get_calibrated_coordinates(self.norm_x, self.norm_y)
                
                # Adicionar ao histórico para suavização
                self.x_history.append(pixel_x)
                self.y_history.append(pixel_y)
                
                # Calcular média móvel
                smoothed_x = sum(self.x_history) / len(self.x_history)
                smoothed_y = sum(self.y_history) / len(self.y_history)
                
                # Arredondar para inteiro
                final_x = int(smoothed_x)
                final_y = int(smoothed_y)
                
                # Verificar estabilização da posição
                self.check_position_stability(final_x, final_y, current_time)
                
                # Lógica de posicionamento e clique
                if not self.mouse_pressed:
                    # Move para posição (sempre atualiza posição do cursor)
                    pyautogui.moveTo(final_x, final_y, duration=0.01)
                    
                    # Só clica se posição estiver estável
                    if self.is_position_stable:
                        time.sleep(POSITION_STABILIZE_DELAY)  # Delay configurável para estabilizar posição
                        pyautogui.mouseDown()
                        self.mouse_pressed = True
                        self.initial_position_set = True
                        print(f"[TOUCH] Clique estável: ({final_x}, {final_y}) - raio: {STABILITY_RADIUS}px, tempo: {STABILITY_TIME}s")
                    else:
                        # Mostra progresso da estabilização
                        if self.stable_position:
                            distance = ((final_x - self.stable_position[0])**2 + (final_y - self.stable_position[1])**2)**0.5
                            remaining_time = STABILITY_TIME - (current_time - self.stability_start_time)
                            print(f"[STABLE] Estabilizando... distância: {distance:.1f}px/{STABILITY_RADIUS}px, restam: {remaining_time:.2f}s")
                        else:
                            print(f"[STABLE] Aguardando estabilização... ({final_x}, {final_y})")
                            
                elif self.mouse_pressed:
                    # MOVIMENTO CONTÍNUO: Drag para desenhar
                    pyautogui.dragTo(final_x, final_y, duration=0.01)
                    print(f"[TOUCH] DragTo({final_x}, {final_y})")
                else:
                    # Mouse não pressionado - movimento normal (hover)
                    pyautogui.moveTo(final_x, final_y)
                
                # Log coordinates with throttling (500ms)
                if current_time - self.last_log_time >= self.log_interval:
                    status = " [PRESSED]" if self.mouse_pressed else ""
                    print(f"[AIRSCAN] X:{self.norm_x:.2f} Y:{self.norm_y:.2f} -> Tela({final_x}, {final_y}){status}")
                    self.last_log_time = current_time
                    
            except Exception as e:
                print(f"[ERROR] Failed to update mouse position: {e}")
    
    def reset_watchdog_timer(self):
        """Reinicia o timer de watchdog - cancela o antigo e cria novo"""
        # Cancela timer existente
        if self.watchdog_timer and self.watchdog_timer.is_alive():
            self.watchdog_timer.cancel()
        
        # Cria novo timer que será chamado se não receber dados por 0.3s
        self.watchdog_timer = threading.Timer(self.data_timeout, self.on_data_timeout)
        self.watchdog_timer.daemon = True
        self.watchdog_timer.start()
    
    def on_data_timeout(self):
        """Chamado quando não recebe dados do AirScan por 0.3s"""
        if self.mouse_pressed:
            pyautogui.mouseUp()
            self.mouse_pressed = False
            self.initial_position_set = False  # Reset flag para próximo toque
            # Reset sistema de estabilização
            self.stable_position = None
            self.is_position_stable = False
            print(f"[TOUCH] MouseUp - sem dados por {self.data_timeout}s")
    
    def check_position_stability(self, x, y, current_time):
        """Verifica se a posição está estável dentro do raio de tolerância"""
        if self.stable_position is None:
            # Primeira posição - inicia estabilização
            self.stable_position = (x, y)
            self.stability_start_time = current_time
            self.is_position_stable = False
            return
        
        # Calcula distância da posição estável atual
        distance = ((x - self.stable_position[0])**2 + (y - self.stable_position[1])**2)**0.5
        
        if distance <= STABILITY_RADIUS:
            # Dentro do raio - verifica se passou tempo suficiente
            time_in_stability = current_time - self.stability_start_time
            if time_in_stability >= STABILITY_TIME:
                self.is_position_stable = True
            else:
                self.is_position_stable = False
        else:
            # Fora do raio - reinicia estabilização
            self.stable_position = (x, y)
            self.stability_start_time = current_time
            self.is_position_stable = False
    
    def handle_mouse_x(self, unused_addr, x):
        """Handle X coordinate from AirScan"""
        self.norm_x = x
        # Write coordinates to temp file for calibration process
        self.write_coordinates_to_temp()
        self.update_mouse_position()
    
    def handle_mouse_y(self, unused_addr, y):
        """Handle Y coordinate from AirScan"""
        self.norm_y = y
        # Write coordinates to temp file for calibration process
        self.write_coordinates_to_temp()
        self.update_mouse_position()
    
    def write_coordinates_to_temp(self):
        """Write current coordinates to temporary file for calibration"""
        if self.norm_x is not None and self.norm_y is not None:
            try:
                with open("airscan_coords.tmp", "w") as f:
                    json.dump({"x": self.norm_x, "y": self.norm_y}, f)
            except Exception as e:
                print(f"[WARNING] Failed to write coordinates to temp file: {e}")
    
    def handle_mouse_click(self, unused_addr, z):
        """Handle click state from AirScan - não usado mais (detecção por falta de dados X/Y)"""
        # Este método não faz nada - a detecção de mouseUp é feita por watchdog timer
        # quando para de receber dados X/Y
        pass
    
    def start_calibration(self):
        """Launch calibration tool"""
        try:
            # Check if calibration is already running
            if self.calibration_process and self.calibration_process.poll() is None:
                print("[CALIBRAÇÃO] Calibração já está em execução! Ignorando chamada...")
                return
            
            # Stop the main server and ensure port is free
            if self.server:
                print("[CALIBRAÇÃO] Parando servidor principal para calibração...")
                self.server.shutdown()
                self.server = None
            
            # Ensure port is free before starting calibration
            if self.is_port_in_use(AIRSCAN_PORT):
                print(f"[CALIBRAÇÃO] Porta {AIRSCAN_PORT} ainda em uso, aguardando...")
                if not self.wait_for_port_free(AIRSCAN_PORT, timeout=5):
                    print(f"[CALIBRAÇÃO] Forçando liberação da porta {AIRSCAN_PORT}...")
                    self.kill_processes_using_port(AIRSCAN_PORT)
                    time.sleep(1)  # Give time for port to be released
            
            # Save current directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            calibration_script = os.path.join(current_dir, "AirScan_Calibration.py")
            
            # Launch calibration in a new process
            self.calibration_process = subprocess.Popen([sys.executable, calibration_script])
            print("Ferramenta de calibração iniciada!")
            
            # Monitor calibration process
            self.monitor_calibration()
            
        except Exception as e:
            print(f"[ERROR] Failed to start calibration: {e}")
    
    def monitor_calibration(self):
        """Monitor calibration process and reload data when complete"""
        def monitor():
            if self.calibration_process:
                self.calibration_process.wait()
                
                # Check if calibration was cancelled
                cancelled = os.path.exists('calibration_cancelled.flag')
                if cancelled:
                    print("[CALIBRAÇÃO] Calibração cancelada pelo usuário.")
                    try:
                        os.remove('calibration_cancelled.flag')
                    except:
                        pass
                else:
                    print("[CALIBRAÇÃO] Processo de calibração finalizado. Recarregando dados...")
                    self.calibration_data = self.load_calibration()
                    print("[CALIBRAÇÃO] Dados de calibração atualizados!")
                
                self.calibration_complete.set()
                print("[CALIBRAÇÃO] Sistema de controle continua ativo.")
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
    
    def restart_server(self):
        """Restart the main OSC server"""
        try:
            # Setup OSC dispatcher
            dispatcher = Dispatcher()
            dispatcher.map(f"/airscan/blob/{BLOB_ID}/x", self.handle_mouse_x)
            dispatcher.map(f"/airscan/blob/{BLOB_ID}/y", self.handle_mouse_y)
            dispatcher.map(f"/airscan/blob/{BLOB_ID}/z", self.handle_mouse_click)
            
            # Start OSC server
            self.server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", AIRSCAN_PORT), dispatcher)
            print(f"[INFO] Servidor AirScan reiniciado em 0.0.0.0:{AIRSCAN_PORT}")
            
            # Start server in background thread
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
        except Exception as e:
            print(f"[ERROR] Erro ao reiniciar servidor: {e}")
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        try:
            import keyboard
            
            def on_calibration_shortcut():
                print("[CALIBRAÇÃO] Atalho Shift+C detectado!")
                self.start_calibration()
            
            def on_exit_shortcut():
                print("[SAÍDA] Atalho Ctrl+Q detectado!")
                print("[INFO] Encerrando sistema...")
                self.shutdown_event.set()
                self.running = False
            
            # Usar add_hotkey que é mais confiável
            keyboard.add_hotkey('shift+c', on_calibration_shortcut)
            keyboard.add_hotkey('ctrl+q', on_exit_shortcut)
            print("✅ Atalhos configurados:")
            print("   • Shift+C: Iniciar calibração")
            print("   • Ctrl+Q: Encerrar sistema")
            print("   • Ctrl+C: Encerrar sistema (sinal)")
            
        except ImportError:
            print("❌ Módulo keyboard não disponível - atalhos desabilitados")
        except Exception as e:
            print(f"❌ Erro ao configurar atalhos: {e}")
    
    def start(self):
        """Start the AirScan control server"""
        print("=" * 50)
        print("AIRSCAN CONTROL - INICIANDO")
        print("=" * 50)
        
        # Display configuration
        print(f"[CONFIG] Modo: {AIRSCAN_MODE} (Blob {BLOB_ID})")
        print(f"[CONFIG] Taxa de atualização: {MOUSE_UPDATE_RATE}Hz (~{1000/MOUSE_UPDATE_RATE:.1f}ms)")
        print(f"[CONFIG] Suavização: {SMOOTHING_SAMPLES} amostras (média móvel)")
        print(f"[CONFIG] Sistema Touch Screen: Watchdog {MOUSE_RELEASE_DELAY}s (sem dados = mouseUp)")
        print(f"[CONFIG] Resolução AirScan: {DEFAULT_AIRSCAN_WIDTH}x{DEFAULT_AIRSCAN_HEIGHT}")
        print(f"[CONFIG] Resolução Tela: {screen_width}x{screen_height}")
        
        # Setup OSC dispatcher
        dispatcher = Dispatcher()
        dispatcher.map(f"/airscan/blob/{BLOB_ID}/x", self.handle_mouse_x)
        dispatcher.map(f"/airscan/blob/{BLOB_ID}/y", self.handle_mouse_y)
        dispatcher.map(f"/airscan/blob/{BLOB_ID}/z", self.handle_mouse_click)
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Display calibration status
        if self.calibration_data.get("points"):
            print(f"[INFO] Calibração ativa: {len(self.calibration_data['points'])} pontos")
        else:
            print("[WARNING] Nenhuma calibração encontrada. Pressione Shift+C para calibrar.")
        
        # Check if port is available before starting server
        if self.is_port_in_use(AIRSCAN_PORT):
            print(f"[WARNING] Porta {AIRSCAN_PORT} está em uso. Tentando liberar...")
            if not self.wait_for_port_free(AIRSCAN_PORT, timeout=5):
                print(f"[WARNING] Forçando liberação da porta {AIRSCAN_PORT}...")
                self.kill_processes_using_port(AIRSCAN_PORT)
                time.sleep(2)  # Give time for port to be released
        
        # Start OSC server
        try:
            self.server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", AIRSCAN_PORT), dispatcher)
            print(f"\n[INFO] Servidor AirScan iniciado em 0.0.0.0:{AIRSCAN_PORT}")
            print("[INFO] Atalhos disponíveis:")
            print("[INFO]   • Ctrl+C: Encerrar sistema")
            print("[INFO]   • Ctrl+Q: Encerrar sistema")
            print("[INFO]   • Shift+C: Iniciar calibração")
            print("[INFO] A calibração reiniciará automaticamente o controle")
            print("-" * 50)
            
            # Start server in a separate thread
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            # Main loop - wait for shutdown event
            while self.running and not self.shutdown_event.is_set():
                try:
                    # Check every second if we should shutdown
                    if self.shutdown_event.wait(1.0):
                        break
                except KeyboardInterrupt:
                    print("\n[INFO] Ctrl+C detectado. Encerrando...")
                    break
            
            print("\n[INFO] Encerrando servidor...")
            
        except OSError as e:
            if e.errno == 10048:  # Port already in use
                print(f"\n[ERROR] Porta {AIRSCAN_PORT} ainda está em uso após tentativas de liberação.")
                print(f"[INFO] Execute manualmente: netstat -ano | findstr :{AIRSCAN_PORT}")
                print(f"[INFO] Ou reinicie o sistema para liberar a porta.")
            else:
                print(f"\n[ERROR] Erro de rede: {e}")
        except Exception as e:
            print(f"\n[ERROR] Erro inesperado ao iniciar servidor: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        print("[INFO] Limpando recursos...")
        self.running = False
        self.shutdown_event.set()
        
        # Limpar atalhos de teclado
        try:
            import keyboard
            keyboard.clear_all_hotkeys()
            print("[INFO] Atalhos de teclado removidos")
        except:
            pass
        
        # Cancelar watchdog timer se existir
        if self.watchdog_timer and self.watchdog_timer.is_alive():
            self.watchdog_timer.cancel()
            print("[INFO] Watchdog timer cancelado")
        
        # Finalizar processo de calibração se existir
        if self.calibration_process and self.calibration_process.poll() is None:
            print("[INFO] Finalizando processo de calibração...")
            try:
                self.calibration_process.terminate()
                self.calibration_process.wait(timeout=3)
                print("[INFO] Processo de calibração finalizado")
            except subprocess.TimeoutExpired:
                print("[WARNING] Forçando encerramento do processo de calibração...")
                self.calibration_process.kill()
            except Exception as e:
                print(f"[WARNING] Erro ao finalizar processo de calibração: {e}")
        
        # Encerrar servidor OSC
        if self.server:
            try:
                print("[INFO] Encerrando servidor OSC...")
                self.server.shutdown()
                self.server.server_close()
                print("[INFO] Servidor OSC encerrado")
            except Exception as e:
                print(f"[WARNING] Erro ao encerrar servidor: {e}")
        
        print("[INFO] Limpeza concluída. Sistema encerrado.")
        sys.exit(0)

if __name__ == "__main__":
    control = AirScanControl()
    control.start()